"""Snowflake database client."""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import snowflake.connector
from snowflake.connector import SnowflakeConnection

from src.config import get_settings

logger = logging.getLogger(__name__)


class SnowflakeClient:
    """Client for connecting to and querying Snowflake."""

    def __init__(self):
        """Initialize Snowflake client with settings."""
        self.settings = get_settings()
        self._connection: Optional[SnowflakeConnection] = None

    def connect(self) -> None:
        """Establish connection to Snowflake."""
        try:
            connection_params = {
                "account": self.settings.snowflake_account,
                "user": self.settings.snowflake_user,
                "password": self.settings.snowflake_password,
                "warehouse": self.settings.snowflake_warehouse,
                "database": self.settings.snowflake_database,
                "schema": self.settings.snowflake_schema,
            }
            
            if self.settings.snowflake_role:
                connection_params["role"] = self.settings.snowflake_role

            self._connection = snowflake.connector.connect(**connection_params)
            logger.info("Successfully connected to Snowflake")
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise

    def disconnect(self) -> None:
        """Close connection to Snowflake."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnected from Snowflake")

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a pandas DataFrame.

        Args:
            query: SQL query to execute

        Returns:
            DataFrame containing query results
        """
        if not self._connection:
            self.connect()

        try:
            logger.info(f"Executing query: {query[:100]}...")
            cursor = self._connection.cursor()
            cursor.execute(query)
            
            # Fetch all results
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            cursor.close()
            
            df = pd.DataFrame(data, columns=columns)
            logger.info(f"Query returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            raise

    def get_table_data(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Retrieve data from a specific table.

        Args:
            table_name: Name of the table to query
            columns: List of columns to select (default: all columns)
            where_clause: Optional WHERE clause for filtering
            limit: Optional limit on number of rows

        Returns:
            DataFrame containing table data
        """
        column_list = ", ".join(columns) if columns else "*"
        query = f"SELECT {column_list} FROM {table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query)

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
