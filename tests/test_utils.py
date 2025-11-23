"""
Tests for utility functions.
"""

import pytest
from utils.error_handler import error_handler
from utils.sql_parser import sql_parser
from utils.helpers import (
    truncate_long_text,
    format_execution_time,
    pluralize,
    format_bytes,
    calculate_success_rate
)


class TestErrorHandler:
    """Test error classification and handling."""
    
    def test_classify_column_error(self):
        """Test classification of column not found errors."""
        error_msg = 'column "invalid_col" does not exist'
        error_type = error_handler.classify_error(error_msg)
        assert error_type == "column_name"
    
    def test_classify_table_error(self):
        """Test classification of table not found errors."""
        error_msg = 'relation "invalid_table" does not exist'
        error_type = error_handler.classify_error(error_msg)
        assert error_type == "table_name"
    
    def test_classify_syntax_error(self):
        """Test classification of syntax errors."""
        error_msg = 'syntax error at or near "FROM"'
        error_type = error_handler.classify_error(error_msg)
        assert error_type == "syntax"
    
    def test_classify_permission_error(self):
        """Test classification of permission errors."""
        error_msg = 'permission denied for table users'
        error_type = error_handler.classify_error(error_msg)
        assert error_type == "permission"
    
    def test_should_retry(self):
        """Test retry logic for different error types."""
        # Retryable errors
        assert error_handler.should_retry("column_name", 1, 3) is True
        assert error_handler.should_retry("syntax", 2, 3) is True
        
        # Non-retryable errors
        assert error_handler.should_retry("permission", 1, 3) is False
        assert error_handler.should_retry("timeout", 1, 3) is False
        
        # Max attempts reached
        assert error_handler.should_retry("column_name", 3, 3) is False


class TestSQLParser:
    """Test SQL parsing utilities."""
    
    def test_extract_tables(self):
        """Test table name extraction."""
        sql = "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        tables = sql_parser.extract_tables(sql)
        
        assert "users" in tables
        assert "orders" in tables
    
    def test_get_query_type(self):
        """Test query type detection."""
        assert sql_parser.get_query_type("SELECT * FROM users") == "SELECT"
        assert sql_parser.get_query_type("INSERT INTO users VALUES (1, 'test')") == "INSERT"
        assert sql_parser.get_query_type("UPDATE users SET active = true") == "UPDATE"
        assert sql_parser.get_query_type("DELETE FROM users WHERE id = 1") == "DELETE"
    
    def test_has_where_clause(self):
        """Test WHERE clause detection."""
        assert sql_parser.has_where_clause("SELECT * FROM users WHERE active = true") is True
        assert sql_parser.has_where_clause("SELECT * FROM users") is False
    
    def test_estimate_complexity(self):
        """Test complexity estimation."""
        # Simple query
        simple = "SELECT * FROM users"
        assert sql_parser.estimate_complexity(simple) == 0
        
        # Query with JOIN
        join_query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        assert sql_parser.estimate_complexity(join_query) > 0
        
        # Query with aggregation
        agg_query = "SELECT COUNT(*), SUM(amount) FROM orders GROUP BY user_id"
        assert sql_parser.estimate_complexity(agg_query) > 2
    
    def test_get_limit_clause(self):
        """Test LIMIT clause extraction."""
        sql = "SELECT * FROM users LIMIT 10"
        assert sql_parser.get_limit_clause(sql) == 10
        
        sql_no_limit = "SELECT * FROM users"
        assert sql_parser.get_limit_clause(sql_no_limit) is None
    
    def test_add_limit_clause(self):
        """Test adding LIMIT clause."""
        # Add to query without LIMIT
        sql = "SELECT * FROM users"
        limited = sql_parser.add_limit_clause(sql, 50)
        assert "LIMIT 50" in limited
        
        # Replace existing LIMIT
        sql = "SELECT * FROM users LIMIT 10"
        limited = sql_parser.add_limit_clause(sql, 100)
        assert "LIMIT 100" in limited
        assert "LIMIT 10" not in limited


class TestHelpers:
    """Test helper functions."""
    
    def test_truncate_long_text(self):
        """Test text truncation."""
        short = "short text"
        assert truncate_long_text(short, 20) == short
        
        long = "a" * 100
        truncated = truncate_long_text(long, 20)
        assert len(truncated) <= 20
        assert truncated.endswith("...")
    
    def test_format_execution_time(self):
        """Test time formatting."""
        # Less than 1 second
        assert "ms" in format_execution_time(0.450)
        assert "450" in format_execution_time(0.450)
        
        # Seconds
        assert "s" in format_execution_time(2.5)
        assert "2.50" in format_execution_time(2.5)
        
        # Minutes
        result = format_execution_time(125)
        assert "m" in result
    
    def test_pluralize(self):
        """Test pluralization."""
        assert pluralize(1, "row") == "1 row"
        assert pluralize(2, "row") == "2 rows"
        assert pluralize(0, "row") == "0 rows"
        
        # Custom plural
        assert pluralize(1, "category", "categories") == "1 category"
        assert pluralize(2, "category", "categories") == "2 categories"
    
    def test_format_bytes(self):
        """Test byte formatting."""
        assert "B" in format_bytes(500)
        assert "KB" in format_bytes(2048)
        assert "MB" in format_bytes(5 * 1024 * 1024)
    
    def test_calculate_success_rate(self):
        """Test success rate calculation."""
        assert calculate_success_rate(7, 10) == 70.0
        assert calculate_success_rate(0, 10) == 0.0
        assert calculate_success_rate(10, 10) == 100.0
        assert calculate_success_rate(0, 0) == 0.0  # Edge case


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
