import socket
import threading

def handle_client(client_socket):
    client_socket.recv(262)
    client_socket.send(b"\x05\x00")
    data = client_socket.recv(4)
    mode = data[1]
    if mode == 1:
        addrtype = data[3]
        if addrtype == 1:
            address = socket.inet_ntoa(client_socket.recv(4))
        elif addrtype == 3:
            domain_length = client_socket.recv(1)[0]
            address = client_socket.recv(domain_length).decode('utf-8')
        port = int.from_bytes(client_socket.recv(2), 'big')
        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((address, port))
            client_socket.send(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + (9999).to_bytes(2, 'big'))
            client_socket.setblocking(False)
            remote.setblocking(False)
            while True:
                try:
                    data = client_socket.recv(4096)
                    if len(data) == 0:
                        break
                    remote.send(data)
                except:
                    pass
                try:
                    data = remote.recv(4096)
                    if len(data) == 0:
                        break
                    client_socket.send(data)
                except:
                    pass
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 1080))
    server.listen(5)
    print("Listening on port 1080...")
    while True:
        client_socket, addr = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
