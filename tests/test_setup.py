"""
Basic test to verify project setup and imports.
Run with: python -m pytest tests/test_setup.py -v
"""

import pytest


def test_imports():
    """Test that all main modules can be imported."""
    
    # Config
    from config import settings, prompts
    assert settings is not None
    assert prompts is not None
    
    # Database
    from database import connection, schema_manager, query_executor
    assert connection is not None
    assert schema_manager is not None
    assert query_executor is not None
    
    # Vector store
    from vector_store import upstash_client, embeddings
    assert upstash_client is not None
    assert embeddings is not None
    
    # Agents
    from agents import gatekeeper, sql_generator, explainer
    assert gatekeeper is not None
    assert sql_generator is not None
    assert explainer is not None
    
    # Security
    from security import validator, auth, audit_logger
    assert validator is not None
    assert auth is not None
    assert audit_logger is not None
    
    # Utils
    from utils import error_handler, sql_parser, helpers
    assert error_handler is not None
    assert sql_parser is not None
    assert helpers is not None


def test_config_loading():
    """Test that configuration loads properly."""
    from config.settings import settings
    
    # These might be empty in test but should be accessible
    assert hasattr(settings, 'database')
    assert hasattr(settings, 'api')
    assert hasattr(settings, 'upstash')
    assert hasattr(settings, 'security')


def test_prompt_templates():
    """Test that prompt templates are defined."""
    from config.prompts import PromptTemplates, EXAMPLE_QUERIES
    
    assert PromptTemplates.GATEKEEPER_SYSTEM is not None
    assert PromptTemplates.SQL_GENERATION_SYSTEM is not None
    assert PromptTemplates.RESULTS_EXPLANATION_SYSTEM is not None
    assert EXAMPLE_QUERIES is not None


def test_helper_functions():
    """Test basic helper functions."""
    from utils.helpers import (
        truncate_long_text,
        format_execution_time,
        pluralize
    )
    
    # Test truncate
    assert truncate_long_text("short", 10) == "short"
    assert len(truncate_long_text("very long text here", 10)) <= 10
    
    # Test time formatting
    assert "ms" in format_execution_time(0.5)
    assert "s" in format_execution_time(2.5)
    
    # Test pluralize
    assert "1 row" in pluralize(1, "row")
    assert "2 rows" in pluralize(2, "row")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
