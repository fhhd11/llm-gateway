# Handled in dependencies, but if needed:
from supabase import create_client
from app.config import get_settings

settings = get_settings()

def get_client():
    return create_client(settings.supabase_url, settings.supabase_key)