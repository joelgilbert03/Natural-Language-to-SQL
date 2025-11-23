"""
SQL error classification and handling.
"""

import logging
import re
from typing import Dict, Tuple
from psycopg2 import Error as PsycopgError

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Classifies and handles SQL execution errors."""
    
    ERROR_PATTERNS = {
        "column_name": [
            r'column "(\w+)" does not exist',
            r'no such column: (\w+)',
            r'unknown column',
        ],
        "table_name": [
            r'relation "(\w+)" does not exist',
            r'no such table: (\w+)',
            r'table.*not found',
        ],
        "syntax": [
            r'syntax error at or near "(\w+)"',
            r'syntax error',
            r'invalid syntax',
        ],
        "type_mismatch": [
            r'type mismatch',
            r'invalid input syntax for type',
            r'operator does not exist',
            r'cannot cast',
        ],
        "permission": [
            r'permission denied',
            r'must be owner of',
            r'access denied',
        ],
        "timeout": [
            r'timeout',
            r'canceling statement due to statement timeout',
        ]
    }
    
    def classify_error(self, error_message: str) -> str:
        """
        Classify error type based on error message.
        
        Args:
            error_message: Error message from database
            
        Returns:
            Error type: column_name, table_name, syntax, type_mismatch, 
                       permission, timeout, or other
        """
        error_lower = error_message.lower()
        
        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_lower):
                    logger.info(f"Classified error as: {error_type}")
                    return error_type
        
        logger.info("Error classified as: other")
        return "other"
    
    def generate_correction_context(
        self,
        error_type: str,
        error_message: str,
        schema: str
    ) -> str:
        """
        Generate specific guidance for error correction.
        
        Args:
            error_type: Classified error type
            error_message: Original error message
            schema: Database schema information
            
        Returns:
            Guidance text for SQL correction
        """
        guidance_templates = {
            "column_name": f"""The query references a column that doesn't exist.

Error: {error_message}

Please review the schema below and use only the columns that actually exist.
Ensure column names are spelled correctly and match the case if necessary.

Available Schema:
{schema}""",
            
            "table_name": f"""The query references a table that doesn't exist.

Error: {error_message}

Please review the schema below and use only the tables that actually exist.
Ensure table names are spelled correctly.

Available Schema:
{schema}""",
            
            "syntax": f"""There's a SQL syntax error in the query.

Error: {error_message}

Common syntax issues:
- Missing or extra commas
- Unmatched parentheses
- Incorrect keyword order
- Missing required clauses

Please fix the syntax according to PostgreSQL standards.

Schema for reference:
{schema}""",
            
            "type_mismatch": f"""There's a data type mismatch in the query.

Error: {error_message}

Common type issues:
- Comparing incompatible types (e.g., text vs integer)
- Missing type casts (use ::type or CAST(column AS type))
- Incorrect aggregate function usage

Please ensure proper type casting and compatible comparisons.

Schema for reference:
{schema}""",
            
            "permission": f"""The query requires elevated permissions.

Error: {error_message}

The query is attempting an operation that requires DBA privileges.
If in read-only mode, revise the query to use only SELECT operations.

Schema for reference:
{schema}""",
            
            "timeout": f"""The query exceeded the timeout limit.

Error: {error_message}

The query is taking too long to execute. Consider:
- Adding WHERE clause to limit rows
- Simplifying complex joins or subqueries
- Using indexes effectively

Schema for reference:
{schema}""",
            
            "other": f"""An error occurred while executing the query.

Error: {error_message}

Please review the error message and schema to correct the query.

Schema for reference:
{schema}"""
        }
        
        return guidance_templates.get(error_type, guidance_templates["other"])
    
    def parse_postgres_error(self, error: Exception) -> Dict[str, str]:
        """
        Extract structured information from psycopg2 errors.
        
        Args:
            error: Exception from psycopg2
            
        Returns:
            Dictionary with error_code, error_type, detail, hint
        """
        error_dict = {
            "error_code": "",
            "error_type": "unknown",
            "detail": str(error),
            "hint": ""
        }
        
        if isinstance(error, PsycopgError):
            if hasattr(error, 'pgcode'):
                error_dict["error_code"] = error.pgcode or ""
            
            if hasattr(error, 'pgerror'):
                error_dict["detail"] = error.pgerror or str(error)
            
            # Extract hint if available
            error_str = str(error)
            hint_match = re.search(r'HINT: (.*?)(\n|$)', error_str)
            if hint_match:
                error_dict["hint"] = hint_match.group(1)
        
        # Classify error type
        error_dict["error_type"] = self.classify_error(error_dict["detail"])
        
        return error_dict
    
    def should_retry(self, error_type: str, attempt: int, max_attempts: int = 3) -> bool:
        """
        Determine if error is retryable and within attempt limits.
        
        Args:
            error_type: Classified error type
            attempt: Current attempt number (1-indexed)
            max_attempts: Maximum number of attempts
            
        Returns:
            True if should retry, False otherwise
        """
        # Don't retry if max attempts reached
        if attempt >= max_attempts:
            return False
        
        # Retryable error types
        retryable_types = ["column_name", "table_name", "syntax", "type_mismatch"]
        
        # Don't retry permission or timeout errors
        non_retryable_types = ["permission", "timeout"]
        
        if error_type in non_retryable_types:
            return False
        
        if error_type in retryable_types:
            return True
        
        # For "other" errors, allow one retry
        return attempt < 2
    
    def format_error_for_user(self, error_type: str, error_message: str) -> str:
        """
        Format error message for user-friendly display.
        
        Args:
            error_type: Classified error type
            error_message: Original error message
            
        Returns:
            User-friendly error message
        """
        user_messages = {
            "column_name": "❌ The query references a column that doesn't exist in the database. Please check the column names.",
            "table_name": "❌ The query references a table that doesn't exist in the database. Please check the table names.",
            "syntax": "❌ There's a syntax error in the generated SQL query. This is usually due to incorrect SQL formatting.",
            "type_mismatch": "❌ There's a data type mismatch in the query. The query is trying to compare incompatible data types.",
            "permission": "❌ This operation requires DBA privileges. Please switch to DBA mode or revise your request.",
            "timeout": "❌ The query took too long to execute and was cancelled. Try narrowing down your request.",
            "other": "❌ An error occurred while executing the query."
        }
        
        base_message = user_messages.get(error_type, user_messages["other"])
        
        # Add truncated error detail
        error_snippet = error_message[:200] if len(error_message) > 200 else error_message
        
        return f"{base_message}\n\n**Technical Details:** {error_snippet}"


# Global error handler instance
error_handler = ErrorHandler()
