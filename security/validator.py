"""
Query validation and safety checks before execution.
"""

import logging
import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Statement
from sqlparse.tokens import Keyword, DML
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class QueryValidator:
    """Validates SQL queries for safety and policy compliance."""
    
    DESTRUCTIVE_KEYWORDS = ['DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'RENAME']
    
    INJECTION_PATTERNS = [
        r';.*DROP',
        r';.*DELETE',
        r';.*UPDATE',
        r'UNION.*SELECT',
        r'--.*$',
        r'/\*.*\*/',
        r'xp_cmdshell',
        r'exec\s*\(',
    ]
    
    def __init__(self):
        """Initialize query validator."""
        pass
    
    def validate_query(self, sql: str, mode: str = "readonly") -> Tuple[bool, List[str]]:
        """
        Validate query before execution.
        
        Args:
            sql: SQL query to validate
            mode: Execution mode ("readonly" or "dba")
            
        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        issues = []
        
        if not sql or len(sql.strip()) == 0:
            issues.append("Empty query")
            return False, issues
        
        # Parse SQL
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                issues.append("Failed to parse SQL")
                return False, issues
            
            statement = parsed[0]
        except Exception as e:
            issues.append(f"SQL parsing error: {str(e)}")
            return False, issues
        
        # Check mode-specific rules
        if mode == "readonly":
            if not self._is_select_only(statement):
                issues.append("Only SELECT queries allowed in read-only mode")
        
        # Check destructive operations
        destructive_ops = self.check_destructive_operations(sql)
        if destructive_ops:
            issues.extend(destructive_ops)
        
        # Check SQL injection patterns
        if self.check_sql_injection(sql):
            issues.append("Potential SQL injection detected")
        
        # Check for UPDATE/DELETE without WHERE clause in DBA mode
        if mode == "dba":
            query_type = self._get_query_type(statement)
            if query_type in ["UPDATE", "DELETE"]:
                if not self.has_where_clause(sql):
                    issues.append(f"{query_type} query without WHERE clause - affects all rows!")
        
        return (len(issues) == 0, issues)
    
    def _is_select_only(self, statement: Statement) -> bool:
        """
        Check if statement is SELECT only.
        
        Args:
            statement: Parsed SQL statement
            
        Returns:
            True if SELECT only, False otherwise
        """
        # Get first token type
        first_token = str(statement.token_first(skip_ws=True, skip_cm=True)).upper()
        
        if first_token == "WITH":
            # CTE - check if final query is SELECT
            sql_upper = str(statement).upper()
            # Look for the main query after CTE
            if "SELECT" in sql_upper:
                # Check there's no INSERT/UPDATE/DELETE after WITH
                for keyword in ["INSERT", "UPDATE", "DELETE"]:
                    if keyword in sql_upper:
                        return False
                return True
            return False
        
        return first_token == "SELECT"
    
    def _get_query_type(self, statement: Statement) -> str:
        """
        Get the type of SQL query.
        
        Args:
            statement: Parsed SQL statement
            
        Returns:
            Query type string (SELECT, INSERT, UPDATE, DELETE, DDL)
        """
        first_token = str(statement.token_first(skip_ws=True, skip_cm=True)).upper()
        
        if first_token in ["SELECT", "WITH"]:
            return "SELECT"
        elif first_token in ["INSERT", "UPDATE", "DELETE"]:
            return first_token
        else:
            return "DDL"
    
    def check_destructive_operations(self, sql: str) -> List[str]:
        """
        Check for destructive SQL operations.
        
        Args:
            sql: SQL query
            
        Returns:
            List of detected issues
        """
        issues = []
        sql_upper = sql.upper()
        
        for keyword in self.DESTRUCTIVE_KEYWORDS:
            if re.search(rf'\b{keyword}\b', sql_upper):
                issues.append(f"Destructive operation detected: {keyword}")
        
        return issues
    
    def check_sql_injection(self, sql: str) -> bool:
        """
        Check for common SQL injection patterns.
        
        Args:
            sql: SQL query
            
        Returns:
            True if potential injection detected, False otherwise
        """
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                logger.warning(f"Potential SQL injection pattern detected: {pattern}")
                return True
        
        # Check for multiple statements (semicolon followed by another statement)
        statements = sqlparse.split(sql)
        if len(statements) > 1:
            logger.warning("Multiple statements detected")
            return True
        
        return False
    
    def validate_table_names(self, sql: str, allowed_tables: List[str]) -> Tuple[bool, List[str]]:
        """
        Ensure query only references allowed tables.
        
        Args:
            sql: SQL query
            allowed_tables: List of allowed table names
            
        Returns:
            Tuple of (is_valid, list_of_invalid_tables)
        """
        try:
            parsed = sqlparse.parse(sql)[0]
            referenced_tables = self._extract_tables(parsed)
            
            invalid_tables = [table for table in referenced_tables if table not in allowed_tables]
            
            return (len(invalid_tables) == 0, invalid_tables)
            
        except Exception as e:
            logger.error(f"Failed to validate table names: {e}")
            return False, []
    
    def _extract_tables(self, statement: Statement) -> List[str]:
        """
        Extract table names from SQL statement.
        
        Args:
            statement: Parsed SQL statement
            
        Returns:
            List of table names
        """
        tables = []
        from_seen = False
        
        for token in statement.tokens:
            if from_seen:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        table_name = identifier.get_real_name()
                        if table_name:
                            tables.append(table_name)
                elif isinstance(token, Identifier):
                    table_name = token.get_real_name()
                    if table_name:
                        tables.append(table_name)
                from_seen = False
            
            if token.ttype is Keyword and token.value.upper() == 'FROM':
                from_seen = True
        
        return tables
    
    def has_where_clause(self, sql: str) -> bool:
        """
        Check if SQL query has a WHERE clause.
        
        Args:
            sql: SQL query
            
        Returns:
            True if WHERE clause present, False otherwise
        """
        try:
            parsed = sqlparse.parse(sql)[0]
            
            for token in parsed.tokens:
                if isinstance(token, Where):
                    return True
            
            # Also check with regex as backup
            if re.search(r'\bWHERE\b', sql, re.IGNORECASE):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check WHERE clause: {e}")
            # Default to True to be safe
            return True
    
    def estimate_query_complexity(self, sql: str) -> int:
        """
        Estimate query complexity score.
        
        Args:
            sql: SQL query
            
        Returns:
            Complexity score (higher = more complex)
        """
        complexity = 0
        sql_upper = sql.upper()
        
        # Count JOINs
        complexity += len(re.findall(r'\bJOIN\b', sql_upper)) * 2
        
        # Count subqueries
        complexity += sql.count('(SELECT') * 3
        
        # Count aggregations
        agg_functions = ['SUM', 'COUNT', 'AVG', 'MAX', 'MIN']
        for func in agg_functions:
            complexity += len(re.findall(rf'\b{func}\b', sql_upper))
        
        # Count GROUP BY
        if 'GROUP BY' in sql_upper:
            complexity += 2
        
        # Count ORDER BY
        if 'ORDER BY' in sql_upper:
            complexity += 1
        
        return complexity


# Global validator instance
query_validator = QueryValidator()
