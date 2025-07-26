import asyncio
import json
import datetime
from bleak import BleakScanner, BleakClient
from storage import load_history, save_message

CHAT_CHAR_UUID = "0000xxxx-0000-1000-8000-00805f9b34fb"  # define a custom UUID

async def run_chat():
    print("Scanning for devices...")
    devices = await BleakScanner.discover()
    for i, d in enumerate(devices):
        print(f"{i}: {d.name} [{d.address}]")
    idx = int(input("Select device index to chat with: "))
    peer = devices[idx]
    print(f"Connecting to {peer.address}...")
    async with BleakClient(peer.address) as client:
        if not await client.is_connected():
            print("Failed to connect")
            return
        print("Connected")
        history = load_history(peer.address)
        for entry in history:
            ts = entry["timestamp"]
            print(f"{entry['direction']} [{ts}] {entry['message']}")
        def notification_handler(sender, data):
            text = data.decode('utf‑8')
            ts = datetime.datetime.now().isoformat()
            print(f"\rPeer [{ts}]: {text}\n> ", end="", flush=True)
            save_message(peer.address, {"direction": "recv", "timestamp": ts, "message": text})

        await client.start_notify(CHAT_CHAR_UUID, notification_handler)

        while True:
            msg = input("> ")
            if msg.lower() in ("exit", "quit"):
                break
            ts = datetime.datetime.now().isoformat()
            await client.write_gatt_char(CHAT_CHAR_UUID, msg.encode('utf‑8'))
            save_message(peer.address, {"direction": "sent", "timestamp": ts, "message": msg})
        await client.stop_notify(CHAT_CHAR_UUID)

if __name__ == "__main__":
    asyncio.run(run_chat())
