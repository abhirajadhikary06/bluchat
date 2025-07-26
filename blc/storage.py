import json
import os

class ChatStorage:
    def __init__(self, filename):
        self.filename = filename
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                json.dump({"nickname": "", "chats": {}}, f)

    def load_nickname(self):
        with open(self.filename, "r") as f:
            data = json.load(f)
        return data.get("nickname", "")

    def save_nickname(self, nickname):
        with open(self.filename, "r") as f:
            data = json.load(f)
        data["nickname"] = nickname
        with open(self.filename, "w") as f:
            json.dump(data, f)

    def load_messages(self, device_id):
        with open(self.filename, "r") as f:
            data = json.load(f)
        return data.get("chats", {}).get(device_id, [])

    def save_message(self, device_id, message):
        with open(self.filename, "r") as f:
            data = json.load(f)
        if device_id not in data.get("chats", {}):
            data["chats"][device_id] = []
        data["chats"][device_id].append(message)
        with open(self.filename, "w") as f:
            json.dump(data, f)

    def clear_messages(self, device_id):
        with open(self.filename, "r") as f:
            data = json.load(f)
        if device_id in data.get("chats", {}):
            data["chats"][device_id] = []
        with open(self.filename, "w") as f:
            json.dump(data, f)