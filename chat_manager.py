from datetime import datetime
import json

class ChatManager:
    def __init__(self, storage):
        self.storage = storage
        self.nickname = ""
        self.messages = []

    def set_nickname(self, nickname):
        self.nickname = nickname
        self.storage.save_nickname(nickname)

    def load_nickname(self):
        return self.storage.load_nickname()

    def add_message(self, sender, content, is_self):
        timestamp = datetime.now().strftime("%I:%M %p")
        message = {"sender": sender, "content": content, "timestamp": timestamp, "is_self": is_self}
        self.messages.append(message)
        self.storage.save_message(sender, message)
        return message

    def load_messages(self, device_id):
        self.messages = self.storage.load_messages(device_id)
        return self.messages

    def clear_chat(self, device_id):
        self.messages = []
        self.storage.clear_messages(device_id)