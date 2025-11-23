"""
DBA mode authentication and session management.
"""

import logging
import hmac
from datetime import datetime, timedelta
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)


class DBAAuth:
    """Handles DBA mode authentication and session management."""
    
    @staticmethod
    def authenticate(password: str, session_state: dict) -> bool:
        """
        Authenticate user for DBA mode access.
        
        Args:
            password: Password to verify
            session_state: Streamlit session state dictionary
            
        Returns:
            True if authentication successful, False otherwise
        """
        correct_password = settings.security.dba_password
        
        # Timing-attack resistant comparison
        is_valid = hmac.compare_digest(password, correct_password)
        
        if is_valid:
            session_state['dba_authenticated'] = True
            session_state['dba_login_time'] = datetime.now()
            logger.info("DBA authentication successful")
            return True
        else:
            logger.warning("DBA authentication failed - invalid password")
            return False
    
    @staticmethod
    def is_authenticated(session_state: dict) -> bool:
        """
        Check if current session is authenticated for DBA mode.
        
        Args:
            session_state: Streamlit session state dictionary
            
        Returns:
            True if authenticated and session valid, False otherwise
        """
        if not session_state.get('dba_authenticated', False):
            return False
        
        # Check session timeout
        login_time = session_state.get('dba_login_time')
        if login_time:
            elapsed = datetime.now() - login_time
            timeout_hours = settings.security.session_timeout_hours
            
            if elapsed > timedelta(hours=timeout_hours):
                logger.info("DBA session expired")
                DBAAuth.logout(session_state)
                return False
        
        return True
    
    @staticmethod
    def logout(session_state: dict):
        """
        Logout from DBA mode and clear authentication.
        
        Args:
            session_state: Streamlit session state dictionary
        """
        session_state['dba_authenticated'] = False
        session_state['dba_login_time'] = None
        session_state['current_mode'] = 'readonly'
        
        # Clear any pending approvals
        if 'pending_approval' in session_state:
            session_state['pending_approval'] = None
        
        logger.info("DBA session logged out")
    
    @staticmethod
    def get_session_info(session_state: dict) -> Optional[dict]:
        """
        Get information about current DBA session.
        
        Args:
            session_state: Streamlit session state dictionary
            
        Returns:
            Dictionary with session info or None if not authenticated
        """
        if not DBAAuth.is_authenticated(session_state):
            return None
        
        login_time = session_state.get('dba_login_time')
        if not login_time:
            return None
        
        elapsed = datetime.now() - login_time
        timeout_hours = settings.security.session_timeout_hours
        remaining = timedelta(hours=timeout_hours) - elapsed
        
        return {
            'login_time': login_time,
            'elapsed_time': elapsed,
            'remaining_time': remaining,
            'timeout_hours': timeout_hours
        }
    
    @staticmethod
    def refresh_session(session_state: dict) -> bool:
        """
        Refresh DBA session timeout.
        
        Args:
            session_state: Streamlit session state dictionary
            
        Returns:
            True if session refreshed, False if not authenticated
        """
        if not session_state.get('dba_authenticated', False):
            return False
        
        session_state['dba_login_time'] = datetime.now()
        logger.info("DBA session refreshed")
        return True


# Global auth instance (for convenience)
dba_auth = DBAAuth()
