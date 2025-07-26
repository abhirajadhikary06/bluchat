import asyncio
import json
import emoji
from datetime import datetime
from bleak import BleakClient
from storage import ChatStorage

SERVICE_UUID = "12345678-1234-5678-1234-567812345678"
CHAR_UUID = "87654321-4321-6789-4321-678943210987"

class BluetoothChatClient:
    def __init__(self, storage):
        self.storage = storage
        self.nickname = ""
        self.client = None
        self.is_running = False
        self.device_id = None

    async def handle_notification(self, sender, data):
        try:
            packet = json.loads(data.decode())
            if packet["type"] == "message":
                message = emoji.emojize(packet["content"], language="alias")
                msg = self.add_message("Server", message, False)
                print(f"\r{msg['sender']} ({msg['timestamp']}): {msg['content']}")
                print("Enter message: ", end="", flush=True)
            elif packet["type"] == "typing":
                print("\rServer is typing..." if packet["content"] else "\r" + " " * 20, end="", flush=True)
        except json.JSONDecodeError:
            pass

    def add_message(self, sender, content, is_self):
        timestamp = datetime.now().strftime("%I:%M %p")
        message = {"sender": sender, "content": content, "timestamp": timestamp, "is_self": is_self}
        self.storage.save_message(self.device_id, message)
        return message

    async def run(self, server_address):
        self.nickname = input("Enter your nickname: ").strip()
        if not self.nickname:
            print("Nickname cannot be empty!")
            return
        self.storage.save_nickname(self.nickname)
        self.device_id = server_address

        print(f"Connecting to server {server_address}...")
        try:
            async with BleakClient(server_address) as self.client:
                self.is_running = True
                print(f"Connected to server {server_address}")
                await self.client.start_notify(CHAR_UUID, self.handle_notification)

                # Load previous messages
                messages = self.storage.load_messages(self.device_id)
                for msg in messages:
                    print(f"{msg['sender']} ({msg['timestamp']}): {msg['content']}")

                while self.is_running:
                    message = input("Enter message (or 'quit' to stop): ").strip()
                    if message.lower() == "quit":
                        break
                    if message:
                        message = emoji.emojize(message, language="alias")
                        await self.client.write_characteristic(
                            CHAR_UUID,
                            json.dumps({"type": "message", "content": message}).encode()
                        )
                        msg = self.add_message(self.nickname, message, True)
                        print(f"{msg['sender']} ({msg['timestamp']}): {msg['content']}")
                    # Send typing status
                    await self.client.write_characteristic(
                        CHAR_UUID,
                        json.dumps({"type": "typing", "content": bool(message)}).encode()
                    )
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Client error: {str(e)}")
        finally:
            self.is_running = False

async def main():
    storage = ChatStorage("chat_history.json")
    server_address = input("Enter server MAC address: ").strip()
    client = BluetoothChatClient(storage)
    await client.run(server_address)

if __name__ == "__main__":
    asyncio.run(main())