"""
Embedding generation utilities for vector search.

Note: Upstash Vector provides built-in embedding generation,
so this module provides helper functions for text preparation.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class EmbeddingHelper:
    """Helper functions for preparing text for embedding."""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text before embedding generation.
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def embed_schema(table_structure: Dict) -> str:
        """
        Format table schema for embedding.
        
        Args:
            table_structure: Table structure dictionary from schema manager
            
        Returns:
            Formatted text suitable for embedding
        """
        table_name = table_structure.get('table_name', '')
        columns = table_structure.get('columns', [])
        
        # Create descriptive text
        parts = [f"Table {table_name}"]
        
        # Add column information
        if columns:
            column_desc = []
            for col in columns:
                col_name = col.get('column_name', '')
                col_type = col.get('data_type', '')
                column_desc.append(f"{col_name} {col_type}")
            
            parts.append(f"with columns: {', '.join(column_desc)}")
        
        text = " ".join(parts)
        return EmbeddingHelper.normalize_text(text)
    
    @staticmethod
    def embed_question(question: str) -> str:
        """
        Normalize and prepare user question for embedding.
        
        Args:
            question: User's natural language question
            
        Returns:
            Normalized question
        """
        # Basic normalization
        question = EmbeddingHelper.normalize_text(question)
        
        # Remove question marks and punctuation for better matching
        question = re.sub(r'[?!.,;:]', '', question)
        
        return question.strip()
    
    @staticmethod
    def format_example_queries(similar_queries: List[Dict]) -> str:
        """
        Format similar queries into a examples string for prompt.
        
        Args:
            similar_queries: List of similar query dictionaries
            
        Returns:
            Formatted examples text
        """
        if not similar_queries:
            return "No similar examples found."
        
        examples = []
        for i, query in enumerate(similar_queries, 1):
            question = query.get('question', 'N/A')
            sql = query.get('sql', 'N/A')
            examples.append(f"Example {i}:\nQuestion: {question}\nSQL: {sql}\n")
        
        return "\n".join(examples)
    
    @staticmethod
    def expand_abbreviations(text: str) -> str:
        """
        Expand common abbreviations in queries.
        
        Args:
            text: Text with potential abbreviations
            
        Returns:
            Text with expanded abbreviations
        """
        abbreviations = {
            r'\bqty\b': 'quantity',
            r'\bamt\b': 'amount',
            r'\btot\b': 'total',
            r'\bavg\b': 'average',
            r'\bmax\b': 'maximum',
            r'\bmin\b': 'minimum',
            r'\bnum\b': 'number',
            r'\bpct\b': 'percent',
            r'\bid\b': 'identifier',
        }
        
        for abbrev, full in abbreviations.items():
            text = re.sub(abbrev, full, text, flags=re.IGNORECASE)
        
        return text


# Global embedding helper instance
embedding_helper = EmbeddingHelper()
