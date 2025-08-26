import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

try:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
except Exception:
    # In dev environments the Application Default credentials may not be set.
    # The app can still be imported; calls to verify_id_token will raise until
    # proper credentials are configured.
    pass

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth credentials")
