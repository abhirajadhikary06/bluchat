import asyncio
import json
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError

class BluetoothHandler:
    def __init__(self):
        self.client = None
        self.connected = False
        self.on_message = None
        self.on_typing = None
        self.service_uuid = "12345678-1234-5678-1234-567812345678"
        self.char_uuid = "87654321-4321-6789-4321-678943210987"

    async def discover_devices(self):
        devices = await BleakScanner.discover()
        return [(device.name or "Unknown", device.address) for device in devices]

    async def start_server(self, callback):
        try:
            # BLE server not directly supported in Bleak; simulate with client-to-client
            callback("Waiting for connections (client-to-client)...")
            # For simplicity, server mode is a placeholder; actual BLE requires GATT server setup
            # In this case, we'll assume client initiates connection
        except Exception as e:
            callback(f"Server error: {str(e)}")

    async def connect_to_device(self, addr, callback):
        try:
            self.client = BleakClient(addr)
            await self.client.connect()
            self.connected = True
            callback(f"Connected to {addr}")
            asyncio.create_task(self.receive_messages())
        except BleakError as e:
            callback(f"Connection failed: {str(e)}")
            self.connected = False

    async def send_message(self, message):
        if self.connected and self.client:
            try:
                data = json.dumps({"type": "message", "content": message}).encode()
                await self.client.write_characteristic(self.char_uuid, data)
            except BleakError:
                self.connected = False

    async def send_typing(self, is_typing):
        if self.connected and self.client:
            try:
                data = json.dumps({"type": "typing", "content": is_typing}).encode()
                await self.client.write_characteristic(self.char_uuid, data)
            except BleakError:
                self.connected = False

    async def receive_messages(self):
        def notification_handler(sender, data):
            try:
                packet = json.loads(data.decode())
                if packet["type"] == "message" and self.on_message:
                    self.on_message(packet["content"])
                elif packet["type"] == "typing" and self.on_typing:
                    self.on_typing(packet["content"])
            except json.JSONDecodeError:
                pass

        if self.connected and self.client:
            await self.client.start_notify(self.char_uuid, notification_handler)
            while self.connected:
                await asyncio.sleep(0.1)
            await self.client.stop_notify(self.char_uuid)

    async def disconnect(self):
        self.connected = False
        if self.client:
            await self.client.disconnect()