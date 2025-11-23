"""
Safe SQL query execution with error handling and result formatting.
"""

import logging
import time
from typing import Dict, List, Optional, Any
import psycopg2.extras
from psycopg2 import Error as PsycopgError

from database.connection import db

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes SQL queries safely with comprehensive error handling."""
    
    def __init__(self):
        """Initialize query executor."""
        self.max_result_rows = 10000
    
    def execute_readonly_query(self, sql: str) -> Dict[str, Any]:
        """
        Execute a SELECT query with read-only permissions.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Dictionary with:
                - success (bool): Whether execution succeeded
                - data (List[Dict]): Query results as list of dictionaries
                - error (str): Error message if failed
                - execution_time (float): Execution time in seconds
                - row_count (int): Number of rows returned
                - truncated (bool): Whether results were truncated
        """
        start_time = time.time()
        
        try:
            with db.get_readonly_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Execute query
                cursor.execute(sql)
                
                # Fetch results with row limit
                rows = cursor.fetchmany(self.max_result_rows + 1)
                
                # Check if results were truncated
                truncated = len(rows) > self.max_result_rows
                if truncated:
                    rows = rows[:self.max_result_rows]
                
                # Convert to list of dicts
                data = [dict(row) for row in rows]
                
                cursor.close()
                execution_time = time.time() - start_time
                
                logger.info(f"Query executed successfully: {len(data)} rows in {execution_time:.3f}s")
                
                return {
                    "success": True,
                    "data": data,
                    "error": None,
                    "execution_time": execution_time,
                    "row_count": len(data),
                    "truncated": truncated
                }
                
        except PsycopgError as e:
            execution_time = time.time() - start_time
            error_msg = str(e).strip()
            logger.error(f"Query execution failed: {error_msg}")
            
            return {
                "success": False,
                "data": [],
                "error": error_msg,
                "execution_time": execution_time,
                "row_count": 0,
                "truncated": False
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "data": [],
                "error": error_msg,
                "execution_time": execution_time,
                "row_count": 0,
                "truncated": False
            }
    
    def execute_dba_query(self, sql: str, approved: bool = False) -> Dict[str, Any]:
        """
        Execute a query with DBA permissions (INSERT, UPDATE, DELETE).
        
        Args:
            sql: SQL query to execute
            approved: Whether the query has been approved by a human
            
        Returns:
            Dictionary with execution results (same format as execute_readonly_query)
        """
        if not approved:
            return {
                "success": False,
                "data": [],
                "error": "Query must be approved before execution",
                "execution_time": 0.0,
                "row_count": 0,
                "truncated": False
            }
        
        start_time = time.time()
        
        try:
            with db.get_dba_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Execute query
                cursor.execute(sql)
                
                # Get affected rows count
                row_count = cursor.rowcount
                
                # For SELECT queries in DBA mode, fetch results
                if sql.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchmany(self.max_result_rows + 1)
                    truncated = len(rows) > self.max_result_rows
                    if truncated:
                        rows = rows[:self.max_result_rows]
                    data = [dict(row) for row in rows]
                else:
                    data = []
                    truncated = False
                
                cursor.close()
                execution_time = time.time() - start_time
                
                logger.info(f"DBA query executed: {row_count} rows affected in {execution_time:.3f}s")
                
                return {
                    "success": True,
                    "data": data,
                    "error": None,
                    "execution_time": execution_time,
                    "row_count": row_count,
                    "truncated": truncated
                }
                
        except PsycopgError as e:
            execution_time = time.time() - start_time
            error_msg = str(e).strip()
            logger.error(f"DBA query execution failed: {error_msg}")
            
            return {
                "success": False,
                "data": [],
                "error": error_msg,
                "execution_time": execution_time,
                "row_count": 0,
                "truncated": False
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "data": [],
                "error": error_msg,
                "execution_time": execution_time,
                "row_count": 0,
                "truncated": False
            }
    
    def explain_query(self, sql: str) -> Dict[str, Any]:
        """
        Get PostgreSQL EXPLAIN output for query cost estimation.
        
        Args:
            sql: SQL query to analyze
            
        Returns:
            Dictionary with:
                - success (bool): Whether EXPLAIN succeeded
                - plan (List[str]): Query execution plan
                - error (str): Error message if failed
        """
        try:
            with db.get_readonly_connection() as conn:
                cursor = conn.cursor()
                
                # Get EXPLAIN output
                cursor.execute(f"EXPLAIN {sql}")
                plan = cursor.fetchall()
                
                cursor.close()
                
                # Format plan as list of strings
                plan_lines = [row[0] for row in plan]
                
                return {
                    "success": True,
                    "plan": plan_lines,
                    "error": None
                }
                
        except PsycopgError as e:
            error_msg = str(e).strip()
            logger.error(f"EXPLAIN failed: {error_msg}")
            
            return {
                "success": False,
                "plan": [],
                "error": error_msg
            }
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "plan": [],
                "error": error_msg
            }
    
    def estimate_affected_rows(self, sql: str) -> int:
        """
        Estimate number of rows that would be affected by UPDATE/DELETE query.
        
        Args:
            sql: UPDATE or DELETE query
            
        Returns:
            Estimated row count (0 if estimation fails)
        """
        try:
            # Convert UPDATE/DELETE to SELECT COUNT(*)
            sql_upper = sql.strip().upper()
            
            if sql_upper.startswith('UPDATE'):
                # Extract table and WHERE clause
                parts = sql.split('WHERE', 1)
                table_part = parts[0].replace('UPDATE', 'SELECT COUNT(*) FROM', 1)
                table_part = table_part.split('SET')[0].strip()
                
                if len(parts) > 1:
                    count_query = f"{table_part} WHERE {parts[1]}"
                else:
                    count_query = table_part
            
            elif sql_upper.startswith('DELETE'):
                # Replace DELETE FROM with SELECT COUNT(*) FROM
                count_query = sql.replace('DELETE FROM', 'SELECT COUNT(*) FROM', 1)
            
            else:
                return 0
            
            # Execute count query
            with db.get_readonly_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(count_query)
                count = cursor.fetchone()[0]
                cursor.close()
                
                return count
                
        except Exception as e:
            logger.warning(f"Failed to estimate affected rows: {e}")
            return 0


# Global query executor instance
query_executor = QueryExecutor()
