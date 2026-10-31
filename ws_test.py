import asyncio
import json
import websockets

URL = "ws://127.0.0.1:8000/ws/cv"


async def main():
    print("[CLIENT] Connecting to CV server...")

    async with websockets.connect(URL) as ws:
        print("[CLIENT] Connected successfully!")
        print("[CLIENT] Move your hand or head.\n")

        async for message in ws:
            event = json.loads(message)

            source = event.get("source")
            action = event.get("action")
            params = event.get("parameters", {})

            # Avoid flooding terminal with cursor updates.
            if action == "CURSOR_MOVE":
                print(
                    f"\r[HAND] CURSOR x={params.get('x')} "
                    f"y={params.get('y')}    ",
                    end="",
                    flush=True,
                )
            else:
                print(f"\n[{source}] {action} {params}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[CLIENT] Disconnected")
    except OSError as exc:
        print(f"\n[ERROR] Cannot connect: {exc}")