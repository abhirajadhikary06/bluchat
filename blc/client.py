import asyncio
import argparse
import json
import datetime
from bleak import BleakClient
from storage import load_history, save_message

# Replace with your characteristic UUID (must match server setup)
CHAT_CHAR_UUID = "0000xxxx-0000-1000-8000-00805f9b34fb"

def get_args():
    parser = argparse.ArgumentParser(description="Bluetooth Chat Client")
    parser.add_argument("--addr", type=str, help="Bluetooth MAC address of peer device")
    return parser.parse_args()

async def run_chat(address):
    print(f"Connecting to {address}...")
    async with BleakClient(address) as client:
        if not await client.is_connected():
            print("Failed to connect")
            return

        print("Connected to", address)

        history = load_history(address)
        if history:
            print("\n--- Chat History ---")
            for entry in history:
                ts = entry["timestamp"]
                print(f"{entry['direction']} [{ts}]: {entry['message']}")
            print("--------------------\n")

        def notification_handler(sender, data):
            text = data.decode("utf-8")
            ts = datetime.datetime.now().isoformat(timespec="seconds")
            print(f"\rPeer [{ts}]: {text}\n> ", end="", flush=True)
            save_message(address, {
                "direction": "recv",
                "timestamp": ts,
                "message": text
            })

        await client.start_notify(CHAT_CHAR_UUID, notification_handler)

        try:
            while True:
                msg = input("> ")
                if msg.lower() in ("exit", "quit"):
                    break
                ts = datetime.datetime.now().isoformat(timespec="seconds")
                await client.write_gatt_char(CHAT_CHAR_UUID, msg.encode("utf-8"))
                save_message(address, {
                    "direction": "sent",
                    "timestamp": ts,
                    "message": msg
                })
        except KeyboardInterrupt:
            print("\nDisconnected.")
        finally:
            await client.stop_notify(CHAT_CHAR_UUID)

if __name__ == "__main__":
    args = get_args()
    if args.addr:
        mac_address = args.addr
    else:
        mac_address = input("Enter the Bluetooth MAC address of the peer device: ").strip()

    asyncio.run(run_chat(mac_address))
