import json
from pathlib import Path

STORAGE_DIR = Path("chats")
STORAGE_DIR.mkdir(exist_ok=True)

def load_history(peer_addr):
    path = STORAGE_DIR / f"{peer_addr}.json"
    if path.exists():
        return json.loads(path.read_text())
    return []

def save_message(peer_addr, message_entry):
    history = load_history(peer_addr)
    history.append(message_entry)
    path = STORAGE_DIR / f"{peer_addr}.json"
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2))
