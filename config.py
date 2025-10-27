# config.py
import os
import sys
from dotenv import load_dotenv

load_dotenv()

class Config:
    NOTION_API_KEY = os.environ.get('NOTION_API_KEY')
    TRANSACTIONS_DB_ID = os.environ.get('NOTION_TRANSACTIONS_DB_ID')
    ACCOUNTS_DB_ID = os.environ.get('NOTION_ACCOUNTS_DB_ID')
    CATEGORIES_DB_ID = os.environ.get('NOTION_CATEGORIES_DB_ID')
    PILLARS_DB_ID = os.environ.get('NOTION_PILLARS_DB_ID')
    INVESTMENT_TRANSACTIONS_DB_ID = os.environ.get('NOTION_INVESTMENT_TRANSACTIONS_DB_ID')
    HOLDINGS_DB_ID = os.environ.get('NOTION_HOLDINGS_DB_ID')

    # Here is the SSL toggle you requested
    SSL_VERIFY = os.environ.get('SSL_VERIFY', 'true').lower() != 'false'

    # Check for the most critical key
    if not NOTION_API_KEY:
        print("CRITICAL ERROR: NOTION_API_KEY is not set.", file=sys.stderr)
        raise ValueError("CRITICAL ERROR: NOTION_API_KEY is not set.")