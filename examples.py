"""Example usage of the data pipeline."""

import logging
from src.data_pipeline import DataPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_export_query_to_json():
    """Example: Export a Snowflake query to JSON."""
    pipeline = DataPipeline()
    
    # Example query - replace with your actual query
    query = """
        SELECT * 
        FROM trades 
        WHERE trade_date >= CURRENT_DATE - 7
        LIMIT 1000
    """
    
    s3_uri = pipeline.export_query_to_json(
        query=query,
        output_key="exports/recent_trades.json",
        include_timestamp=True,
    )
    
    logger.info(f"Data exported to: {s3_uri}")


def example_export_query_to_csv():
    """Example: Export a Snowflake query to CSV."""
    pipeline = DataPipeline()
    
    # Example query - replace with your actual query
    query = """
        SELECT symbol, price, volume, trade_date
        FROM market_data
        WHERE trade_date = CURRENT_DATE
    """
    
    s3_uri = pipeline.export_query_to_csv(
        query=query,
        output_key="exports/daily_market_data.csv",
        include_timestamp=True,
    )
    
    logger.info(f"Data exported to: {s3_uri}")


def example_export_table_to_json():
    """Example: Export an entire Snowflake table to JSON."""
    pipeline = DataPipeline()
    
    s3_uri = pipeline.export_table_to_json(
        table_name="market_symbols",
        output_key="exports/symbols.json",
        columns=["symbol", "name", "sector", "market_cap"],
        limit=500,
        include_timestamp=True,
    )
    
    logger.info(f"Table exported to: {s3_uri}")


def example_export_table_to_csv_with_filter():
    """Example: Export a filtered Snowflake table to CSV."""
    pipeline = DataPipeline()
    
    s3_uri = pipeline.export_table_to_csv(
        table_name="trades",
        output_key="exports/high_volume_trades.csv",
        where_clause="volume > 1000000",
        limit=1000,
        include_timestamp=True,
    )
    
    logger.info(f"Filtered table exported to: {s3_uri}")


if __name__ == "__main__":
    # Uncomment the example you want to run
    
    # example_export_query_to_json()
    # example_export_query_to_csv()
    # example_export_table_to_json()
    # example_export_table_to_csv_with_filter()
    
    logger.info("Please uncomment one of the example functions to run")
