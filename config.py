import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

STRIPE_SECRET_KEY      = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID        = os.getenv("STRIPE_PRICE_ID")

# See docs/superpowers/specs/2026-07-12-referral-codes-design.md — both are
# deliberately single config constants, not admin-configurable per-code.
REFERRAL_REWARD_MONTHS      = 1  # months credited to BOTH sides of a parent_referral redemption
REFERRER_ANNUAL_CAP_MONTHS  = 2  # max months a referrer can accumulate per rolling 12-month year