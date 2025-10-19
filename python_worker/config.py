import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # loads .env file

OUTPUT_DIR = "outputs"

# Initialize client once
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)