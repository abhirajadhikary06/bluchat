import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import emoji
import asyncio
from ttkbootstrap.style import Style

class BluetoothChatGUI:
    def __init__(self, root, bt_handler, chat_manager):
        self.root = root
        self.bt_handler = bt_handler
        self.chat_manager = chat_manager
        self.style = Style(theme="darkly")  # Teams-like dark theme
        self.root.title("Bluetooth Chat")
        self.root.geometry("1000x700")
        self.device_id = None
        self.is_typing = False
        self.loop = asyncio.get_event_loop()
        self.setup_ui()
        self.bt_handler.on_message = self.receive_message
        self.bt_handler.on_typing = self.update_typing_status

    def setup_ui(self):
        # Configure Teams-like styles
        self.style.configure("TButton", font=("Segoe UI", 12))
        self.style.configure("TLabel", font=("Segoe UI", 12))
        self.style.configure("TEntry", font=("Segoe UI", 12))

        # Main container with sidebar and chat area
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=BOTH, expand=True)

        # Sidebar (Teams-like)
        self.sidebar = ttk.Frame(self.main_frame, width=250, bootstyle=DARK)
        self.sidebar.pack(side=LEFT, fill=Y, padx=(0, 1))
        self.sidebar.pack_propagate(False)

        # Chat area
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        self.setup_nickname_dialog()

    def setup_nickname_dialog(self):
        nickname = self.chat_manager.load_nickname()
        if not nickname:
            self.nickname_window = ttkb.Toplevel(self.root)
            self.nickname_window.title("Set Nickname")
            self.nickname_window.geometry("350x200")
            self.nickname_window.resizable(False, False)
            ttk.Label(self.nickname_window, text="Enter your nickname:", font=("Segoe UI", 14)).pack(pady=20)
            self.nickname_entry = ttk.Entry(self.nickname_window, width=25)
            self.nickname_entry.pack(pady=10)
            ttk.Button(self.nickname_window, text="Save", bootstyle=SUCCESS, command=self.save_nickname).pack(pady=10)
        else:
            self.chat_manager.set_nickname(nickname)
            self.setup_sidebar()

    def save_nickname(self):
        nickname = self.nickname_entry.get().strip()
        if nickname:
            self.chat_manager.set_nickname(nickname)
            self.nickname_window.destroy()
            self.setup_sidebar()
        else:
            messagebox.showerror("Error", "Nickname cannot be empty!")

    def setup_sidebar(self):
        ttk.Label(self.sidebar, text=f"Welcome, {self.chat_manager.nickname}", font=("Segoe UI", 14, "bold"), bootstyle=LIGHT).pack(pady=10)
        self.device_listbox = tk.Listbox(self.sidebar, font=("Segoe UI", 12))  # <-- Changed here
        self.device_listbox.pack(fill=BOTH, expand=True, padx=10, pady=5)
        ttk.Button(self.sidebar, text="Refresh Devices", bootstyle=INFO, command=self.refresh_devices).pack(pady=5)
        ttk.Button(self.sidebar, text="Connect", bootstyle=SUCCESS, command=self.connect_to_device).pack(pady=5)

        self.refresh_devices()

    def refresh_devices(self):
        self.device_listbox.delete(0, tk.END)
        devices = self.loop.run_until_complete(self.bt_handler.discover_devices())
        for name, addr in devices:
            self.device_listbox.insert(tk.END, f"{name} ({addr})")

    def connect_to_device(self):
        selection = self.device_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a device!")
            return
        device = self.device_listbox.get(selection[0])
        addr = device.split("(")[-1].strip(")")
        self.device_id = addr
        self.loop.run_until_complete(self.bt_handler.connect_to_device(addr, self.update_status))

    def update_status(self, message):
        if "Connected" in message:
            self.setup_chat_window()
        else:
            messagebox.showinfo("Status", message)

    def setup_chat_window(self):
        self.chat_frame.destroy()
        self.chat_frame = ttk.Frame(self.main_frame, bootstyle=SECONDARY)
        self.chat_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        # Chat header
        ttk.Label(self.chat_frame, text=f"Chatting as {self.chat_manager.nickname}", font=("Segoe UI", 16, "bold")).pack(pady=10)
        self.typing_label = ttk.Label(self.chat_frame, text="", font=("Segoe UI", 10, "italic"))
        self.typing_label.pack()

        # Chat text area
        self.chat_text = tk.Text(self.chat_frame, height=20, state="disabled", wrap="word", font=("Segoe UI", 12), bg="#2b2b2b", fg="white", insertbackground="white")
        self.chat_text.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Input area
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill=X, padx=10, pady=5)
        self.message_entry = ttk.Entry(input_frame, font=("Segoe UI", 12))
        self.message_entry.pack(side=LEFT, fill=X, expand=True)
        self.message_entry.bind("<KeyRelease>", self.on_typing)
        self.message_entry.bind("<Return>", self.send_message)
        ttk.Button(input_frame, text="Send", bootstyle=SUCCESS, command=self.send_message).pack(side=RIGHT, padx=5)
        ttk.Button(self.chat_frame, text="Clear Chat", bootstyle=DANGER, command=self.clear_chat).pack(side=LEFT, padx=10)
        ttk.Button(self.chat_frame, text="Disconnect", bootstyle=WARNING, command=self.disconnect).pack(side=LEFT, padx=10)

        # Load previous messages
        if self.device_id:
            messages = self.chat_manager.load_messages(self.device_id)
            for msg in messages:
                self.display_message(msg["sender"], msg["content"], msg["timestamp"], msg["is_self"])

    def on_typing(self, event=None):
        text = self.message_entry.get().strip()
        is_typing = bool(text)
        if is_typing != self.is_typing:
            self.is_typing = is_typing
            self.loop.run_until_complete(self.bt_handler.send_typing(is_typing))

    def update_typing_status(self, is_typing):
        self.typing_label.config(text="Typing..." if is_typing else "")

    def send_message(self, event=None):
        message = self.message_entry.get().strip()
        if message:
            message = emoji.emojize(message, language="alias")
            self.loop.run_until_complete(self.bt_handler.send_message(message))
            msg = self.chat_manager.add_message(self.chat_manager.nickname, message, True)
            self.display_message(msg["sender"], msg["content"], msg["timestamp"], True)
            self.message_entry.delete(0, tk.END)
            self.on_typing()

    def receive_message(self, message):
        msg = self.chat_manager.add_message("Other", message, False)
        self.root.after(0, self.display_message, msg["sender"], msg["content"], msg["timestamp"], False)

    def display_message(self, sender, content, timestamp, is_self):
        self.chat_text.config(state="normal")
        tag = "self" if is_self else "other"
        self.chat_text.tag_configure("self", foreground="white", background="#0078d4", justify="right", lmargin1=50, rmargin=10)
        self.chat_text.tag_configure("other", foreground="white", background="#444444", justify="left", lmargin1=10, rmargin=50)
        self.chat_text.insert(tk.END, f"{sender} ({timestamp}): {content}\n", tag)
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)

    def clear_chat(self):
        if self.device_id:
            self.chat_manager.clear_chat(self.device_id)
            self.chat_text.config(state="normal")
            self.chat_text.delete(1.0, tk.END)
            self.chat_text.config(state="disabled")

    def disconnect(self):
        self.loop.run_until_complete(self.bt_handler.disconnect())
        self.chat_frame.destroy()
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        self.setup_sidebar()