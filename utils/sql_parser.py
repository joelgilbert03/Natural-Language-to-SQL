"""
SQL parsing and analysis utilities.
"""

import logging
import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Statement
from sqlparse.tokens import Keyword, DML
from typing import List, Optional

logger = logging.getLogger(__name__)


class SQLParser:
    """Parse and analyze SQL queries."""
    
    def extract_tables(self, sql: str) -> List[str]:
        """
        Extract table names from SQL query.
        
        Args:
            sql: SQL query
            
        Returns:
            List of table names
        """
        try:
            parsed = sqlparse.parse(sql)[0]
            tables = []
            
            from_seen = False
            for token in parsed.tokens:
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
                
                if token.ttype is Keyword and token.value.upper() in ('FROM', 'JOIN', 'INTO', 'UPDATE'):
                    from_seen = True
            
            return list(set(tables))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Failed to extract tables: {e}")
            return []
    
    def extract_columns(self, sql: str) -> List[str]:
        """
        Extract column names from SQL query.
        
        Args:
            sql: SQL query
            
        Returns:
            List of column names
        """
        try:
            # This is a simplified extraction - won't catch all cases
            columns = []
            
            # Find SELECT clause columns
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_clause = select_match.group(1)
                
                # Split by comma
                parts = select_clause.split(',')
                for part in parts:
                    part = part.strip()
                    
                    # Skip asterisk
                    if '*' in part:
                        continue
                    
                    # Extract column name (handle aliases)
                    if ' AS ' in part.upper():
                        # Get the alias
                        alias = part.split(' AS ')[-1].strip()
                        columns.append(alias)
                    else:
                        # Get the column (may include table prefix)
                        col = part.split('.')[-1].strip()
                        # Remove function calls
                        col = re.sub(r'\(.*?\)', '', col).strip()
                        if col:
                            columns.append(col)
            
            return columns
            
        except Exception as e:
            logger.error(f"Failed to extract columns: {e}")
            return []
    
    def get_query_type(self, sql: str) -> str:
        """
        Get the type of SQL query.
        
        Args:
            sql: SQL query
            
        Returns:
            Query type: SELECT, INSERT, UPDATE, DELETE, or DDL
        """
        try:
            parsed = sqlparse.parse(sql)[0]
            first_token = str(parsed.token_first(skip_ws=True, skip_cm=True)).upper()
            
            if first_token in ['SELECT', 'WITH']:
                return 'SELECT'
            elif first_token == 'INSERT':
                return 'INSERT'
            elif first_token == 'UPDATE':
                return 'UPDATE'
            elif first_token == 'DELETE':
                return 'DELETE'
            else:
                return 'DDL'
                
        except Exception as e:
            logger.error(f"Failed to get query type: {e}")
            # Fallback to regex
            sql_upper = sql.strip().upper()
            if sql_upper.startswith('SELECT') or sql_upper.startswith('WITH'):
                return 'SELECT'
            elif sql_upper.startswith('INSERT'):
                return 'INSERT'
            elif sql_upper.startswith('UPDATE'):
                return 'UPDATE'
            elif sql_upper.startswith('DELETE'):
                return 'DELETE'
            else:
                return 'DDL'
    
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
            
            # Backup check with regex
            if re.search(r'\bWHERE\b', sql, re.IGNORECASE):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check WHERE clause: {e}")
            # Fallback to True to be safe
            return True
    
    def estimate_complexity(self, sql: str) -> int:
        """
        Estimate query complexity score.
        
        Args:
            sql: SQL query
            
        Returns:
            Complexity score (higher = more complex)
        """
        complexity = 0
        sql_upper = sql.upper()
        
        # Count JOINs (2 points each)
        complexity += len(re.findall(r'\bJOIN\b', sql_upper)) * 2
        
        # Count subqueries (3 points each)
        complexity += sql.count('(SELECT') * 3
        
        # Count aggregations (1 point each)
        agg_functions = ['SUM', 'COUNT', 'AVG', 'MAX', 'MIN', 'GROUP_CONCAT']
        for func in agg_functions:
            complexity += len(re.findall(rf'\b{func}\b', sql_upper))
        
        # Count GROUP BY (2 points)
        if 'GROUP BY' in sql_upper:
            complexity += 2
        
        # Count ORDER BY (1 point)
        if 'ORDER BY' in sql_upper:
            complexity += 1
        
        # Count HAVING (2 points)
        if 'HAVING' in sql_upper:
            complexity += 2
        
        # Count DISTINCT (1 point)
        if 'DISTINCT' in sql_upper:
            complexity += 1
        
        # Count UNION (2 points each)
        complexity += len(re.findall(r'\bUNION\b', sql_upper)) * 2
        
        return complexity
    
    def format_sql(self, sql: str, compact: bool = False) -> str:
        """
        Format SQL query for better readability.
        
        Args:
            sql: SQL query to format
            compact: If True, use minimal formatting; if False, use full formatting
            
        Returns:
            Formatted SQL string
        """
        try:
            if compact:
                # Remove extra whitespace
                formatted = ' '.join(sql.split())
            else:
                # Use sqlparse for formatting
                formatted = sqlparse.format(
                    sql,
                    reindent=True,
                    keyword_case='upper',
                    identifier_case='lower'
                )
            
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to format SQL: {e}")
            return sql
    
    def get_limit_clause(self, sql: str) -> Optional[int]:
        """
        Extract LIMIT value from SQL query.
        
        Args:
            sql: SQL query
            
        Returns:
            Limit value or None if no LIMIT clause
        """
        limit_match = re.search(r'\bLIMIT\s+(\d+)', sql, re.IGNORECASE)
        if limit_match:
            return int(limit_match.group(1))
        return None
    
    def add_limit_clause(self, sql: str, limit: int) -> str:
        """
        Add or update LIMIT clause in SQL query.
        
        Args:
            sql: SQL query
            limit: Limit value to add
            
        Returns:
            SQL with LIMIT clause
        """
        # Check if LIMIT already exists
        existing_limit = self.get_limit_clause(sql)
        
        if existing_limit is not None:
            # Replace existing LIMIT
            sql = re.sub(
                r'\bLIMIT\s+\d+',
                f'LIMIT {limit}',
                sql,
                flags=re.IGNORECASE
            )
        else:
            # Add LIMIT to end
            sql = sql.rstrip(';').strip()
            sql = f"{sql} LIMIT {limit}"
        
        return sql


# Global SQL parser instance
sql_parser = SQLParser()
