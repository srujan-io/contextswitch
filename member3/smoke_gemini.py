"""Manual plumbing check: one Gemini response and one local sentence vector."""

from __future__ import annotations

import sys

from matcher import FastEmbedEncoder
from settings import create_gemini_client, load_settings


def main() -> int:
    client = None
    try:
        settings = load_settings()
    except Exception as exc:
        print(f"Configuration load failed ({type(exc).__name__})", file=sys.stderr)
        return 1
    try:
        client = create_gemini_client(settings)
    except RuntimeError as exc:
        safe_messages = {
            "GEMINI_API_KEY is not configured in member3/.env",
            "google-genai is not installed; install member3/requirements.txt",
        }
        message = str(exc)
        if message in safe_messages:
            print(f"Gemini SDK setup failed: {message}", file=sys.stderr)
        else:
            print(f"Gemini SDK setup failed ({type(exc).__name__})", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Gemini SDK setup failed ({type(exc).__name__})", file=sys.stderr)
        return 1
    try:
        response = client.models.generate_content(
            model=settings.model,
            contents="Reply with exactly: GEMINI_OK",
            config={"temperature": 0, "max_output_tokens": 16},
        )
        print("Gemini smoke response:", (getattr(response, "text", "") or "").strip())
    except Exception as exc:
        # SDK/network exceptions may contain request details; never print them.
        print(f"Gemini request failed ({type(exc).__name__}); check network, key access, and model availability.", file=sys.stderr)
        return 1
    try:
        encoder = FastEmbedEncoder(settings.embedding_model)
        vector = encoder.encode(["Find the USB connector"])[0]
        print("Sentence embedding dimension:", len(vector))
        return 0
    except RuntimeError as exc:
        print(f"Embedding setup failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Embedding/model download failed ({type(exc).__name__}); check network and FastEmbed model access.", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
