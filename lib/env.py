import os

from dotenv import load_dotenv
from typing import Optional

load_dotenv()

APP_NAME: str = os.getenv("APP_NAME") or "Cyberflix Catalog"
APP_URL: str = os.getenv("APP_URL") or "0.0.0.0"
APP_PORT: int = int(os.getenv("APP_PORT") or 8000)
APP_LOG_LEVEL: str = os.getenv("APP_LOG_LEVEL") or "info"
APP_TIMEOUT: int = int(os.getenv("APP_TIMEOUT") or 600)

TMDB_API_KEY: str = os.getenv("TMDB_API_KEY")
MDBLIST_API_KEY: Optional[str] = os.getenv("MDBLIST_API_KEY") or None

TRAKT_CLIENT_ID: Optional[str] = os.getenv("TRAKT_CLIENT_ID") or None
TRAKT_CLIENT_SECRET: Optional[str] = os.getenv("TRAKT_CLIENT_SECRET") or None

SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL") or None
SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY") or None

SPONSOR: str = os.getenv("SPONSOR") or ""
SKIP_DB_UPDATE: bool = os.getenv("SKIP_DB_UPDATE") == "True"
