"""
PostgreSQL database connection management for Neon Serverless.
"""

import psycopg2
from psycopg2 import pool, OperationalError, DatabaseError
from typing import Optional
import logging
from contextlib import contextmanager

from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages PostgreSQL connections with pooling and automatic retry."""
    
    def __init__(self):
        """Initialize connection pools for read-only and DBA modes."""
        self._readonly_pool: Optional[pool.SimpleConnectionPool] = None
        self._dba_pool: Optional[pool.SimpleConnectionPool] = None
        
    def get_readonly_pool(self) -> pool.SimpleConnectionPool:
        """
        Get or create read-only connection pool.
        
        Returns:
            SimpleConnectionPool: Read-only connection pool
            
        Raises:
            OperationalError: If connection fails
        """
        if self._readonly_pool is None:
            try:
                self._readonly_pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=settings.database.readonly_connection_string
                )
                logger.info("Read-only connection pool created successfully")
            except OperationalError as e:
                logger.error(f"Failed to create read-only connection pool: {e}")
                raise
        
        return self._readonly_pool
    
    def get_dba_pool(self) -> pool.SimpleConnectionPool:
        """
        Get or create DBA connection pool.
        
        Returns:
            SimpleConnectionPool: DBA connection pool
            
        Raises:
            OperationalError: If connection fails
        """
        if self._dba_pool is None:
            try:
                self._dba_pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=5,
                    dsn=settings.database.dba_connection_string
                )
                logger.info("DBA connection pool created successfully")
            except OperationalError as e:
                logger.error(f"Failed to create DBA connection pool: {e}")
                raise
        
        return self._dba_pool
    
    @contextmanager
    def get_readonly_connection(self):
        """
        Context manager for read-only database connections.
        
        Yields:
            psycopg2.connection: Database connection
            
        Example:
            with db.get_readonly_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        pool = self.get_readonly_pool()
        conn = pool.getconn()
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Read-only connection error: {e}")
            raise
        finally:
            pool.putconn(conn)
    
    @contextmanager
    def get_dba_connection(self):
        """
        Context manager for DBA database connections.
        
        Yields:
            psycopg2.connection: Database connection
            
        Example:
            with db.get_dba_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET status = 'active'")
        """
        pool = self.get_dba_pool()
        conn = pool.getconn()
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"DBA connection error: {e}")
            raise
        finally:
            pool.putconn(conn)
    
    def test_connection(self, mode: str = "readonly") -> tuple[bool, str]:
        """
        Test database connectivity.
        
        Args:
            mode: Connection mode ("readonly" or "dba")
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if mode == "readonly":
                with self.get_readonly_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1;")
                    cursor.close()
            else:
                with self.get_dba_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1;")
                    cursor.close()
            
            return True, f"{mode.capitalize()} connection successful"
            
        except OperationalError as e:
            error_msg = f"{mode.capitalize()} connection failed: Authentication or network error - {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except DatabaseError as e:
            error_msg = f"{mode.capitalize()} connection failed: Database error - {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"{mode.capitalize()} connection failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def close_all_connections(self):
        """Close all connection pools gracefully."""
        if self._readonly_pool:
            self._readonly_pool.closeall()
            logger.info("Read-only connection pool closed")
            self._readonly_pool = None
        
        if self._dba_pool:
            self._dba_pool.closeall()
            logger.info("DBA connection pool closed")
            self._dba_pool = None


# Global database connection instance
db = DatabaseConnection()
