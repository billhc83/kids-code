import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")