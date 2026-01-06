"""Data pipeline orchestration."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from src.data_pipeline.s3_writer import S3Writer
from src.data_pipeline.snowflake_client import SnowflakeClient

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates data extraction from Snowflake and export to S3."""

    def __init__(self):
        """Initialize data pipeline with clients."""
        self.snowflake_client = SnowflakeClient()
        self.s3_writer = S3Writer()

    def export_query_to_csv(
        self,
        query: str,
        output_key: str,
        include_timestamp: bool = True,
    ) -> str:
        """
        Execute a Snowflake query and export results to S3 as CSV.

        Args:
            query: SQL query to execute
            output_key: S3 key for the output file
            include_timestamp: Whether to append timestamp to filename

        Returns:
            S3 URI of the exported file
        """
        try:
            # Extract data from Snowflake
            logger.info("Extracting data from Snowflake")
            with self.snowflake_client as client:
                df = client.execute_query(query)

            # Add timestamp to filename if requested
            if include_timestamp:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                if output_key.endswith(".csv"):
                    output_key = output_key[:-4] + f"_{timestamp}.csv"
                else:
                    output_key = f"{output_key}_{timestamp}.csv"

            # Write to S3
            logger.info(f"Writing data to S3: {output_key}")
            s3_uri = self.s3_writer.write_csv(df, output_key)
            
            logger.info(f"Successfully exported {len(df)} rows to {s3_uri}")
            return s3_uri
        except Exception as e:
            logger.error(f"Failed to export query to CSV: {e}")
            raise

    def export_query_to_json(
        self,
        query: str,
        output_key: str,
        include_timestamp: bool = True,
        orient: str = "records",
    ) -> str:
        """
        Execute a Snowflake query and export results to S3 as JSON.

        Args:
            query: SQL query to execute
            output_key: S3 key for the output file
            include_timestamp: Whether to append timestamp to filename
            orient: JSON orientation ('records', 'index', 'columns', etc.)

        Returns:
            S3 URI of the exported file
        """
        try:
            # Extract data from Snowflake
            logger.info("Extracting data from Snowflake")
            with self.snowflake_client as client:
                df = client.execute_query(query)

            # Add timestamp to filename if requested
            if include_timestamp:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                if output_key.endswith(".json"):
                    output_key = output_key[:-5] + f"_{timestamp}.json"
                else:
                    output_key = f"{output_key}_{timestamp}.json"

            # Write to S3
            logger.info(f"Writing data to S3: {output_key}")
            s3_uri = self.s3_writer.write_json(df, output_key, orient=orient)
            
            logger.info(f"Successfully exported {len(df)} rows to {s3_uri}")
            return s3_uri
        except Exception as e:
            logger.error(f"Failed to export query to JSON: {e}")
            raise

    def export_table_to_csv(
        self,
        table_name: str,
        output_key: str,
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        limit: Optional[int] = None,
        include_timestamp: bool = True,
    ) -> str:
        """
        Export a Snowflake table to S3 as CSV.

        Args:
            table_name: Name of the table to export
            output_key: S3 key for the output file
            columns: Optional list of columns to include
            where_clause: Optional WHERE clause for filtering
            limit: Optional limit on number of rows
            include_timestamp: Whether to append timestamp to filename

        Returns:
            S3 URI of the exported file
        """
        try:
            # Extract data from Snowflake
            logger.info(f"Extracting table {table_name} from Snowflake")
            with self.snowflake_client as client:
                df = client.get_table_data(table_name, columns, where_clause, limit)

            # Add timestamp to filename if requested
            if include_timestamp:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                if output_key.endswith(".csv"):
                    output_key = output_key[:-4] + f"_{timestamp}.csv"
                else:
                    output_key = f"{output_key}_{timestamp}.csv"

            # Write to S3
            logger.info(f"Writing data to S3: {output_key}")
            s3_uri = self.s3_writer.write_csv(df, output_key)
            
            logger.info(f"Successfully exported {len(df)} rows to {s3_uri}")
            return s3_uri
        except Exception as e:
            logger.error(f"Failed to export table to CSV: {e}")
            raise

    def export_table_to_json(
        self,
        table_name: str,
        output_key: str,
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        limit: Optional[int] = None,
        include_timestamp: bool = True,
        orient: str = "records",
    ) -> str:
        """
        Export a Snowflake table to S3 as JSON.

        Args:
            table_name: Name of the table to export
            output_key: S3 key for the output file
            columns: Optional list of columns to include
            where_clause: Optional WHERE clause for filtering
            limit: Optional limit on number of rows
            include_timestamp: Whether to append timestamp to filename
            orient: JSON orientation ('records', 'index', 'columns', etc.)

        Returns:
            S3 URI of the exported file
        """
        try:
            # Extract data from Snowflake
            logger.info(f"Extracting table {table_name} from Snowflake")
            with self.snowflake_client as client:
                df = client.get_table_data(table_name, columns, where_clause, limit)

            # Add timestamp to filename if requested
            if include_timestamp:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                if output_key.endswith(".json"):
                    output_key = output_key[:-5] + f"_{timestamp}.json"
                else:
                    output_key = f"{output_key}_{timestamp}.json"

            # Write to S3
            logger.info(f"Writing data to S3: {output_key}")
            s3_uri = self.s3_writer.write_json(df, output_key, orient=orient)
            
            logger.info(f"Successfully exported {len(df)} rows to {s3_uri}")
            return s3_uri
        except Exception as e:
            logger.error(f"Failed to export table to JSON: {e}")
            raise
