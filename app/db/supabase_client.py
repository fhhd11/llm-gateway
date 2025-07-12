# Handled in dependencies, but if needed:
from supabase import create_client
from app.config import settings

def get_client():
    return create_client(settings.supabase_url, settings.supabase_key)