import socket
import threading

def handle_client(client_socket):
    try:
        # Odczytaj pierwsze 262 bajty, które powinny zawierać wiadomość powitalną
        greeting = client_socket.recv(262)
        if len(greeting) < 2:
            print("Greeting length is too short")
            client_socket.close()
            return

        # Wysyłamy odpowiedź na wiadomość powitalną
        client_socket.send(b"\x05\x00")

        # Odczytaj kolejne 4 bajty, które powinny zawierać żądanie
        data = client_socket.recv(4)
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
        elif addrtype == 3:  # Domeny
            domain_length = client_socket.recv(1)[0]
            address = client_socket.recv(domain_length).decode('utf-8')
        else:
            print(f"Unsupported address type: {addrtype}")
            client_socket.close()
            return

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
            print(f"Error connecting to remote server: {e}")
        finally:
            client_socket.close()
            remote.close()
    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.close()

def main():
    server_host = input("Enter the server host (default: 0.0.0.0): ") or "0.0.0.0"
    server_port = int(input("Enter the server port (default: 1080): ") or 1080)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_host, server_port))
    server.listen(5)
    print(f"Listening on {server_host}:{server_port}...")
    while True:
        client_socket, addr = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
