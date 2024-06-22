import socket
import threading

def load_users():
    users = {}
    with open("users.txt", "r") as f:
        for line in f:
            username, password = line.strip().split(":")
            users[username] = password
    return users

def authenticate(username, password, users):
    return users.get(username) == password

def handle_client(client_socket, users):
    try:
        # Read authentication data
        auth_data = client_socket.recv(1024).decode().split(":")
        if len(auth_data) != 2 or not authenticate(auth_data[0], auth_data[1], users):
            client_socket.send(b"Authentication failed")
            client_socket.close()
            return
        client_socket.send(b"Authentication successful")

        # Read initial SOCKS5 handshake
        greeting = client_socket.recv(2)
        if len(greeting) != 2 or greeting[0] != 0x05:
            print("Unsupported SOCKS version or invalid greeting length")
            client_socket.close()
            return

        nmethods = greeting[1]
        methods = client_socket.recv(nmethods)
        client_socket.send(b"\x05\x00")  # No authentication required

        # Read SOCKS5 request
        request = client_socket.recv(4)
        if len(request) != 4 or request[0] != 0x05:
            print("Invalid SOCKS5 request")
            client_socket.close()
            return

        cmd = request[1]
        if cmd != 1:  # Only CONNECT is supported
            print(f"Unsupported SOCKS5 command: {cmd}")
            client_socket.send(b"\x05\x07\x00\x01")  # Command not supported
            client_socket.close()
            return

        addrtype = request[3]
        if addrtype == 1:  # IPv4
            address = socket.inet_ntoa(client_socket.recv(4))
        elif addrtype == 3:  # Domain
            domain_length = client_socket.recv(1)[0]
            address = client_socket.recv(domain_length).decode('utf-8')
        else:
            print(f"Unsupported address type: {addrtype}")
            client_socket.send(b"\x05\x08\x00\x01")  # Address type not supported
            client_socket.close()
            return

        port = int.from_bytes(client_socket.recv(2), 'big')

        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((address, port))
            client_socket.send(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + (port).to_bytes(2, 'big'))
            client_socket.setblocking(False)
            remote.setblocking(False)
            while True:
                try:
                    data = client_socket.recv(4096)
                    if len(data) == 0:
                        break
                    remote.send(data)
                except BlockingIOError:
                    pass
                try:
                    data = remote.recv(4096)
                    if len(data) == 0:
                        break
                    client_socket.send(data)
                except BlockingIOError:
                    pass
        except Exception as e:
            print(f"Error connecting to remote server: {e}")
            client_socket.send(b"\x05\x04\x00\x01")  # Host unreachable
        finally:
            client_socket.close()
            remote.close()
    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.close()

def main():
    users = load_users()
    server_host = input("Enter the server host (default: 0.0.0.0): ") or "0.0.0.0"
    server_port = int(input("Enter the server port (default: 1080): ") or 1080)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_host, server_port))
    server.listen(5)
    print(f"Listening on {server_host}:{server_port}...")
    while True:
        client_socket, addr = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, users))
        client_handler.start()

if __name__ == "__main__":
    main()
