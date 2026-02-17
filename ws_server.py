import asyncio
import websockets
import json

async def handler(websocket):
    print("Phone connected!")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(data)
            except json.JSONDecodeError:
                print("Invalid JSON received:", message)
    except websockets.ConnectionClosed:
        print("Connection closed by phone")

async def main():
    server = await websockets.serve(
        handler,
        host="0.0.0.0",
        port=8765
    )
    print("WebSocket running on 0.0.0.0:8765")
    await server.wait_closed()

asyncio.run(main())
