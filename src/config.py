"""
Configuration module.
Loads secrets from environment variables (.env file).
Never hardcode API keys in the source code.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Tokens ---
SPTRANS_TOKEN = os.getenv("SPTRANS_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Database ---
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_SERVER = os.getenv("DB_SERVER", "localhost\\SQLEXPRESS")
DB_NAME = os.getenv("DB_NAME", "ColetaTransporte")
DB_TRUSTED = os.getenv("DB_TRUSTED", "yes")

def get_connection_string() -> str:
    """Returns the ODBC connection string."""
    return (
        f"Driver={{{DB_DRIVER}}};"
        f"Server={DB_SERVER};"
        f"Database={DB_NAME};"
        f"Trusted_Connection={DB_TRUSTED};"
    )

# --- Geographic bounds (São Paulo Capital) ---
SP_LAT_MIN, SP_LAT_MAX = -24.02, -23.35
SP_LON_MIN, SP_LON_MAX = -46.95, -46.30

# --- Analysis defaults ---
DIST_MAX_KM = 1.5
MAX_CONNECTIONS = 15
