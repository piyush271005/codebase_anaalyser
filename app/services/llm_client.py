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

def call_groq(prompt: str, model: str | None = None, api_key: str | None = None, max_tokens: int = 500) -> str:

    api_key = api_key or os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Groq API key not provided. Please provide an API key or set GROQ_API_KEY.")

    model = model or "groq/compound-mini"

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError(f"Groq returned empty response for model '{model}'.")
        return content

    except ImportError:
        import requests
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.3
                },
                timeout=30
            )
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Groq API error ({model}): {e}")
    except Exception as e:
        raise RuntimeError(f"Groq API error ({model}): {e}")


# ──────────────────────────────────────────────
# Provider 2: Gemini
# ──────────────────────────────────────────────
# Provider 2: Gemini
# ──────────────────────────────────────────────

def call_gemini(prompt: str, model: str | None = None, api_key: str | None = None, max_tokens: int = 500) -> str:

    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("[LLM] Error: 'google-generativeai' package not installed. Run: pip install google-generativeai")

    api_key = api_key or os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Gemini API key not provided. Please provide an API key or set GEMINI_API_KEY.")

    genai.configure(api_key=api_key)

    model_name = model or "gemini-3.5-flash-lite"

    try:
        gemini_model = genai.GenerativeModel(model_name)

        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens)
        )

        if not response.text:
            raise RuntimeError(f"Gemini returned empty response for model '{model_name}'.")

        return response.text

    except Exception as e:
        raise RuntimeError(f"Gemini API error ({model_name}): {e}")


# ──────────────────────────────────────────────
# Provider 3: OpenAI (GPT)
# ──────────────────────────────────────────────

def call_openai(prompt: str, model: str | None = None, api_key: str | None = None, max_tokens: int = 500) -> str:

    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("[LLM] Error: 'openai' package not installed. Run: pip install openai")

    api_key = api_key or os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OpenAI API key not provided. Please provide an API key or set OPENAI_API_KEY.")

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
            max_tokens=max_tokens,
            temperature=0.3,
        )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError(f"OpenAI returned empty response for model '{model}'.")

        return content

    except Exception as e:
        raise RuntimeError(f"OpenAI error ({model}): {e}")


# ──────────────────────────────────────────────
# Provider 4: Ollama (local)
# ──────────────────────────────────────────────

def call_ollama(prompt: str, model: str | None = None, api_key: str | None = None, max_tokens: int = 500) -> str:

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
                "options": {"num_predict": max_tokens},
            },
            timeout=120,
        )

        response.raise_for_status()

        resp_text = response.json().get("response")
        if not resp_text:
            raise RuntimeError(f"Ollama returned empty response for model '{model}' at {base_url}.")

        return resp_text

    except Exception as e:
        raise RuntimeError(f"Ollama error ({model} at {base_url}): {e}")


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

def call_llm(
    prompt: str,
    model: str | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    max_tokens: int = 500
) -> str:
    """
    Send a prompt to the configured LLM provider and return the text response.
    Raises exceptions directly on any failure without silent fallbacks.
    """

    provider_name = (provider or os.environ.get("LLM_PROVIDER", "groq")).strip().lower()

    provider_function = PROVIDERS.get(provider_name)

    if provider_function is None:
        raise ValueError(
            f"[LLM] Unknown provider: '{provider_name}'. "
            f"Available providers: {list(PROVIDERS.keys())}"
        )

    # Model priority: explicit parameter > env var (only if provider not explicitly specified) > provider default
    if not model and not provider:
        model = os.environ.get("LLM_MODEL")

    return provider_function(prompt, model=model, api_key=api_key, max_tokens=max_tokens)
