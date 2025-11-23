"""
Tests for SQL validation and security features.
"""

import pytest
from security.validator import query_validator


class TestQueryValidator:
    """Test query validation functionality."""
    
    def test_select_only_readonly_mode(self):
        """Test that only SELECT queries pass in readonly mode."""
        
        # Valid SELECT query
        sql = "SELECT * FROM users WHERE active = true"
        is_safe, issues = query_validator.validate_query(sql, mode="readonly")
        assert is_safe is True
        assert len(issues) == 0
        
        # Invalid UPDATE query in readonly mode
        sql = "UPDATE users SET active = false WHERE id = 1"
        is_safe, issues = query_validator.validate_query(sql, mode="readonly")
        assert is_safe is False
        assert any("read-only" in issue.lower() for issue in issues)
    
    def test_destructive_operations(self):
        """Test detection of destructive operations."""
        
        destructive_queries = [
            "DROP TABLE users",
            "TRUNCATE TABLE logs",
            "ALTER TABLE users ADD COLUMN test VARCHAR(255)",
            "CREATE TABLE new_table (id INT)"
        ]
        
        for sql in destructive_queries:
            issues = query_validator.check_destructive_operations(sql)
            assert len(issues) > 0
    
    def test_sql_injection_patterns(self):
        """Test SQL injection detection."""
        
        # Potential injection attempts
        injection_attempts = [
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM users UNION SELECT * FROM passwords",
            "SELECT * FROM users WHERE id = 1 OR 1=1 --",
        ]
        
        for sql in injection_attempts:
            has_injection = query_validator.check_sql_injection(sql)
            assert has_injection is True
        
        # Clean query
        clean_sql = "SELECT name, email FROM users WHERE active = true"
        has_injection = query_validator.check_sql_injection(clean_sql)
        assert has_injection is False
    
    def test_where_clause_detection(self):
        """Test WHERE clause detection."""
        
        # Query with WHERE clause
        sql = "DELETE FROM users WHERE inactive_days > 365"
        assert query_validator.has_where_clause(sql) is True
        
        # Query without WHERE clause
        sql = "DELETE FROM users"
        assert query_validator.has_where_clause(sql) is False
    
    def test_empty_query(self):
        """Test validation of empty queries."""
        
        is_safe, issues = query_validator.validate_query("", mode="readonly")
        assert is_safe is False
        assert any("empty" in issue.lower() for issue in issues)
    
    def test_complexity_estimation(self):
        """Test query complexity scoring."""
        
        # Simple query
        simple_sql = "SELECT * FROM users"
        complexity = query_validator.estimate_query_complexity(simple_sql)
        assert complexity == 0
        
        # Complex query with JOINs and aggregations
        complex_sql = """
        SELECT 
            u.region,
            COUNT(*) as order_count,
            SUM(o.total) as revenue
        FROM users u
        JOIN orders o ON u.id = o.user_id
        GROUP BY u.region
        ORDER BY revenue DESC
        """
        complexity = query_validator.estimate_query_complexity(complex_sql)
        assert complexity > 5


class TestDBAAuth:
    """Test DBA authentication."""
    
    def test_authentication(self):
        """Test DBA password authentication."""
        from security.auth import DBAAuth
        
        # Create mock session state
        session_state = {}
        
        # Test with wrong password
        result = DBAAuth.authenticate("wrong_password", session_state)
        assert result is False
        assert session_state.get('dba_authenticated') is not True
        
        # Note: Testing with correct password requires actual env variable
        # In production, use proper test fixtures
    
    def test_session_management(self):
        """Test session state management."""
        from security.auth import DBAAuth
        
        session_state = {}
        
        # Not authenticated initially
        assert DBAAuth.is_authenticated(session_state) is False
        
        # Logout should handle non-existent state
        DBAAuth.logout(session_state)
        assert session_state.get('dba_authenticated') is False


class TestAuditLogger:
    """Test audit logging functionality."""
    
    def test_query_logging(self):
        """Test query attempt logging."""
        from security.audit_logger import AuditLogger
        import tempfile
        import os
        
        # Use temp directory for tests
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            
            # Log a query
            log_id = logger.log_query_attempt(
                user_id="test_user",
                question="Show me all users",
                sql="SELECT * FROM users",
                mode="readonly"
            )
            
            assert log_id is not None
            assert log_id.startswith("20")  # Starts with year
            
            # Update result
            logger.log_query_result(
                log_id=log_id,
                success=True,
                error=None,
                execution_time=0.5,
                row_count=10
            )
            
            # Verify log file exists
            log_files = os.listdir(tmpdir)
            assert len(log_files) > 0
    
    def test_statistics(self):
        """Test audit statistics calculation."""
        from security.audit_logger import AuditLogger
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            
            # Log some queries
            for i in range(5):
                log_id = logger.log_query_attempt(
                    user_id=f"user_{i}",
                    question=f"Query {i}",
                    sql=f"SELECT * FROM table_{i}",
                    mode="readonly"
                )
                
                # 3 successful, 2 failed
                logger.log_query_result(
                    log_id=log_id,
                    success=(i < 3),
                    error="Error" if i >= 3 else None,
                    execution_time=0.5,
                    row_count=10 if i < 3 else 0
                )
            
            # Get statistics
            stats = logger.get_statistics()
            
            assert stats["total_queries"] == 5
            assert stats["successful_queries"] == 3
            assert stats["failed_queries"] == 2
            assert stats["success_rate"] == 60.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
