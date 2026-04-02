import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    # Create the client only when config is present.
    # This avoids crashing the app on import during deployments where env vars
    # are not set (e.g. missing Render service environment variables).
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
