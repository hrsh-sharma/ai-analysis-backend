from openai import OpenAI
from core.config import settings

# Set timeout at client level — applies to every call
ai_client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    timeout=30.0,
    max_retries=0,
)

AI_MODEL = "llama-3.3-70b-versatile"
