"""
Upstash Vector database client for semantic search and query history.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

try:
    from upstash_vector import Index
except ImportError:
    Index = None

from config.settings import settings

logger = logging.getLogger(__name__)


class UpstashClient:
    """Interface with Upstash Vector for semantic schema search and query history."""
    
    def __init__(self):
        """Initialize Upstash Vector client."""
        self._index: Optional[Any] = None
        self._initialized = False
    
    def initialize_vector_store(self) -> bool:
        """
        Setup Upstash client and verify connection.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
        
        if Index is None:
            logger.error("upstash-vector package not installed")
            return False
        
        try:
            self._index = Index(
                url=settings.upstash.vector_url,
                token=settings.upstash.vector_token
            )
            
            # Test connection
            info = self._index.info()
            logger.info(f"Upstash Vector initialized: {info}")
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Upstash Vector: {e}")
            return False
    
    def store_schema_embeddings(self, table_data: Dict) -> bool:
        """
        Embed and store table schema in vector database.
        
        Args:
            table_data: Dictionary containing table schema information
                - table_name: Name of the table
                - columns: List of column dictionaries
                - table_schema: Schema name
                
        Returns:
            True if storage successful, False otherwise
        """
        if not self._initialized:
            if not self.initialize_vector_store():
                return False
        
        try:
            table_name = table_data.get('table_name')
            
            # Create text description for embedding
            description_parts = [f"Table: {table_name}"]
            
            # Add column information
            columns = table_data.get('columns', [])
            column_names = [col['column_name'] for col in columns]
            description_parts.append(f"Columns: {', '.join(column_names)}")
            
            # Add data types
            type_info = [f"{col['column_name']} ({col['data_type']})" for col in columns]
            description_parts.append(f"Column types: {', '.join(type_info)}")
            
            description = " | ".join(description_parts)
            
            # Store in vector database
            # Upstash Vector will automatically generate embeddings
            self._index.upsert(
                vectors=[
                    {
                        "id": f"schema_{table_name}",
                        "data": description,
                        "metadata": {
                            "type": "schema",
                            "table_name": table_name,
                            "columns": column_names,
                            "column_count": len(columns)
                        }
                    }
                ]
            )
            
            logger.info(f"Stored schema embedding for table: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store schema embedding: {e}")
            return False
    
    def store_successful_query(self, question: str, sql: str, metadata: Dict) -> bool:
        """
        Store successful query in history for future reference.
        
        Args:
            question: Natural language question
            sql: SQL query that was executed
            metadata: Additional metadata (execution_time, row_count, timestamp)
            
        Returns:
            True if storage successful, False otherwise
        """
        if not self._initialized:
            if not self.initialize_vector_store():
                return False
        
        try:
            # Create unique ID based on timestamp
            query_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Store with question as the searchable text
            self._index.upsert(
                vectors=[
                    {
                        "id": query_id,
                        "data": question,
                        "metadata": {
                            "type": "query",
                            "question": question,
                            "sql": sql,
                            "execution_time": metadata.get("execution_time", 0.0),
                            "row_count": metadata.get("row_count", 0),
                            "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                            "success": True
                        }
                    }
                ]
            )
            
            logger.info(f"Stored successful query: {query_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store query history: {e}")
            return False
    
    def search_similar_schemas(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for table schemas relevant to the query.
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            
        Returns:
            List of relevant table schema dictionaries
        """
        if not self._initialized:
            if not self.initialize_vector_store():
                return []
        
        try:
            # Query vector database
            results = self._index.query(
                data=query,
                top_k=top_k,
                include_metadata=True,
                filter="type = 'schema'"
            )
            
            # Extract table information from results
            schemas = []
            for result in results:
                if hasattr(result, 'metadata'):
                    schemas.append({
                        "table_name": result.metadata.get("table_name"),
                        "columns": result.metadata.get("columns", []),
                        "relevance_score": result.score if hasattr(result, 'score') else 0.0
                    })
            
            logger.info(f"Found {len(schemas)} relevant schemas for query")
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to search schemas: {e}")
            return []
    
    def search_similar_queries(self, question: str, top_k: int = 3) -> List[Dict]:
        """
        Find similar past queries for few-shot learning.
        
        Args:
            question: Natural language question
            top_k: Number of similar queries to return
            
        Returns:
            List of similar query dictionaries with questions and SQL
        """
        if not self._initialized:
            if not self.initialize_vector_store():
                return []
        
        try:
            # Query vector database
            results = self._index.query(
                data=question,
                top_k=top_k,
                include_metadata=True,
                filter="type = 'query'"
            )
            
            # Extract query information
            similar_queries = []
            for result in results:
                if hasattr(result, 'metadata'):
                    similar_queries.append({
                        "question": result.metadata.get("question"),
                        "sql": result.metadata.get("sql"),
                        "execution_time": result.metadata.get("execution_time", 0.0),
                        "relevance_score": result.score if hasattr(result, 'score') else 0.0
                    })
            
            logger.info(f"Found {len(similar_queries)} similar queries")
            return similar_queries
            
        except Exception as e:
            logger.error(f"Failed to search query history: {e}")
            return []
    
    def clear_all_data(self) -> bool:
        """
        Clear all data from vector store (use with caution).
        
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            if not self.initialize_vector_store():
                return False
        
        try:
            # Note: Upstash Vector doesn't have a direct clear all method
            # This would need to be implemented by fetching all IDs and deleting
            logger.warning("Clear all data not implemented - requires manual deletion")
            return False
            
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")
            return False


# Global Upstash client instance
upstash_client = UpstashClient()
