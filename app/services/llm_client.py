"""
LLM Client — Multi-Provider Support

Supports: Groq, Gemini, OpenAI (GPT), Ollama

Configuration via environment variables:
    LLM_PROVIDER   = "groq" | "gemini" | "openai" | "ollama"
    GROQ_API_KEY   = "gsk_..."
    GEMINI_API_KEY  = "AI..."
    OPENAI_API_KEY  = "sk-..."
    OLLAMA_BASE_URL = "http://localhost:11434"  (optional, this is default)
    LLM_MODEL      = model name (optional, each provider has a default)
"""

import os


# ──────────────────────────────────────────────
# Provider 1: Groq
# ──────────────────────────────────────────────

def call_groq(prompt: str, model: str | None = None) -> str | None:

    try:
        from groq import Groq
    except ImportError:
        print("[LLM] Error: 'groq' package not installed. Run: pip install groq")
        return None

    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        print("[LLM] Error: GROQ_API_KEY not set")
        return None

    client = Groq(api_key=api_key)

    model = model or "llama-3.1-8b-instant"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"[LLM] Groq error: {e}")
        return None


# ──────────────────────────────────────────────
# Provider 2: Gemini
# ──────────────────────────────────────────────

def call_gemini(prompt: str, model: str | None = None) -> str | None:

    try:
        import google.generativeai as genai
    except ImportError:
        print("[LLM] Error: 'google-generativeai' package not installed. Run: pip install google-generativeai")
        return None

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("[LLM] Error: GEMINI_API_KEY not set")
        return None

    genai.configure(api_key=api_key)

    model_name = model or "gemini-2.0-flash"

    try:
        gemini_model = genai.GenerativeModel(model_name)

        response = gemini_model.generate_content(prompt)

        return response.text

    except Exception as e:
        print(f"[LLM] Gemini error: {e}")
        return None


# ──────────────────────────────────────────────
# Provider 3: OpenAI (GPT)
# ──────────────────────────────────────────────

def call_openai(prompt: str, model: str | None = None) -> str | None:

    try:
        from openai import OpenAI
    except ImportError:
        print("[LLM] Error: 'openai' package not installed. Run: pip install openai")
        return None

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("[LLM] Error: OPENAI_API_KEY not set")
        return None

    client = OpenAI(api_key=api_key)

    model = model or "gpt-4o-mini"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"[LLM] OpenAI error: {e}")
        return None


# ──────────────────────────────────────────────
# Provider 4: Ollama (local)
# ──────────────────────────────────────────────

def call_ollama(prompt: str, model: str | None = None) -> str | None:

    import requests

    base_url = os.environ.get(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    )

    model = model or "llama3.2"

    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        return response.json().get("response")

    except Exception as e:
        print(f"[LLM] Ollama error: {e}")
        return None


# ──────────────────────────────────────────────
# Provider Registry
# ──────────────────────────────────────────────

PROVIDERS = {
    "groq": call_groq,
    "gemini": call_gemini,
    "openai": call_openai,
    "ollama": call_ollama,
}


# ──────────────────────────────────────────────
# Main Function — call_llm()
# ──────────────────────────────────────────────

def call_llm(prompt: str, model: str | None = None) -> str | None:
    """
    Send a prompt to the configured LLM provider
    and return the text response.

    Provider is selected via the LLM_PROVIDER
    environment variable.

    Model can be overridden via the model parameter
    or the LLM_MODEL environment variable.

    Returns None if the API call fails.
    """

    provider_name = os.environ.get("LLM_PROVIDER", "groq")

    provider_function = PROVIDERS.get(provider_name)

    if provider_function is None:
        print(
            f"[LLM] Unknown provider: {provider_name}. "
            f"Available: {list(PROVIDERS.keys())}"
        )
        return None

    # Model priority: parameter > env var > provider default
    model = model or os.environ.get("LLM_MODEL")

    return provider_function(prompt, model)
