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

def tun_to_socks(tun, socks_host, socks_port):
    socks_address = (socks_host, socks_port)
    while True:
        packet = os.read(tun, 4096)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(socks_address)
            s.send(packet)

if __name__ == "__main__":
    tun_ip = input("Enter the TUN device IP address (default: 10.8.0.1): ") or "10.8.0.1"
    tun_netmask = input("Enter the TUN device netmask (default: 24): ") or "24"
    socks_host = input("Enter the SOCKS5 server host (default: 127.0.0.1): ") or "127.0.0.1"
    socks_port = int(input("Enter the SOCKS5 server port (default: 1080): ") or 1080)

    tun = configure_tun(tun_ip, tun_netmask)
    tun_to_socks(tun, socks_host, socks_port)
