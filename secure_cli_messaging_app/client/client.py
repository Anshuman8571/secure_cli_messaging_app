# client/client.py
import os
import asyncio
import websockets
import json
import aioconsole  # For non-blocking input
from crypto_utils import (
    generate_keys,
    serialize_private_key,
    serialize_public_key,
    load_private_key,
    load_public_key,
    encrypt_message,
    decrypt_message
)

SERVER_WS_URL = "ws://3.109.58.129:8765"
PRIVATE_KEY_FILE = "private_key.pem"
PUBLIC_KEY_FILE = "public_key.pem"

# CHANGE: Added a shared dictionary to act as a cache for incoming public keys.
# This is the key to solving the race condition.
PUBLIC_KEY_CACHE = {}

async def listen_for_messages(websocket, private_key):
    """Listens for all incoming messages, decrypts, and prints or caches them."""
    async for message in websocket:
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'message':
                sender = data.get('from')
                encrypted_msg = data.get('message')
                decrypted_msg = decrypt_message(encrypted_msg, private_key)
                # Using aioconsole.aprint to safely print without messing up user input
                await aioconsole.aprint(f"\n[Message from {sender}]: {decrypted_msg}")
            
            # CHANGE: The listener now handles 'key_response' messages.
            elif msg_type == 'key_response':
                # Store the received public key in our shared cache.
                PUBLIC_KEY_CACHE[data.get('username')] = data.get('public_key')

            elif msg_type == 'error':
                await aioconsole.aprint(f"\n[Server Error]: {data.get('message')}")
        except json.JSONDecodeError:
            await aioconsole.aprint(f"\n[Error]: Received malformed data from server.")
        except Exception as e:
            await aioconsole.aprint(f"\n[Error]: Could not process message: {e}")


async def handle_user_input(websocket, username):
    """Handles user input for sending messages."""
    while True:
        recipient = await aioconsole.ainput("Enter recipient's username (or 'exit'): ")
        if recipient.lower() == 'exit':
            break

        # CHANGE: Logic to request and wait for a key from the cache.
        # Clear any old key for the recipient to ensure we get a fresh one.
        PUBLIC_KEY_CACHE[recipient] = None
        
        # Request recipient's public key from the server
        await websocket.send(json.dumps({'type': 'get_key', 'username': recipient}))
        
        # Wait for the listener task to populate the cache.
        # We'll wait for up to 5 seconds.
        try:
            for _ in range(50): # 50 * 0.1s = 5 seconds timeout
                if PUBLIC_KEY_CACHE.get(recipient) is not None:
                    break
                await asyncio.sleep(0.1)
            
            key_pem = PUBLIC_KEY_CACHE.get(recipient)
            if not key_pem:
                print(f"Could not get public key for '{recipient}'. User may not exist or is offline.")
                continue

        except Exception:
            print(f"An error occurred while fetching the public key for '{recipient}'.")
            continue
        
        recipient_public_key = load_public_key(key_pem)
        print(f"--- Starting chat with {recipient}. Type '/back' to choose someone else. ---")

        while True:
            msg_text = await aioconsole.ainput(f"> ")
            if msg_text.lower() == '/back':
                break
            
            encrypted_msg = encrypt_message(msg_text, recipient_public_key)
            payload = {
                'type': 'message',
                'from': username,
                'to': recipient,
                'message': encrypted_msg
            }
            await websocket.send(json.dumps(payload))

async def main():
    """Main function to run the client."""
    # Step 1: Key Management
    if not os.path.exists(PRIVATE_KEY_FILE):
        print("No keys found. Generating a new key pair...")
        private_key, public_key = generate_keys()
        with open(PRIVATE_KEY_FILE, "w") as f:
            f.write(serialize_private_key(private_key))
        with open(PUBLIC_KEY_FILE, "w") as f:
            f.write(serialize_public_key(public_key))
        print(f"Keys saved to {PRIVATE_KEY_FILE} and {PUBLIC_KEY_FILE}.")
    else:
        print("Loading existing keys.")
    
    with open(PRIVATE_KEY_FILE, "r") as f:
        private_key = load_private_key(f.read())
    with open(PUBLIC_KEY_FILE, "r") as f:
        public_key_pem = f.read()

    # Step 2: User Setup and Connection
    username = input("Enter your username: ")

    try:
        async with websockets.connect(SERVER_WS_URL) as websocket:
            # Step 3: Registration
            print(f"Registering as '{username}'...")
            registration_payload = {
                'type': 'register',
                'username': username,
                'public_key': public_key_pem
            }
            await websocket.send(json.dumps(registration_payload))
            response = json.loads(await websocket.recv())
            
            if response.get('status') != 'Registration successful':
                print(f"Registration failed: {response.get('error', 'Unknown error')}")
                return
            
            print("Successfully connected and registered.")

            # Step 4: Run listener and input handler concurrently
            listener_task = asyncio.create_task(listen_for_messages(websocket, private_key))
            # CHANGE: Removed private_key from handle_user_input as it's no longer needed there.
            input_task = asyncio.create_task(handle_user_input(websocket, username))
            
            await asyncio.gather(listener_task, input_task)

    except ConnectionRefusedError:
        print("Connection failed. Is the server running?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClient shut down.")