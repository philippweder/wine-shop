import os # Import os module
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Determine the path to the .env file, assuming it's in the 'backend' directory (parent of 'app')
# __file__ is the path to config.py (backend/app/config.py)
# os.path.dirname(__file__) is backend/app/
# os.path.join(os.path.dirname(__file__), "..") is backend/
# os.path.join(os.path.dirname(__file__), "..", ".env") is backend/.env
ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str

    # Made Shopify and Stripe keys optional
    SHOPIFY_API_KEY: Optional[str] = None
    SHOPIFY_API_SECRET_KEY: Optional[str] = None
    SHOPIFY_STORE_DOMAIN: Optional[str] = None
    SHOPIFY_API_VERSION: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, extra='ignore') # Allow and ignore extra fields

settings = Settings()
