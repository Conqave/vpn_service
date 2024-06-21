import os
import fcntl
import struct
import socket

TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

def configure_tun(tun_ip, tun_netmask):
    tun = os.open('/dev/net/tun', os.O_RDWR)
    ifr = struct.pack('16sH', b'tun0', IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)

    os.system(f"sudo ip addr add {tun_ip}/{tun_netmask} dev tun0")
    os.system("sudo ip link set dev tun0 up")

    print(f"Using existing TUN device: tun0, IP: {tun_ip}/{tun_netmask}")
    return tun

def tun_to_socks(tun, socks_host, socks_port, username, password):
    socks_address = (socks_host, socks_port)
    while True:
        packet = os.read(tun, 4096)
        print(f"Read packet from TUN: {packet}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(socks_address)
            s.send(f"{username}:{password}".encode())
            response = s.recv(1024)
            if response != b"Authentication successful":
                print("Authentication failed")
                break

            s.send(packet)
            print(f"Sent packet to SOCKS5 server: {packet}")

            while True:
                response = s.recv(4096)
                if not response:
                    break
                print(f"Received packet from SOCKS5 server: {response}")
                # Sprawdzamy, czy odpowiedź jest poprawnym pakietem sieciowym
                if response.startswith(b'E') or response.startswith(b'\x45'):
                    os.write(tun, response)
                    print(f"Wrote packet to TUN: {response}")

if __name__ == "__main__":
    tun_ip = input("Enter the TUN device IP address (default: 10.8.0.1): ") or "10.8.0.1"
    tun_netmask = input("Enter the TUN device netmask (default: 24): ") or "24"
    socks_host = input("Enter the SOCKS5 server host (default: 127.0.0.1): ") or "127.0.0.1"
    socks_port = int(input("Enter the SOCKS5 server port (default: 1080): ") or 1080)
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    tun = configure_tun(tun_ip, tun_netmask)
    tun_to_socks(tun, socks_host, socks_port, username, password)
