import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)

# In-memory storage for simplicity.
# A real application would use a database.
USERS = {}  # Stores {'username': 'public_key_pem'}
CONNECTED_CLIENTS = {}  # Stores {'username': websocket_connection}

async def handler(websocket):
    """
    Handles a single client connection, registration, and message relaying.
    """
    username = None
    try:
        # The first message from the client must be for registration.
        message = await websocket.recv()
        data = json.loads(message)
        
        if data.get('type') == 'register':
            username = data.get('username')
            public_key = data.get('public_key')
            
            if not username or not public_key:
                await websocket.send(json.dumps({
                    'error': 'Username and public key required for registration.'
                }))
                return
            
            USERS[username] = public_key
            CONNECTED_CLIENTS[username] = websocket
            logging.info(f"User '{username}' registered and connected.")
            # FIX #1: Removed the period from "successful"
            await websocket.send(json.dumps({'status': 'Registration successful'}))
        else:
            await websocket.send(json.dumps({'error': 'Client must register first.'}))
            return

        # Main loop to listen for messages from this client
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'get_key':
                target_user = data.get('username')
                public_key = USERS.get(target_user)
                if public_key:
                    # FIX #2: Changed 'key response' to 'key_response'
                    response = {'type': 'key_response', 'username': target_user, 'public_key': public_key}
                else:
                    # FIX #3: Made the error message a proper f-string
                    response = {'type': 'error', 'message': f'User "{target_user}" not found.'}
                await websocket.send(json.dumps(response))
            
            elif msg_type == 'message':
                recipient = data.get('to')
                recipient_ws = CONNECTED_CLIENTS.get(recipient)

                if recipient_ws:
                    logging.info(f"Relaying message from '{username}' to '{recipient}'")
                    await recipient_ws.send(message)
                else:
                    logging.warning(f"User '{recipient}' is not online. Message not delivered.")
                    # FIX #4: Corrected the typo in "Recipient"
                    await websocket.send(json.dumps({'type': 'error', 'message': f"Recipient '{recipient}' is offline."}))

    except websockets.exceptions.ConnectionClosed as e:
        logging.info(f"Connection closed for user: {username}. Reason: {e}")
    except Exception as e:
        logging.error(f"An error occurred with user {username}: {e}") # (Corrected minor typo 'occured' to 'occurred')
    finally:
        # Cleanup on disconnect
        if username and username in CONNECTED_CLIENTS:
            del CONNECTED_CLIENTS[username]
            logging.info(f"User '{username}' disconnected.")

async def main():
    host = '0.0.0.0'
    port = 8765
    logging.info(f"Starting WebSocket server on ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())