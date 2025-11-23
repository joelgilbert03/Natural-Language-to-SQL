"""
Audit logging for query attempts and DBA actions.
"""

import logging
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logs all query attempts and DBA actions for compliance and debugging."""
    
    def __init__(self, log_dir: str = "audit_logs"):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._log_cache: Dict[str, Dict] = {}
    
    def log_query_attempt(
        self,
        user_id: str,
        question: str,
        sql: str,
        mode: str
    ) -> str:
        """
        Log a query attempt.
        
        Args:
            user_id: Session or user identifier
            question: Natural language question
            sql: Generated SQL query
            mode: Execution mode (readonly or dba)
            
        Returns:
            Log entry ID
        """
        log_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        log_entry = {
            "log_id": log_id,
            "timestamp": datetime.now().isoformat(),
            "session_id": user_id,
            "mode": mode,
            "question": question,
            "generated_sql": sql,
            "validation_passed": None,
            "execution_success": None,
            "error_message": None,
            "execution_time_seconds": None,
            "rows_returned": None,
            "dba_approved": False,
            "approver_id": None
        }
        
        # Cache in memory
        self._log_cache[log_id] = log_entry
        
        # Write to file
        self._write_log_entry(log_id, log_entry)
        
        logger.info(f"Logged query attempt: {log_id}")
        return log_id
    
    def log_query_result(
        self,
        log_id: str,
        success: bool,
        error: Optional[str],
        execution_time: float,
        row_count: int = 0
    ):
        """
        Update log entry with query execution results.
        
        Args:
            log_id: Log entry ID from log_query_attempt
            success: Whether execution succeeded
            error: Error message if failed
            execution_time: Execution time in seconds
            row_count: Number of rows returned/affected
        """
        if log_id not in self._log_cache:
            logger.warning(f"Log ID {log_id} not found in cache")
            # Try to load from file
            log_entry = self._read_log_entry(log_id)
            if log_entry:
                self._log_cache[log_id] = log_entry
            else:
                return
        
        log_entry = self._log_cache[log_id]
        log_entry['execution_success'] = success
        log_entry['error_message'] = error
        log_entry['execution_time_seconds'] = execution_time
        log_entry['rows_returned'] = row_count
        
        # Write updated entry
        self._write_log_entry(log_id, log_entry)
        
        logger.info(f"Updated query result for log: {log_id}")
    
    def log_dba_action(
        self,
        action: str,
        sql: str,
        approved: bool,
        approver: str
    ) -> str:
        """
        Log a DBA mode action with approval status.
        
        Args:
            action: Action type (APPROVED, REJECTED, EXECUTED)
            sql: SQL query
            approved: Whether action was approved
            approver: Session ID of approver
            
        Returns:
            Log entry ID
        """
        log_id = f"dba_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        log_entry = {
            "log_id": log_id,
            "timestamp": datetime.now().isoformat(),
            "log_type": "DBA_ACTION",
            "action": action,
            "sql": sql,
            "approved": approved,
            "approver_id": approver
        }
        
        # Write to file
        self._write_log_entry(log_id, log_entry)
        
        logger.info(f"Logged DBA action: {log_id} - {action}")
        return log_id
    
    def get_audit_trail(
        self,
        limit: int = 100,
        mode: Optional[str] = None,
        success_only: bool = False
    ) -> List[Dict]:
        """
        Retrieve audit logs with optional filtering.
        
        Args:
            limit: Maximum number of entries to return
            mode: Filter by mode (readonly or dba)
            success_only: Only return successful queries
            
        Returns:
            List of log entry dictionaries
        """
        audit_trail = []
        
        # Read all log files
        log_files = sorted(self.log_dir.glob("*.json"), reverse=True)
        
        for log_file in log_files[:limit]:
            try:
                with open(log_file, 'r') as f:
                    log_entry = json.load(f)
                
                # Apply filters
                if mode and log_entry.get('mode') != mode:
                    continue
                
                if success_only and not log_entry.get('execution_success'):
                    continue
                
                audit_trail.append(log_entry)
                
            except Exception as e:
                logger.error(f"Failed to read log file {log_file}: {e}")
        
        return audit_trail
    
    def _write_log_entry(self, log_id: str, log_entry: Dict):
        """
        Write log entry to file.
        
        Args:
            log_id: Log entry ID
            log_entry: Log entry dictionary
        """
        try:
            log_file = self.log_dir / f"{log_id}.json"
            with open(log_file, 'w') as f:
                json.dump(log_entry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write log entry {log_id}: {e}")
    
    def _read_log_entry(self, log_id: str) -> Optional[Dict]:
        """
        Read log entry from file.
        
        Args:
            log_id: Log entry ID
            
        Returns:
            Log entry dictionary or None if not found
        """
        try:
            log_file = self.log_dir / f"{log_id}.json"
            if log_file.exists():
                with open(log_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read log entry {log_id}: {e}")
        
        return None
    
    def get_statistics(self) -> Dict:
        """
        Get audit log statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_queries = 0
        successful_queries = 0
        failed_queries = 0
        dba_actions = 0
        
        log_files = list(self.log_dir.glob("*.json"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    log_entry = json.load(f)
                
                if log_entry.get('log_type') == 'DBA_ACTION':
                    dba_actions += 1
                else:
                    total_queries += 1
                    if log_entry.get('execution_success'):
                        successful_queries += 1
                    elif log_entry.get('execution_success') is False:
                        failed_queries += 1
                        
            except Exception:
                pass
        
        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": success_rate,
            "dba_actions": dba_actions
        }


# Global audit logger instance
audit_logger = AuditLogger()
