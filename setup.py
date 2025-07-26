from setuptools import setup

setup(
    name="BluetoothChatApp",
    version="1.0",
    description="A BLE-based chat application",
    author="Your Name",
    packages=["bluetooth_chat_app"],
    install_requires=[
        "bleak",
        "ttkbootstrap",
        "emoji",
    ],
)