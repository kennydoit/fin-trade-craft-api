"""S3 file writer for exporting data to flat files."""

import json
import logging
from datetime import datetime
from io import BytesIO, StringIO
from typing import Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from src.config import get_settings

logger = logging.getLogger(__name__)


class S3Writer:
    """Client for writing data to S3 as flat files."""

    def __init__(self):
        """Initialize S3 writer with settings."""
        self.settings = get_settings()
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key,
            region_name=self.settings.aws_region,
        )
        self.bucket_name = self.settings.s3_bucket_name

    def write_csv(
        self,
        data: pd.DataFrame,
        file_key: str,
        include_index: bool = False,
    ) -> str:
        """
        Write DataFrame to S3 as CSV file.

        Args:
            data: DataFrame to write
            file_key: S3 object key (path/filename)
            include_index: Whether to include DataFrame index

        Returns:
            S3 URI of the written file
            
        Note:
            For large datasets, this method loads the entire CSV into memory.
            Consider implementing chunked uploads for datasets larger than 1GB.
        """
        try:
            csv_buffer = StringIO()
            data.to_csv(csv_buffer, index=include_index)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=csv_buffer.getvalue(),
                ContentType="text/csv",
            )
            
            s3_uri = f"s3://{self.bucket_name}/{file_key}"
            logger.info(f"Successfully wrote CSV to {s3_uri}")
            return s3_uri
        except ClientError as e:
            logger.error(f"Failed to write CSV to S3: {e}")
            raise

    def write_json(
        self,
        data: pd.DataFrame,
        file_key: str,
        orient: str = "records",
        indent: Optional[int] = 2,
    ) -> str:
        """
        Write DataFrame to S3 as JSON file.

        Args:
            data: DataFrame to write
            file_key: S3 object key (path/filename)
            orient: JSON orientation ('records', 'index', 'columns', etc.)
            indent: Number of spaces for indentation (None for compact)

        Returns:
            S3 URI of the written file
        """
        try:
            json_str = data.to_json(orient=orient, indent=indent)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=json_str,
                ContentType="application/json",
            )
            
            s3_uri = f"s3://{self.bucket_name}/{file_key}"
            logger.info(f"Successfully wrote JSON to {s3_uri}")
            return s3_uri
        except ClientError as e:
            logger.error(f"Failed to write JSON to S3: {e}")
            raise

    def list_files(self, prefix: str = "") -> list:
        """
        List files in S3 bucket with optional prefix.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )
            
            if "Contents" not in response:
                return []
            
            files = [obj["Key"] for obj in response["Contents"]]
            logger.info(f"Found {len(files)} files with prefix '{prefix}'")
            return files
        except ClientError as e:
            logger.error(f"Failed to list files from S3: {e}")
            raise

    def get_file_url(self, file_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for downloading a file.

        Args:
            file_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_key},
                ExpiresIn=expiration,
            )
            logger.info(f"Generated presigned URL for {file_key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    def read_file(self, file_key: str) -> bytes:
        """
        Read file content from S3.

        Args:
            file_key: S3 object key

        Returns:
            File content as bytes
            
        Note:
            This method loads the entire file into memory. For large files (>100MB),
            consider using streaming reads or downloading to disk instead.
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=file_key
            )
            content = response["Body"].read()
            logger.info(f"Successfully read file {file_key}")
            return content
        except ClientError as e:
            logger.error(f"Failed to read file from S3: {e}")
            raise
