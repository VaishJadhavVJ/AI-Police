import os

from langchain_openai import ChatOpenAI


DEFAULT_BASE_URL = "https://api.z.ai/api/paas/v4"
DEFAULT_MODEL = "glm-5.3-flash"


def build_model():
    return ChatOpenAI(
        model=DEFAULT_MODEL,
        api_key=os.environ["ZAI_API_KEY"],
        base_url=DEFAULT_BASE_URL,
        temperature=0,
        timeout=600,
        max_retries=0,
    )