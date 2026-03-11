"""
Database connection and session management for NoteEase.
Uses SQLAlchemy with PostgreSQL.
"""
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load .env only for missing variables (don't override already-set env vars)
_backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_backend_root, '.env'), override=False)


def _build_database_url():
    """
    Build a fully authenticated database URL from environment variables.

    The POSTGRES_URL env var may be:
    - A full URL with credentials: postgresql://user:pass@host:port/db
    - A URL without credentials:   postgresql://host:port/db
    - Just a hostname:             localhost

    Returns:
        str: PostgreSQL connection URL with credentials
    """
    postgres_url = os.getenv('POSTGRES_URL', '')
    user = os.getenv('POSTGRES_USER', 'appuser')
    password = os.getenv('POSTGRES_PASSWORD', 'dbuser123')
    db_name = os.getenv('POSTGRES_DB', 'myapp')
    port_str = os.getenv('POSTGRES_PORT', '5000')

    try:
        port = int(port_str) if port_str and port_str.strip() else 5000
    except (ValueError, TypeError):
        port = 5000

    # If POSTGRES_URL is a full connection URL
    if postgres_url.startswith('postgresql://') or postgres_url.startswith('postgres://'):
        # Check if URL already contains credentials (user:pass@)
        # Pattern: scheme://user:pass@host or scheme://user@host
        has_credentials = bool(re.search(r'://[^/@]+@', postgres_url))
        if has_credentials:
            return postgres_url

        # Inject credentials into the URL
        # Replace scheme:// with scheme://user:pass@
        scheme_end = postgres_url.index('://') + 3
        scheme = postgres_url[:scheme_end]
        rest = postgres_url[scheme_end:]
        return f'{scheme}{user}:{password}@{rest}'

    # Build from individual components (POSTGRES_URL is just a hostname)
    host = postgres_url if postgres_url else 'localhost'
    return f'postgresql://{user}:{password}@{host}:{port}/{db_name}'


DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency that provides a database session.
    Yields a database session and ensures it is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    from .models import Base  # noqa: F401 - imported to register models
    Base.metadata.create_all(bind=engine)
