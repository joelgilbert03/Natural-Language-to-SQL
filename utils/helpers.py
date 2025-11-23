"""
General utility helper functions.
"""

import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


def format_result_table(results: List[Dict], max_rows: int = 100) -> str:
    """
    Convert query results to markdown table.
    
    Args:
        results: Query results as list of dictionaries
        max_rows: Maximum number of rows to display
        
    Returns:
        Markdown formatted table string
    """
    if not results:
        return "_No results_"
    
    # Limit rows
    display_results = results[:max_rows]
    truncated = len(results) > max_rows
    
    try:
        # Use pandas for nice table formatting
        df = pd.DataFrame(display_results)
        
        # Format values
        for col in df.columns:
            df[col] = df[col].apply(lambda x: truncate_long_text(str(x), 100) if x is not None else 'NULL')
        
        # Convert to markdown
        markdown = df.to_markdown(index=False)
        
        if truncated:
            markdown += f"\n\n_... and {len(results) - max_rows} more rows_"
        
        return markdown
        
    except Exception as e:
        logger.error(f"Failed to format result table: {e}")
        # Fallback to simple format
        return str(results[:5])


def truncate_long_text(text: str, max_length: int = 50) -> str:
    """
    Safely truncate text with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def format_execution_time(seconds: float) -> str:
    """
    Format execution time in human-readable format.
    
    Args:
        seconds: Execution time in seconds
        
    Returns:
        Formatted time string (e.g., "450 ms", "2.3 s")
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"


def generate_session_id() -> str:
    """
    Generate unique session identifier.
    
    Returns:
        Unique session ID string
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    return f"session_{timestamp}_{unique_id}"


def safe_json_loads(json_str: str) -> Dict:
    """
    Parse JSON string with error handling.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed dictionary or empty dict if parsing fails
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return {}


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """
    Format timestamp for display.
    
    Args:
        timestamp: Datetime object (None = current time)
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    import re
    # Keep only alphanumeric, dash, underscore, and dot
    sanitized = re.sub(r'[^\w\-.]', '_', filename)
    # Remove leading/trailing dots and underscores
    sanitized = sanitized.strip('._')
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    return sanitized


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Return singular or plural form based on count.
    
    Args:
        count: Number of items
        singular: Singular form of word
        plural: Plural form (if None, adds 's' to singular)
        
    Returns:
        Appropriate form with count
    """
    if plural is None:
        plural = f"{singular}s"
    
    word = singular if count == 1 else plural
    return f"{count} {word}"


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes in human-readable format.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 KB", "2.3 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def calculate_success_rate(successful: int, total: int) -> float:
    """
    Calculate success rate percentage.
    
    Args:
        successful: Number of successful operations
        total: Total number of operations
        
    Returns:
        Success rate as percentage (0-100)
    """
    if total == 0:
        return 0.0
    return (successful / total) * 100


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries (later dicts override earlier ones).
    
    Args:
        *dicts: Variable number of dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def dict_to_table(data: Dict, title: Optional[str] = None) -> str:
    """
    Convert dictionary to simple markdown table.
    
    Args:
        data: Dictionary to convert
        title: Optional table title
        
    Returns:
        Markdown formatted table
    """
    lines = []
    
    if title:
        lines.append(f"### {title}\n")
    
    lines.append("| Key | Value |")
    lines.append("|-----|-------|")
    
    for key, value in data.items():
        # Format value
        if isinstance(value, (list, dict)):
            value = json.dumps(value)
        value_str = truncate_long_text(str(value), 100)
        
        lines.append(f"| {key} | {value_str} |")
    
    return "\n".join(lines)
