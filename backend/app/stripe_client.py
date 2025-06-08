import stripe
from .config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def get_stripe_client():
    return stripe
