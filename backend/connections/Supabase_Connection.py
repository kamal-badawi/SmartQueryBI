# Import necessary types and functions
from supabase import create_client, Client
from decouple import config

def create_supabase_connection() -> Client:
    """
    Establishes a secure connection to a Supabase PostgreSQL database.

    Overview
    --------
    This function loads the required credentials (Supabase URL and API key) from environment variables,
    typically stored in a .env file, using the `decouple` library. It then initializes a Supabase client 
    configured with these credentials and returns it for executing queries or RPC calls.

    Workflow
    --------
    1. Load configuration:
       - Retrieves the Supabase project URL from the environment variable `SUPABASE_URL`.
       - Retrieves the Supabase anon/service key from the environment variable `SUPABASE_KEY`.
    2. Initialize Supabase client:
       - Creates a client object using the loaded URL and key.
    3. Return the client:
       - The returned `Client` object can be used for database queries, inserts, updates, or RPC calls.

    Returns
    -------
    Client
        An initialized Supabase Client object ready for executing queries or RPCs.

    Security Considerations
    -----------------------
    - Credentials should be stored securely and not hardcoded in the source code.
    - Use `.env` files or other secure secret management systems.
    """
    # Load Supabase project URL from environment variables
    supabase_url = config("SUPABASE_URL")
    # Load Supabase API key from environment variables
    supabase_key = config("SUPABASE_KEY")

    # Initialize the Supabase client using the loaded credentials
    supabase = create_client(supabase_url, supabase_key)

    # Return the configured Supabase client
    return supabase
