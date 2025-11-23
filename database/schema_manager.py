"""
Database schema retrieval and caching for LLM context.
"""

import logging
from typing import List, Dict, Optional
import psycopg2.extras

from database.connection import db

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages database schema retrieval and formatting for LLMs."""
    
    def __init__(self):
        """Initialize schema manager."""
        self._schema_cache: Optional[List[Dict]] = None
        self._relationships_cache: Optional[List[Dict]] = None
    
    def fetch_schema(self, force_refresh: bool = False) -> List[Dict]:
        """
        Fetch complete database schema from PostgreSQL information_schema.
        
        Args:
            force_refresh: Force refresh even if cached
            
        Returns:
            List of table dictionaries with columns and metadata
        """
        if self._schema_cache and not force_refresh:
            return self._schema_cache
        
        try:
            with db.get_readonly_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Query to get tables and columns
                query = """
                SELECT 
                    t.table_schema,
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    tc.constraint_type
                FROM information_schema.tables t
                LEFT JOIN information_schema.columns c 
                    ON t.table_name = c.table_name 
                    AND t.table_schema = c.table_schema
                LEFT JOIN information_schema.key_column_usage kcu
                    ON c.table_name = kcu.table_name
                    AND c.column_name = kcu.column_name
                    AND c.table_schema = kcu.table_schema
                LEFT JOIN information_schema.table_constraints tc
                    ON kcu.constraint_name = tc.constraint_name
                    AND kcu.table_schema = tc.table_schema
                WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
                    AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name, c.ordinal_position;
                """
                
                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()
                
                # Organize by table
                tables = {}
                for row in rows:
                    table_name = row['table_name']
                    if table_name not in tables:
                        tables[table_name] = {
                            'table_name': table_name,
                            'table_schema': row['table_schema'],
                            'columns': []
                        }
                    
                    tables[table_name]['columns'].append({
                        'column_name': row['column_name'],
                        'data_type': row['data_type'],
                        'is_nullable': row['is_nullable'],
                        'column_default': row['column_default'],
                        'constraint_type': row['constraint_type']
                    })
                
                self._schema_cache = list(tables.values())
                logger.info(f"Fetched schema for {len(self._schema_cache)} tables")
                return self._schema_cache
                
        except Exception as e:
            logger.error(f"Failed to fetch schema: {e}")
            raise
    
    def get_table_structure(self, table_name: str) -> Optional[Dict]:
        """
        Get detailed structure for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table structure dictionary or None if not found
        """
        schema = self.fetch_schema()
        for table in schema:
            if table['table_name'] == table_name:
                return table
        return None
    
    def get_relationships(self, force_refresh: bool = False) -> List[Dict]:
        """
        Extract foreign key relationships between tables.
        
        Args:
            force_refresh: Force refresh even if cached
            
        Returns:
            List of relationship dictionaries
        """
        if self._relationships_cache and not force_refresh:
            return self._relationships_cache
        
        try:
            with db.get_readonly_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                query = """
                SELECT
                    tc.table_name AS from_table,
                    kcu.column_name AS from_column,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema NOT IN ('pg_catalog', 'information_schema');
                """
                
                cursor.execute(query)
                relationships = cursor.fetchall()
                cursor.close()
                
                self._relationships_cache = [dict(row) for row in relationships]
                logger.info(f"Fetched {len(self._relationships_cache)} relationships")
                return self._relationships_cache
                
        except Exception as e:
            logger.error(f"Failed to fetch relationships: {e}")
            return []
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """
        Get sample rows from a table for context.
        
        Args:
            table_name: Name of the table
            limit: Number of sample rows to retrieve
            
        Returns:
            List of sample row dictionaries
        """
        try:
            with db.get_readonly_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Safely quote table name to prevent SQL injection
                query = f"SELECT * FROM {psycopg2.extensions.quote_ident(table_name, conn)} LIMIT %s;"
                cursor.execute(query, (limit,))
                
                samples = cursor.fetchall()
                cursor.close()
                
                return [dict(row) for row in samples]
                
        except Exception as e:
            logger.warning(f"Failed to fetch sample data for {table_name}: {e}")
            return []
    
    def build_schema_context(self, relevant_tables: Optional[List[str]] = None) -> str:
        """
        Format schema information for LLM prompt injection.
        
        Args:
            relevant_tables: List of table names to include (None = all tables)
            
        Returns:
            Formatted schema string for LLM context
        """
        schema = self.fetch_schema()
        relationships = self.get_relationships()
        
        # Filter tables if specified
        if relevant_tables:
            schema = [t for t in schema if t['table_name'] in relevant_tables]
        
        context_parts = []
        
        # Add table definitions
        for table in schema:
            table_name = table['table_name']
            context_parts.append(f"-- Table: {table_name}")
            
            # Build CREATE TABLE statement
            columns_def = []
            for col in table['columns']:
                col_def = f"    {col['column_name']} {col['data_type']}"
                
                if col['constraint_type'] == 'PRIMARY KEY':
                    col_def += " PRIMARY KEY"
                
                if col['is_nullable'] == 'NO':
                    col_def += " NOT NULL"
                
                if col['column_default']:
                    col_def += f" DEFAULT {col['column_default']}"
                
                columns_def.append(col_def)
            
            context_parts.append(f"CREATE TABLE {table_name} (")
            context_parts.append(",\n".join(columns_def))
            context_parts.append(");")
            
            # Add sample data
            samples = self.get_sample_data(table_name, limit=2)
            if samples:
                context_parts.append(f"-- Sample data from {table_name}:")
                if samples:
                    # Show column headers
                    headers = list(samples[0].keys())
                    context_parts.append(f"-- {' | '.join(headers)}")
                    # Show sample rows
                    for sample in samples:
                        values = [str(v)[:30] if v is not None else 'NULL' for v in sample.values()]
                        context_parts.append(f"-- {' | '.join(values)}")
            
            context_parts.append("")  # Empty line between tables
        
        # Add relationships
        if relationships:
            context_parts.append("-- Foreign Key Relationships:")
            for rel in relationships:
                context_parts.append(
                    f"-- {rel['from_table']}.{rel['from_column']} -> "
                    f"{rel['to_table']}.{rel['to_column']}"
                )
        
        return "\n".join(context_parts)
    
    def get_all_table_names(self) -> List[str]:
        """
        Get list of all table names in the database.
        
        Returns:
            List of table names
        """
        schema = self.fetch_schema()
        return [table['table_name'] for table in schema]


# Global schema manager instance
schema_manager = SchemaManager()
