import os

from langchain_openai import ChatOpenAI


DEFAULT_BASE_URL = "https://api.z.ai/api/paas/v4"
DEFAULT_MODEL = "glm-5.3-flash"


def build_model():
    api_key = os.environ["ZAI_API_KEY"]
    base_url = os.environ.get("ZAI_BASE_URL", DEFAULT_BASE_URL)
    model = os.environ.get("ZAI_MODEL", DEFAULT_MODEL)
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )