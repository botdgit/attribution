"""Firebase authentication utilities."""
import logging
from typing import Optional
import firebase_admin
from firebase_admin import auth, credentials


logger = logging.getLogger(__name__)


class FirebaseAuth:
    """Firebase authentication handler."""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id
        self._app = None
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialize Firebase admin SDK."""
        try:
            if not firebase_admin._apps:
                # Use default credentials if no explicit config
                cred = credentials.ApplicationDefault()
                self._app = firebase_admin.initialize_app(cred, {
                    'projectId': self.project_id
                })
            else:
                self._app = firebase_admin.get_app()
        except Exception as e:
            logger.warning(f"Firebase initialization failed: {e}")
            self._app = None
    
    def verify_token(self, id_token: str) -> Optional[dict]:
        """Verify Firebase ID token and return user info."""
        if not self._app:
            logger.error("Firebase not initialized")
            return None
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            return {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False)
            }
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def get_user(self, uid: str) -> Optional[dict]:
        """Get user information by UID."""
        if not self._app:
            return None
        
        try:
            user_record = auth.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name
            }
        except Exception as e:
            logger.error(f"Failed to get user {uid}: {e}")
            return None


# Global auth instance
firebase_auth = FirebaseAuth()


def verify_firebase_token(token: str) -> Optional[dict]:
    """Convenience function to verify Firebase token."""
    return firebase_auth.verify_token(token)