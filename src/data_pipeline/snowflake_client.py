"""Snowflake database client."""

import logging
import re
from typing import List, Optional

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

    def execute_query(self, query: str, sanitize_log: bool = True) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a pandas DataFrame.

        Args:
            query: SQL query to execute
            sanitize_log: Whether to sanitize the query in logs

        Returns:
            DataFrame containing query results
        """
        if not self._connection:
            self.connect()

        try:
            # Sanitize query for logging to avoid exposing sensitive data
            log_query = query[:100] + "..." if len(query) > 100 else query
            if sanitize_log:
                log_query = "<query redacted for security>"
            logger.info(f"Executing query: {log_query}")
            
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
            table_name: Name of the table to query (should be validated/sanitized by caller)
            columns: List of columns to select (default: all columns)
            where_clause: Optional WHERE clause for filtering (should be validated/sanitized by caller)
            limit: Optional limit on number of rows

        Returns:
            DataFrame containing table data
            
        Warning:
            This method does not fully sanitize where_clause for SQL injection.
            Only use where_clause with trusted inputs or implement additional validation.
            For user-provided filters, consider using a parameterized query approach
            or a query builder library instead of this method.
        """
        # Validate table name contains only allowed characters
        if not re.match(r'^[a-zA-Z0-9_\.]+$', table_name):
            raise ValueError(f"Invalid table name: {table_name}. Only alphanumeric, underscore, and dot characters are allowed.")
        
        column_list = ", ".join(columns) if columns else "*"
        
        # Validate column names if provided
        if columns:
            for col in columns:
                if not re.match(r'^[a-zA-Z0-9_]+$', col):
                    raise ValueError(f"Invalid column name: {col}. Only alphanumeric and underscore characters are allowed.")
        
        query = f"SELECT {column_list} FROM {table_name}"
        
        if where_clause:
            # Validate WHERE clause contains only safe characters (basic check)
            # This is NOT foolproof - only use with trusted sources
            if any(char in where_clause for char in [';', '--', '/*', '*/', 'DROP', 'DELETE', 'UPDATE', 'INSERT']):
                raise ValueError("WHERE clause contains potentially dangerous SQL keywords or characters")
            logger.warning("WHERE clause provided. Ensure it is from a trusted source to prevent SQL injection.")
            query += f" WHERE {where_clause}"
        
        if limit:
            # Validate limit is an integer
            if not isinstance(limit, int) or limit < 0:
                raise ValueError(f"Invalid limit: {limit}. Must be a non-negative integer.")
            query += f" LIMIT {limit}"
        
        return self.execute_query(query, sanitize_log=False)

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
