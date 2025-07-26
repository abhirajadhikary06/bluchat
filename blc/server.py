import socket

# Steps
# 1. Device Manager -> Realtek Bluetooth Adapter
# 2. Right Click -> Properties -> Advanced -> Address
# 3. Turn on Bluetooth on both devices and make server device visible

server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)  # RFCOMM specific protocol
server.bind(("1c:ce:51:3e:a2:b4", 4))  # MAC Address and Channel 4 #28:d0:43:51:e4:4b
server.listen(1)

print("Waiting for connection...")

client, addr = server.accept()
print(f"Accepted connection from {addr}")

try:
    while True:
        data = client.recv(1024)
        if not data:
            break
        print(f"Received: {data.decode('utf-8')}")
        message = input("Enter message: ")
        client.send(message.encode('utf-8'))
except OSError:
    pass

print("Disconnected")

client.close()
server.close()