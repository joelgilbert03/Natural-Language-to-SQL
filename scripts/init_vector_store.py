"""
Initialize the vector store with database schemas.

This script should be run once after setting up your database to populate
the Upstash Vector store with schema embeddings for semantic search.

Usage:
    python scripts/init_vector_store.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import db
from database.schema_manager import schema_manager
from vector_store.upstash_client import upstash_client
from vector_store.embeddings import embedding_helper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_vector_store():
    """Initialize Upstash Vector store with database schemas."""
    
    logger.info("=== Initializing Vector Store ===")
    
    # Step 1: Test database connection
    logger.info("Step 1: Testing database connection...")
    if not db.test_connection():
        logger.error("❌ Database connection failed! Check your connection string.")
        return False
    logger.info("✅ Database connection successful")
    
    # Step 2: Initialize Upstash Vector
    logger.info("\nStep 2: Initializing Upstash Vector store...")
    try:
        upstash_client.initialize_vector_store()
        logger.info("✅ Upstash Vector initialized")
    except Exception as e:
        logger.error(f"❌ Upstash initialization failed: {e}")
        return False
    
    # Step 3: Fetch database schema
    logger.info("\nStep 3: Fetching database schema...")
    try:
        schema_info = schema_manager.fetch_schema()
        logger.info(f"✅ Found {len(schema_info)} tables")
        
        for table in schema_info:
            logger.info(f"  - {table['table_name']} ({len(table['columns'])} columns)")
    except Exception as e:
        logger.error(f"❌ Schema fetch failed: {e}")
        return False
    
    # Step 4: Store schema embeddings
    logger.info("\nStep 4: Storing schema embeddings in vector database...")
    stored_count = 0
    
    for table_info in schema_info:
        try:
            # Store in Upstash Vector (it will create embeddings automatically)
            upstash_client.store_schema_embeddings(table_info)
            
            stored_count += 1
            logger.info(f"  ✅ Stored: {table_info['table_name']}")
            
        except Exception as e:
            logger.error(f"  ❌ Failed to store {table_info['table_name']}: {e}")
    
    logger.info(f"\n✅ Successfully stored {stored_count}/{len(schema_info)} schemas")
    
    # Step 5: Test semantic search
    logger.info("\nStep 5: Testing semantic search...")
    try:
        test_query = "find user information"
        results = upstash_client.search_similar_schemas(test_query, top_k=3)
        
        logger.info(f"✅ Search test successful! Found {len(results)} results for '{test_query}':")
        for i, result in enumerate(results, 1):
            logger.info(f"  {i}. {result['table_name']} (score: {result.get('score', 'N/A')})")
    
    except Exception as e:
        logger.error(f"❌ Search test failed: {e}")
    
    logger.info("\n=== Initialization Complete ===")
    logger.info("\n🎉 Your vector store is ready! You can now run the main application.")
    
    return True


if __name__ == "__main__":
    success = initialize_vector_store()
    sys.exit(0 if success else 1)
