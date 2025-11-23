"""
Agent 2: SQL Generator - Generate PostgreSQL queries using SQLCoder-7B-2.
"""

import logging
import requests
import re
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from config.prompts import PromptTemplates

logger = logging.getLogger(__name__)


class SQLGeneratorAgent:
    """Agent responsible for SQL query generation and correction."""
    
    def __init__(self):
        """Initialize SQL generator with Cloudflare Workers AI credentials."""
        self.account_id = settings.api.cloudflare_account_id
        self.auth_token = settings.api.cloudflare_auth_token
        self.api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/defog/sqlcoder-7b-2"
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_sql(self, question: str, schema_context: str, examples: str) -> str:
        """
        Generate SQL query using SQLCoder-7B-2 via Cloudflare Workers AI.
        
        Args:
            question: Natural language question
            schema_context: Database schema information
            examples: Similar successful queries
            
        Returns:
            Generated SQL query string
            
        Raises:
            Exception: If SQL generation fails
        """
        try:
            prompt = PromptTemplates.sql_generation_prompt(question, schema_context, examples)
            
            payload = {
                "messages": [
                    {"role": "system", "content": PromptTemplates.SQL_GENERATION_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.2
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Extract SQL from response
            if 'result' in result and 'response' in result['result']:
                sql_response = result['result']['response']
            elif 'response' in result:
                sql_response = result['response']
            else:
                raise ValueError(f"Unexpected response format: {result}")
            
            # Clean and extract SQL
            sql = self.extract_sql_from_response(sql_response)
            
            logger.info(f"Generated SQL: {sql[:100]}...")
            return sql
            
        except requests.RequestException as e:
            logger.error(f"Cloudflare API request failed: {e}")
            raise
        
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise
    
    def correct_sql(self, failed_sql: str, error_message: str, error_type: str, schema_context: str) -> str:
        """
        Attempt to fix SQL based on error classification.
        
        Args:
            failed_sql: SQL query that failed
            error_message: Error message from database
            error_type: Classified error type
            schema_context: Database schema information
            
        Returns:
            Corrected SQL query
            
        Raises:
            Exception: If correction fails
        """
        try:
            prompt = PromptTemplates.error_correction_prompt(
                failed_sql=failed_sql,
                error_message=error_message,
                error_type=error_type,
                schema=schema_context
            )
            
            payload = {
                "messages": [
                    {"role": "system", "content": PromptTemplates.ERROR_CORRECTION_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.1  # Lower temperature for corrections
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Extract SQL from response
            if 'result' in result and 'response' in result['result']:
                sql_response = result['result']['response']
            elif 'response' in result:
                sql_response = result['response']
            else:
                raise ValueError(f"Unexpected response format: {result}")
            
            # Clean and extract SQL
            sql = self.extract_sql_from_response(sql_response)
            
            logger.info(f"Corrected SQL: {sql[:100]}...")
            return sql
            
        except Exception as e:
            logger.error(f"SQL correction failed: {e}")
            raise
    
    def extract_sql_from_response(self, response: str) -> str:
        """
        Extract clean SQL from LLM response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Clean SQL query
        """
        # Remove markdown code blocks
        sql = re.sub(r'```sql\n?', '', response)
        sql = re.sub(r'```\n?', '', sql)
        
        # Remove common prefixes
        prefixes = ['SQL:', 'Query:', 'Answer:', 'Here is the SQL:']
        for prefix in prefixes:
            if sql.strip().startswith(prefix):
                sql = sql.replace(prefix, '', 1)
        
        # Strip whitespace
        sql = sql.strip()
        
        # Remove trailing semicolon if present (we'll add it when executing)
        if sql.endswith(';'):
            sql = sql[:-1].strip()
        
        # Remove any explanatory text after the query
        # Look for common sentence starters
        explanation_markers = [
            '\n\nThis query',
            '\n\nThe above',
            '\n\nNote:',
            '\n\nExplanation:',
        ]
        
        for marker in explanation_markers:
            if marker in sql:
                sql = sql.split(marker)[0].strip()
        
        return sql
    
    def validate_sql_syntax(self, sql: str) -> bool:
        """
        Basic syntax validation for SQL.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            True if syntax appears valid, False otherwise
        """
        if not sql or len(sql.strip()) == 0:
            return False
        
        sql_upper = sql.upper().strip()
        
        # Check if it starts with a valid SQL keyword
        valid_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']
        starts_valid = any(sql_upper.startswith(keyword) for keyword in valid_starts)
        
        if not starts_valid:
            return False
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            logger.warning("Unbalanced parentheses in SQL")
            return False
        
        # Check for balanced quotes
        single_quotes = sql.count("'")
        if single_quotes % 2 != 0:
            logger.warning("Unbalanced single quotes in SQL")
            return False
        
        return True


# Global SQL generator agent instance
sql_generator = SQLGeneratorAgent()
