import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

load_dotenv()  # loads .env file

OUTPUT_DIR = "outputs"

# Initialize client once
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY_GROQ"),
    base_url="https://api.groq.com/openai/v1"
)

client2 = OpenAI(
    api_key=os.environ["OPENAI_API_KEY_CHATGPT"],
    base_url="https://api.openai.com/v1"
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)