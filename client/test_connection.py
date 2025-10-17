# test_connection.py
print("--- Script Starting ---")
print("Importing asyncio...")
import asyncio
print("Importing websockets...")
import websockets

# Please double-check this URL is still correct from your localtunnel
TEST_URL = "wss://strong-years-spend.loca.lt"

async def test():
    print(f"Attempting to connect to {TEST_URL}...")
    try:
        # Add a timeout to the connection attempt
        async with asyncio.timeout(10):
            async with websockets.connect(TEST_URL) as websocket:
                print("\nSUCCESS: WebSocket connection established!")
                response = await websocket.recv()
                print(f"Received response from server: {response}")
    except TimeoutError:
        print("\n--- CONNECTION FAILED ---")
        print("The connection timed out after 10 seconds.")
        print("This means a firewall or network issue is blocking the connection.")
    except Exception as e:
        print("\n--- CONNECTION FAILED ---")
        print(f"The connection failed with the following error: {e}")

# FIX: Corrected the typo from _name_ to __name__
if __name__ == "__main__":
    asyncio.run(test())