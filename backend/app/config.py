from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SHOPIFY_API_KEY: str
    SHOPIFY_API_SECRET_KEY: str
    SHOPIFY_STORE_DOMAIN: str
    SHOPIFY_API_VERSION: str
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
