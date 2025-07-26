import asyncio
import json
import emoji
from datetime import datetime
from bleak import BleakGATTCharacteristic, BleakScanner, BleakClient
from bleak.backends.service import BleakGATTService
from bleak import BleakServerGATT, advertise
from storage import ChatStorage

SERVICE_UUID = "12345678-1234-5678-1234-567812345678"
CHAR_UUID = "87654321-4321-6789-4321-678943210987"

class BluetoothChatServer:
    def __init__(self, storage):
        self.storage = storage
        self.nickname = ""
        self.connected_client = None
        self.is_running = False
        self.device_id = None

    async def handle_notification(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        try:
            packet = json.loads(data.decode())
            if packet["type"] == "message":
                message = emoji.emojize(packet["content"], language="alias")
                msg = self.add_message("Client", message, False)
                print(f"{msg['sender']} ({msg['timestamp']}): {msg['content']}")
            elif packet["type"] == "typing":
                print("\rClient is typing..." if packet["content"] else "\r" + " " * 20, end="")
        except json.JSONDecodeError:
            pass

    def add_message(self, sender, content, is_self):
        timestamp = datetime.now().strftime("%I:%M %p")
        message = {"sender": sender, "content": content, "timestamp": timestamp, "is_self": is_self}
        self.storage.save_message(self.device_id, message)
        return message

    async def run(self):
        self.nickname = input("Enter your nickname: ").strip()
        if not self.nickname:
            print("Nickname cannot be empty!")
            return
        self.storage.save_nickname(self.nickname)
        print("Starting server...")

        async def on_connect(client: BleakClient):
            self.connected_client = client
            self.device_id = client.address
            self.is_running = True
            print(f"Connected to client {self.device_id}")
            messages = self.storage.load_messages(self.device_id)
            for msg in messages:
                print(f"{msg['sender']} ({msg['timestamp']}): {msg['content']}")

        async def on_disconnect(client: BleakClient):
            self.is_running = False
            self.connected_client = None
            print("Client disconnected")

        # Define GATT service and characteristic
        service = BleakGATTService(SERVICE_UUID)
        characteristic = BleakGATTCharacteristic(
            CHAR_UUID,
            ["read", "write", "notify"],
            "Chat Characteristic"
        )
        characteristic.add_callback(self.handle_notification)
        service.add_characteristic(characteristic)

        # Start advertising
        try:
            await advertise(
                services=[service],
                on_connect=on_connect,
                on_disconnect=on_disconnect,
                name=f"ChatServer_{self.nickname}"
            )
            while True:
                if self.is_running and self.connected_client:
                    message = input("\rEnter message (or 'quit' to stop): ").strip()
                    if message.lower() == "quit":
                        break
                    if message:
                        message = emoji.emojize(message, language="alias")
                        await self.connected_client.write_characteristic(
                            CHAR_UUID,
                            json.dumps({"type": "message", "content": message}).encode()
                        )
                        msg = self.add_message(self.nickname, message, True)
                        print(f"{msg['sender']} ({msg['timestamp']}): {msg['content']}")
                    # Send typing status
                    await self.connected_client.write_characteristic(
                        CHAR_UUID,
                        json.dumps({"type": "typing", "content": bool(message)}).encode()
                    )
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Server error: {str(e)}")
        finally:
            if self.connected_client:
                await self.connected_client.disconnect()

async def main():
    storage = ChatStorage("chat_history.json")
    server = BluetoothChatServer(storage)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())