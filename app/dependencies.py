from fastapi import Depends, HTTPException, Header
from jose import JWTError, jwt
from supabase import create_client
from app.config import settings

def get_supabase_client():
    return create_client(settings.supabase_url, settings.supabase_key)

async def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["RS256" if "supabase" in settings.jwt_secret else "HS256"])  # Adjust algorithm if needed
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")