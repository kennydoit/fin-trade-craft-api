"""FastAPI application for serving flat files from S3."""

import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from src.config import get_settings
from src.data_pipeline import DataPipeline, S3Writer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="API service for distributing financial market data files from S3",
)

# Initialize clients
s3_writer = S3Writer()
data_pipeline = DataPipeline()


class FileInfo(BaseModel):
    """Model for file information."""

    key: str
    size: Optional[int] = None
    last_modified: Optional[str] = None


class ExportRequest(BaseModel):
    """Model for data export requests."""

    query: str
    output_key: str
    format: str = "json"  # json or csv
    include_timestamp: bool = True
    orient: Optional[str] = "records"  # For JSON exports


class TableExportRequest(BaseModel):
    """Model for table export requests."""

    table_name: str
    output_key: str
    format: str = "json"  # json or csv
    columns: Optional[List[str]] = None
    where_clause: Optional[str] = None
    limit: Optional[int] = None
    include_timestamp: bool = True
    orient: Optional[str] = "records"  # For JSON exports


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": "API for distributing financial market data files",
        "endpoints": {
            "files": "/files - List available files",
            "download": "/files/{file_key:path}/download - Get download URL",
            "export_query": "/export/query - Export Snowflake query results",
            "export_table": "/export/table - Export Snowflake table",
            "health": "/health - Health check",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.api_title}


@app.get("/files", response_model=List[str])
async def list_files(prefix: str = Query("", description="Optional prefix to filter files")):
    """
    List available files in S3.

    Args:
        prefix: Optional prefix to filter files by path

    Returns:
        List of file keys
    """
    try:
        files = s3_writer.list_files(prefix)
        return files
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@app.get("/files/{file_key:path}/download")
async def get_download_url(
    file_key: str,
    expiration: int = Query(3600, description="URL expiration in seconds"),
):
    """
    Get a presigned download URL for a file.

    Args:
        file_key: S3 object key (file path)
        expiration: URL expiration time in seconds (default: 1 hour)

    Returns:
        Presigned download URL
    """
    try:
        url = s3_writer.get_file_url(file_key, expiration)
        return {"file_key": file_key, "download_url": url, "expires_in": expiration}
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate download URL: {str(e)}"
        )


@app.get("/files/{file_key:path}/content")
async def get_file_content(file_key: str):
    """
    Get the content of a file directly.

    Args:
        file_key: S3 object key (file path)

    Returns:
        File content
    """
    try:
        content = s3_writer.read_file(file_key)
        
        # Determine content type based on file extension
        if file_key.endswith(".json"):
            return JSONResponse(content=content.decode("utf-8"))
        elif file_key.endswith(".csv"):
            return JSONResponse(
                content={"data": content.decode("utf-8")},
                media_type="text/csv",
            )
        else:
            return {"content": content.decode("utf-8")}
    except Exception as e:
        logger.error(f"Failed to retrieve file content: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve file content: {str(e)}"
        )


@app.post("/export/query")
async def export_query(request: ExportRequest):
    """
    Export Snowflake query results to S3.

    Args:
        request: Export request with query and output configuration

    Returns:
        S3 URI of the exported file
    """
    try:
        if request.format.lower() == "csv":
            s3_uri = data_pipeline.export_query_to_csv(
                query=request.query,
                output_key=request.output_key,
                include_timestamp=request.include_timestamp,
            )
        elif request.format.lower() == "json":
            s3_uri = data_pipeline.export_query_to_json(
                query=request.query,
                output_key=request.output_key,
                include_timestamp=request.include_timestamp,
                orient=request.orient or "records",
            )
        else:
            raise HTTPException(
                status_code=400, detail="Format must be 'json' or 'csv'"
            )

        return {"s3_uri": s3_uri, "status": "success"}
    except Exception as e:
        logger.error(f"Failed to export query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export query: {str(e)}")


@app.post("/export/table")
async def export_table(request: TableExportRequest):
    """
    Export Snowflake table to S3.

    Args:
        request: Table export request with configuration

    Returns:
        S3 URI of the exported file
    """
    try:
        if request.format.lower() == "csv":
            s3_uri = data_pipeline.export_table_to_csv(
                table_name=request.table_name,
                output_key=request.output_key,
                columns=request.columns,
                where_clause=request.where_clause,
                limit=request.limit,
                include_timestamp=request.include_timestamp,
            )
        elif request.format.lower() == "json":
            s3_uri = data_pipeline.export_table_to_json(
                table_name=request.table_name,
                output_key=request.output_key,
                columns=request.columns,
                where_clause=request.where_clause,
                limit=request.limit,
                include_timestamp=request.include_timestamp,
                orient=request.orient or "records",
            )
        else:
            raise HTTPException(
                status_code=400, detail="Format must be 'json' or 'csv'"
            )

        return {"s3_uri": s3_uri, "status": "success"}
    except Exception as e:
        logger.error(f"Failed to export table: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export table: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
    )
