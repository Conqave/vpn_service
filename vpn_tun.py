import os
import fcntl
import struct
import socket
import rsa

TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

# Pobierz pełną ścieżkę do katalogu skryptu
script_dir = os.path.dirname(os.path.abspath(__file__))

# Wczytaj klucze RSA
client_private_key_path = os.path.join(script_dir, 'client_private_key.pem')
server_public_key_path = os.path.join(script_dir, 'server_public_key.pem')

with open(client_private_key_path, 'rb') as f:
    client_private_key = rsa.PrivateKey.load_pkcs1(f.read())

with open(server_public_key_path, 'rb') as f:
    server_public_key = rsa.PublicKey.load_pkcs1(f.read())

def configure_tun(tun_ip, tun_netmask):
    tun = os.open('/dev/net/tun', os.O_RDWR)
    ifr = struct.pack('16sH', b'tun0', IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)

    os.system(f"sudo ip addr add {tun_ip}/{tun_netmask} dev tun0")
    os.system("sudo ip link set dev tun0 up")
    
    print(f"Using existing TUN device: tun0, IP: {tun_ip}/{tun_netmask}")
    return tun

def split_bytes(data, chunk_size):
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

def tun_to_socks(tun, socks_host, socks_port, username, password):
    socks_address = (socks_host, socks_port)
    while True:
        packet = os.read(tun, 4096)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                print("Connecting to SOCKS5 server...")
                s.connect(socks_address)
                print("Connected to SOCKS5 server")
                
                # SOCKS5 handshake
                s.sendall(b"\x05\x01\x02")
                response = s.recv(2)
                print(f"SOCKS5 handshake response: {response}")
                if len(response) < 2 or response[1] != 0x02:
                    print(f"No acceptable authentication methods, received: {response}")
                    return

                # Encrypt password
                encrypted_password = rsa.encrypt(password.encode('utf-8'), server_public_key)
                print(f"Encrypted password: {encrypted_password}")

                # Split encrypted password into manageable chunks
                password_chunks = split_bytes(encrypted_password, 255)

                # Username/Password authentication
                s.sendall(b"\x01" + bytes([len(username)]) + username.encode('utf-8') + bytes([len(password_chunks)]))
                for chunk in password_chunks:
                    s.sendall(bytes([len(chunk)]) + chunk)
                
                auth_response = s.recv(2)
                print(f"Authentication response: {auth_response}")
                if len(auth_response) < 2 or auth_response[1] != 0x00:
                    print(f"Authentication failed, received: {auth_response}")
                    return

                # SOCKS5 request (IPv4 address 0.0.0.0 and port 0)
                s.sendall(b"\x05\x01\x00\x01" + socket.inet_aton("0.0.0.0") + (0).to_bytes(2, 'big'))
                response = s.recv(10)
                print(f"SOCKS5 request response: {response}")
                if len(response) < 10 or response[1] != 0x00:
                    print(f"SOCKS5 request failed, received: {response}")
                    return
                
                # Send the packet from TUN to SOCKS server
                s.sendall(packet)
                print(f"Sent packet: {packet}")

                while True:
                    response = s.recv(4096)
                    if not response:
                        break
                    os.write(tun, response)
                    print(f"Wrote packet to TUN: {response}")

            except Exception as e:
                print(f"Error connecting to remote server: {e}")

if __name__ == "__main__":
    tun_ip = "10.8.0.1"
    tun_netmask = "24"
    socks_host = "127.0.0.1"
    socks_port = 1080
    username = "user1"
    password = "password1"

    tun = configure_tun(tun_ip, tun_netmask)
    tun_to_socks(tun, socks_host, socks_port, username, password)
