import socket
import threading
import rsa
import os

# Sample users dictionary (in a real application, use a secure storage)
users = {
    "user1": "password1",
    "user2": "password2"
}

# Pobierz pełną ścieżkę do katalogu skryptu
script_dir = os.path.dirname(os.path.abspath(__file__))

# Wczytaj klucze RSA
server_private_key_path = os.path.join(script_dir, 'server_private_key.pem')

with open(server_private_key_path, 'rb') as f:
    server_private_key = rsa.PrivateKey.load_pkcs1(f.read())

def authenticate(client_socket):
    try:
        # Receive version and number of authentication methods supported
        greeting = client_socket.recv(2)
        if len(greeting) != 2 or greeting[0] != 0x05:
            client_socket.close()
            return False

        # Receive the list of authentication methods
        n_methods = greeting[1]
        methods = client_socket.recv(n_methods)

        # Check if the "username/password" method (0x02) is supported
        if 0x02 not in methods:
            # No acceptable methods
            client_socket.send(b"\x05\xFF")
            client_socket.close()
            return False

        # Send selection of "username/password" method
        client_socket.send(b"\x05\x02")

        # Receive username/password authentication request
        auth_request = client_socket.recv(2)
        if len(auth_request) != 2 or auth_request[0] != 0x01:
            client_socket.close()
            return False

        # Extract username
        username_len = auth_request[1]
        username = client_socket.recv(username_len).decode('utf-8')

        # Extract number of password chunks
        password_chunks_len = client_socket.recv(1)[0]
        encrypted_password = b""
        
        for _ in range(password_chunks_len):
            chunk_len = client_socket.recv(1)[0]
            encrypted_password += client_socket.recv(chunk_len)
        
        # Decrypt password
        decrypted_password = rsa.decrypt(encrypted_password, server_private_key).decode('utf-8')
        print(f"Received username: {username}")
        print(f"Received encrypted password: {encrypted_password}")
        print(f"Decrypted password: {decrypted_password}")

        # Validate username and password
        if username in users and users[username] == decrypted_password:
            # Authentication successful
            client_socket.send(b"\x01\x00")
            return True
        else:
            # Authentication failed
            client_socket.send(b"\x01\x01")
            client_socket.close()
            return False
    except Exception as e:
        print(f"Authentication error: {e}")
        client_socket.close()
        return False

def handle_client(client_socket):
    try:
        # Authenticate user
        if not authenticate(client_socket):
            print("Authentication failed")
            return

        # Read the SOCKS request
        data = client_socket.recv(4)
        print(f"SOCKS request: {data}")
        if len(data) < 4:
            print("Data length is too short")
            client_socket.close()
            return

        mode = data[1]
        if mode != 1:
            print(f"Unsupported mode: {mode}")
            client_socket.close()
            return

        addrtype = data[3]
        if addrtype == 1:  # IPv4
            address = socket.inet_ntoa(client_socket.recv(4))
        elif addrtype == 3:  # Domain name
            domain_length = client_socket.recv(1)[0]
            address = client_socket.recv(domain_length).decode('utf-8')
        else:
            print(f"Unsupported address type: {addrtype}")
            client_socket.close()
            return

        port = int.from_bytes(client_socket.recv(2), 'big')
        print(f"Connecting to {address}:{port}")

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
            print(f"Error connecting to remote server: {e}")
        finally:
            client_socket.close()
            remote.close()
    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.close()

def main():
    server_host = "0.0.0.0"
    server_port = 1081

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_host, server_port))
    server.listen(5)
    print(f"Listening on {server_host}:{server_port}...")
    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
