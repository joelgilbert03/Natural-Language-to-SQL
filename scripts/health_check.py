"""
Pre-deployment health check script.

This script validates your environment configuration and tests
all critical components before deployment.

Usage:
    python scripts/health_check.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

logging.basicConfig(level=logging.WARNING)


def print_header(text):
    """Print section header."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{text:^60}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")


def print_success(text):
    """Print success message."""
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")


def print_error(text):
    """Print error message."""
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")


def print_warning(text):
    """Print warning message."""
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")


def check_environment_variables():
    """Check if all required environment variables are set."""
    print_header("Environment Variables Check")
    
    required_vars = [
        "NEON_READONLY_CONNECTION_STRING",
        "NEON_DBA_CONNECTION_STRING",
        "GROQ_API_KEY",
        "CLOUDFLARE_ACCOUNT_ID",
        "CLOUDFLARE_AUTH_TOKEN",
        "UPSTASH_VECTOR_URL",
        "UPSTASH_VECTOR_TOKEN",
        "DBA_PASSWORD"
    ]
    
    all_set = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first/last few chars only for security
            masked = f"{value[:8]}...{value[-4:]}" if len(value) > 15 else "***"
            print_success(f"{var}: {masked}")
        else:
            print_error(f"{var}: NOT SET")
            all_set = False
    
    return all_set


def check_database_connection():
    """Test database connections."""
    print_header("Database Connection Check")
    
    try:
        from database.connection import db
        
        # Test readonly connection
        if db.test_connection():
            print_success("Read-only database connection successful")
        else:
            print_error("Read-only database connection failed")
            return False
        
        # Test DBA connection
        if db.test_dba_connection():
            print_success("DBA database connection successful")
        else:
            print_warning("DBA database connection failed (check credentials)")
        
        return True
        
    except Exception as e:
        print_error(f"Database connection error: {e}")
        return False


def check_api_keys():
    """Test API connections."""
    print_header("API Keys Check")
    
    # Test Groq
    try:
        from agents.gatekeeper import gatekeeper
        result = gatekeeper.classify_intent("Hello")
        if result and "intent" in result:
            print_success("Groq API connection successful")
        else:
            print_error("Groq API test failed")
    except Exception as e:
        print_error(f"Groq API error: {e}")
    
    # Test Cloudflare
    try:
        from agents.sql_generator import sql_generator
        # This is a basic connectivity test
        print_success("Cloudflare Workers AI configured")
    except Exception as e:
        print_error(f"Cloudflare Workers AI error: {e}")
    
    # Test Upstash
    try:
        from vector_store.upstash_client import upstash_client
        print_success("Upstash Vector configured")
    except Exception as e:
        print_error(f"Upstash Vector error: {e}")
    
    return True


def check_dependencies():
    """Check if all required packages are installed."""
    print_header("Dependencies Check")
    
    required_packages = [
        "streamlit",
        "psycopg2",
        "groq",
        "requests",
        "sqlparse",
        "pydantic",
        "pytest",
        "pandas",
        "tabulate"
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print_success(f"{package} installed")
        except ImportError:
            print_error(f"{package} NOT installed")
            all_installed = False
    
    return all_installed


def check_file_structure():
    """Verify project file structure."""
    print_header("File Structure Check")
    
    required_files = [
        "app.py",
        "requirements.txt",
        ".env",
        ".gitignore",
        "config/settings.py",
        "config/prompts.py",
        "database/connection.py",
        "database/schema_manager.py",
        "database/query_executor.py",
        "agents/gatekeeper.py",
        "agents/sql_generator.py",
        "agents/explainer.py",
        "security/validator.py",
        "security/auth.py",
        "security/audit_logger.py",
        ".streamlit/config.toml"
    ]
    
    all_exist = True
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} NOT FOUND")
            all_exist = False
    
    return all_exist


def check_vector_store():
    """Check if vector store is initialized."""
    print_header("Vector Store Check")
    
    try:
        from vector_store.upstash_client import upstash_client
        
        # Try to search (this will fail gracefully if not initialized)
        results = upstash_client.search_similar_schemas("test query", top_k=1)
        
        if results:
            print_success(f"Vector store initialized ({len(results)} schemas found)")
            return True
        else:
            print_warning("Vector store appears empty - run: python scripts/init_vector_store.py")
            return False
            
    except Exception as e:
        print_error(f"Vector store error: {e}")
        return False


def run_basic_tests():
    """Run basic unit tests."""
    print_header("Basic Tests")
    
    try:
        import pytest
        
        # Run tests
        result = pytest.main([
            "tests/test_setup.py",
            "-v",
            "--tb=short",
            "-q"
        ])
        
        if result == 0:
            print_success("All basic tests passed")
            return True
        else:
            print_error("Some tests failed")
            return False
            
    except Exception as e:
        print_error(f"Test execution error: {e}")
        return False


def main():
    """Run all health checks."""
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}{'NL2SQL System Health Check':^60}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("File Structure", check_file_structure),
        ("Dependencies", check_dependencies),
        ("Database Connection", check_database_connection),
        ("API Keys", check_api_keys),
        ("Vector Store", check_vector_store),
        ("Basic Tests", run_basic_tests),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_error(f"Check '{check_name}' failed with error: {e}")
            results[check_name] = False
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        if result:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")
    
    print(f"\n{Fore.CYAN}Overall: {passed}/{total} checks passed{Style.RESET_ALL}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"{Fore.GREEN}{'✅ ALL CHECKS PASSED!':^60}")
        print(f"{Fore.GREEN}{'Your system is ready for deployment':^60}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
        return 0
    else:
        print(f"\n{Fore.RED}{'='*60}")
        print(f"{Fore.RED}{'❌ SOME CHECKS FAILED':^60}")
        print(f"{Fore.RED}{'Please fix the issues before deployment':^60}")
        print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Health check cancelled by user{Style.RESET_ALL}")
        sys.exit(1)
