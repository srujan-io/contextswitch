"""Manual plumbing check: one Gemini response and one local sentence vector."""

from __future__ import annotations

import sys

from matcher import FastEmbedEncoder
from settings import create_gemini_client, load_settings


def main() -> int:
    client = None
    try:
        settings = load_settings()
        client = create_gemini_client(settings)
        response = client.models.generate_content(
            model=settings.model,
            contents="Reply with exactly: GEMINI_OK",
            config={"temperature": 0, "max_output_tokens": 16},
        )
        print("Gemini smoke response:", (getattr(response, "text", "") or "").strip())
        encoder = FastEmbedEncoder(settings.embedding_model)
        vector = encoder.encode(["Find the USB connector"])[0]
        print("Sentence embedding dimension:", len(vector))
        return 0
    except Exception as exc:
        # Do not print exception text: some SDK/network exceptions can include
        # request URLs or headers. A type label is enough for this safe smoke.
        print(f"Smoke check failed ({type(exc).__name__})", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
