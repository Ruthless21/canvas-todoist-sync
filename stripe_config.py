import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Stripe API keys
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Stripe product and price IDs
STRIPE_PRODUCT_ID = os.environ.get('STRIPE_PRODUCT_ID', '')
STRIPE_MONTHLY_PRICE_ID = os.environ.get('STRIPE_MONTHLY_PRICE_ID', '')
STRIPE_YEARLY_PRICE_ID = os.environ.get('STRIPE_YEARLY_PRICE_ID', '')

# Domain for redirects
DOMAIN = os.environ.get('DOMAIN', 'http://localhost:5000')

# Price settings - subscription model with correct prices
MONTHLY_PRICE = 1.99  # Updated to match Stripe
YEARLY_PRICE = 18.99  # Updated to match Stripe
TRIAL_DAYS = 7 