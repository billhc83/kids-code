from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Initialize the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
