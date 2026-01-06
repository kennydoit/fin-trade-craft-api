"""Main entry point for the Financial Trade Craft API."""

import logging
import sys

import uvicorn

from src.api import app
from src.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    """Run the API server."""
    settings = get_settings()
    
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Server will run on {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
