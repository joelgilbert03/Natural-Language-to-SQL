"""
NL2SQL - Natural Language to SQL Query System
Main Streamlit Application
"""

import streamlit as st
import time
import logging
import sys
from typing import Optional, Tuple, List, Dict
from datetime import datetime

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="NL2SQL - Natural Language to SQL",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Try to import configuration and modules
try:
    from config.settings import settings
    from config.prompts import EXAMPLE_QUERIES
    from database.connection import db
    from database.schema_manager import schema_manager
    from database.query_executor import query_executor
    from vector_store.upstash_client import upstash_client
    from vector_store.embeddings import embedding_helper
    from agents.gatekeeper import gatekeeper
    from agents.sql_generator import sql_generator
    from agents.explainer import explainer
    from security.validator import query_validator
    from security.audit_logger import audit_logger
    from utils.error_handler import error_handler
    from utils.sql_parser import sql_parser
    from utils.helpers import (
        format_execution_time,
        generate_session_id,
        pluralize,
        calculate_success_rate
    )
    
    CONFIG_LOADED = True
    CONFIG_ERROR = None
    
except Exception as e:
    CONFIG_LOADED = False
    CONFIG_ERROR = str(e)
    st.error(f"""
    ### ⚠️ Configuration Error
    
    The application failed to load configuration:
    
    ```
    {CONFIG_ERROR}
    ```
    
    **Common Causes:**
    1. Missing environment variables/secrets
    2. Invalid database connection string
    3. Missing API keys
    
    **Required Secrets (check Settings → Repository secrets):**
    - `NEON_READONLY_CONNECTION_STRING`
    - `GROQ_API_KEY`
    - `CLOUDFLARE_ACCOUNT_ID`
    - `CLOUDFLARE_AUTH_TOKEN`
    - `UPSTASH_VECTOR_URL`
    - `UPSTASH_VECTOR_TOKEN`
    
    Please add all required secrets in Settings and the app will restart automatically.
    """)
    st.stop()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom CSS
st.markdown("""
<style>
    .stAlert > div {
        padding: 1rem;
    }
    .success-metric {
        color: #00C851;
    }
    .error-metric {
        color: #ff4444;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ====================  SESSION STATE INITIALIZATION ====================

def initialize_session_state():
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "schema_cache" not in st.session_state:
        st.session_state.schema_cache = None
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = generate_session_id()
    
    if "query_stats" not in st.session_state:
        st.session_state.query_stats = {
            "total": 0,
            "successful": 0,
            "failed": 0
        }


# ==================== SQL GENERATION WITH RETRIES ====================

def generate_sql_with_retries(
    question: str,
    schema: str,
    examples: str,
    max_retries: int = 3
) -> Tuple[Optional[str], int]:
    """
    Attempt SQL generation with automatic error correction.
    
    Returns:
        Tuple of (sql query or None, number of attempts)
    """
    attempts = 0
    last_sql = None
    last_error = None
    
    while attempts < max_retries:
        attempts += 1
        
        try:
            if attempts == 1:
                # First attempt - generate fresh SQL
                sql = sql_generator.generate_sql(question, schema, examples)
            else:
                # Correction attempt
                err_type = error_handler.classify_error(last_error)
                error_context = error_handler.generate_correction_context(
                    error_type=err_type,
                    error_message=last_error,
                    schema=schema
                )
                sql = sql_generator.correct_sql(
                    failed_sql=last_sql,
                    error_message=last_error,
                    error_type=err_type,
                    schema_context=error_context
                )
            
            # Validate basic syntax
            if not sql_generator.validate_sql_syntax(sql):
                raise ValueError("Invalid SQL syntax generated")
            
            # Test with EXPLAIN (doesn't execute but validates syntax)
            explain_result = query_executor.explain_query(sql)
            
            if explain_result["success"]:
                # SQL is valid!
                logger.info(f"SQL validated successfully after {attempts} attempt(s)")
                return sql, attempts
            else:
                # EXPLAIN failed - syntax error
                raise Exception(explain_result["error"])
                
        except Exception as e:
            last_sql = sql if 'sql' in locals() else last_sql
            last_error = str(e)
            logger.warning(f"Attempt {attempts} failed: {last_error}")
            
            if attempts >= max_retries:
                logger.error(f"Failed to generate valid SQL after {attempts} attempts")
                return None, attempts
    
    return None, attempts


# ==================== QUERY EXECUTION ====================

def execute_and_display(sql: str, original_question: str):
    """Execute validated SQL and display results."""
    
    # Start audit log
    log_id = audit_logger.log_query_attempt(
        user_id=st.session_state.session_id,
        question=original_question,
        sql=sql,
        mode="readonly"
    )
    
    # Execute query
    with st.spinner("⚡ Executing query..."):
        start_time = time.time()
        result = query_executor.execute_readonly_query(sql)
        execution_time = time.time() - start_time
    
    # Update audit log
    audit_logger.log_query_result(
        log_id=log_id,
        success=result["success"],
        error=result.get("error"),
        execution_time=execution_time,
        row_count=result.get("row_count", 0)
    )
    
    # Update stats
    st.session_state.query_stats["total"] += 1
    if result["success"]:
        st.session_state.query_stats["successful"] += 1
    else:
        st.session_state.query_stats["failed"] += 1
    
    if not result["success"]:
        error_msg = error_handler.format_error_for_user(
            error_handler.classify_error(result["error"]),
            result["error"]
        )
        st.error(error_msg)
        return
    
    # Store successful query in vector database
    if result["success"] and result["row_count"] > 0:
        upstash_client.store_successful_query(
            question=original_question,
            sql=sql,
            metadata={
                "execution_time": execution_time,
                "row_count": result["row_count"],
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # Generate explanation with Agent 3
    with st.spinner("🤖 Analyzing results..."):
        explanation = explainer.explain_results(
            question=original_question,
            sql=sql,
            results=result["data"]
        )
    
    # Display results
    with st.chat_message("assistant"):
        st.markdown(explanation)
        
        # Show data table
        if result["data"]:
            with st.expander("📊 View Data Table", expanded=False):
                st.dataframe(result["data"], use_container_width=True)
                
                if result.get("truncated"):
                    st.warning(f"⚠️ Results truncated to {len(result['data'])} rows")
        
        # Show SQL query
        with st.expander("🔍 View SQL Query", expanded=False):
            st.code(sql, language="sql")
        
        # Show execution info
        st.caption(
            f"⚡ Executed in {format_execution_time(execution_time)} | "
            f"{pluralize(result['row_count'], 'row')}"
        )
    
    # Save to message history
    st.session_state.messages.append({
        "role": "assistant",
        "content": explanation,
        "sql": sql,
        "data": result["data"][:10],  # Store only sample
        "execution_time": execution_time,
        "row_count": result["row_count"]
    })


# ==================== MESSAGE HANDLER ====================

def handle_user_message(user_message: str):
    """Process user message through the agent pipeline."""
    
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_message})
    
    with st.chat_message("user"):
        st.write(user_message)
    
    # Agent 1: Gatekeeper classification
    with st.spinner("🤖 Analyzing your question..."):
        intent_result = gatekeeper.classify_intent(user_message)
    
    # Handle different intents
    if intent_result["intent"] == "greeting":
        response = intent_result["response"]
        with st.chat_message("assistant"):
            st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        return
    
    if intent_result["needs_clarification"]:
        response = intent_result["response"]
        with st.chat_message("assistant"):
            st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        return
    
    if intent_result["intent"] != "data_query":
        response = "I can only help with data queries. Please ask a question about your database."
        with st.chat_message("assistant"):
            st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        return
    
    # Preprocess question
    processed_question = gatekeeper.preprocess_question(user_message)
    
    # Retrieve relevant schema
    with st.spinner("📚 Retrieving database schema..."):
        similar_schemas = upstash_client.search_similar_schemas(processed_question, top_k=5)
        similar_queries = upstash_client.search_similar_queries(processed_question, top_k=3)
        
        # Build schema context
        if similar_schemas:
            relevant_tables = [s["table_name"] for s in similar_schemas]
            schema_context = schema_manager.build_schema_context(relevant_tables)
        else:
            # Fallback to full schema
            schema_context = schema_manager.build_schema_context()
        
        # Build examples context
        examples_context = embedding_helper.format_example_queries(similar_queries)
        if not similar_queries:
            examples_context = EXAMPLE_QUERIES
    
    # Agent 2: Generate SQL with retries
    with st.spinner("🔨 Generating SQL query..."):
        sql_query, attempts = generate_sql_with_retries(
            question=processed_question,
            schema=schema_context,
            examples=examples_context
        )
    
    if sql_query is None:
        with st.chat_message("assistant"):
            st.error("❌ I couldn't generate a valid SQL query after multiple attempts. Please try rephrasing your question or make it more specific.")
        return
    
    # Validate query
    with st.spinner("🔒 Validating query..."):
        is_safe, issues = query_validator.validate_query(
            sql_query,
            "readonly"
        )
    
    if not is_safe:
        with st.chat_message("assistant"):
            st.error(f"❌ Query validation failed:\n\n" + "\n".join([f"- {issue}" for issue in issues]))
        return
    
    # Execute query
    execute_and_display(sql_query, processed_question)


# ==================== SIDEBAR ====================

def render_sidebar():
    """Render sidebar with mode controls and statistics."""
    
    with st.sidebar:
        st.title("🔍 NL2SQL Settings")
        
        # Mode indicator
        st.info("🔒 **Read-Only Mode**\n\nSafe data exploration with SELECT queries only")
        
        st.divider()
        
        # Statistics
        st.subheader("📊 Statistics")
        
        stats = st.session_state.query_stats
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Queries", stats["total"])
        with col2:
            success_rate = calculate_success_rate(stats["successful"], stats["total"])
            st.metric("Success Rate", f"{success_rate:.0f}%")
        
        st.metric("Successful", stats["successful"], delta=None)
        st.metric("Failed", stats["failed"], delta=None)
        
        # Audit logs
        if st.button("View Audit Logs"):
            audit_stats = audit_logger.get_statistics()
            st.json(audit_stats)


# ==================== MAIN APP ====================

def main():
    """Main application entry point."""
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main header
    st.title("🔍 Natural Language to SQL")
    st.markdown("""
    Ask questions about your database in plain English, and I'll translate them to SQL!
    
    **Examples:**
    - "Show me total sales by region for last month"
    - "How many active customers do we have?"
    - "List top 10 products by revenue"
    """)
    
    st.divider()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Show additional info for assistant messages
            if message["role"] == "assistant" and "sql" in message:
                with st.expander("View Details"):
                    st.code(message["sql"], language="sql")
                    if "execution_time" in message:
                        st.caption(f"⚡ {format_execution_time(message['execution_time'])}")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        handle_user_message(prompt)


# ==================== RUN APP ====================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        st.error(f"An unexpected error occurred: {str(e)}")
        st.info("Please check the logs for more details.")
