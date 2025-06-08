import shopify
from .config import settings

def get_shopify_client():
    shopify.ShopifyResource.set_site(f"https://{settings.SHOPIFY_API_KEY}:{settings.SHOPIFY_API_SECRET_KEY}@{settings.SHOPIFY_STORE_DOMAIN}/admin/api/{settings.SHOPIFY_API_VERSION}")
    return shopify
