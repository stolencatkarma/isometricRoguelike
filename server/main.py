# Entry point for the Python server
# Uses websockets for multiplayer
import asyncio
import websockets
import uuid
import json

connected_clients = {}

async def handler(websocket, path):
    # Assign a unique ID to each client
    client_id = str(uuid.uuid4())
    connected_clients[client_id] = websocket
    print(f"Client {client_id} connected.")
    try:
        # Send a JSON welcome message
        welcome_msg = json.dumps({
            "type": "welcome",
            "sender": "server",
            "payload": {"client_id": client_id}
        })
        await websocket.send(welcome_msg)
        async for message in websocket:
            try:
                data = json.loads(message)
                # Attach sender ID if not present
                if "sender" not in data:
                    data["sender"] = client_id
                # Relay to all other clients
                relay_msg = json.dumps(data)
                for other_id, other_ws in connected_clients.items():
                    if other_id != client_id:
                        await other_ws.send(relay_msg)
            except json.JSONDecodeError:
                print(f"Invalid JSON from {client_id}: {message}")
    except websockets.ConnectionClosed:
        print(f"Client {client_id} disconnected.")
    finally:
        del connected_clients[client_id]

async def main():
    print("Server starting on ws://localhost:8765 ...")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
