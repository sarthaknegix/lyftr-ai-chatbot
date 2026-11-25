
import os
from dotenv import load_dotenv

# Load settings from the project's .env file
load_dotenv()

# Read API keys in order: key_1, key_2, etc.
LLM_API_KEYS = [
    key.strip()
    for key in os.getenv("LLM_API_KEYS", "").split(",")
    if key.strip() and not key.strip().startswith("YOUR_")
]

# Model configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gemini/gemini-2.5-flash")

# Application configuration
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000"
    ).split(",")
    if origin.strip()
]

ENABLE_FAILURE_SIMULATION = (
    os.getenv("ENABLE_FAILURE_SIMULATION", "false").lower() == "true"
)
