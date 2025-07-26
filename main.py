import tkinter as tk
from gui import BluetoothChatGUI
from bluetooth_handler import BluetoothHandler
from chat_manager import ChatManager
from storage import ChatStorage

def main():
    root = tk.Tk()
    storage = ChatStorage("chat_history.json")
    bt_handler = BluetoothHandler()
    chat_manager = ChatManager(storage)
    app = BluetoothChatGUI(root, bt_handler, chat_manager)
    root.mainloop()

if __name__ == "__main__":
    main()