import tunetap
import socket

def configure_tun():
    tun = tunetap.TunTapDevice(name="tun0", mode='tun')
    tun.addr = '10.0.0.1'
    tun.netmask = '255.255.255.0'
    tun.mtu = 1500
    tun.up()
    print(f"Configured TUN device: {tun.name}, IP: {tun.addr}/{tun.netmask}")
    return tun

def tun_to_socks(tun):
    socks_address = ("127.0.0.1", 1080)
    while True:
        packet = tun.read()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(socks_address)
            s.send(packet)

if __name__ == "__main__":
    tun = configure_tun()
    tun_to_socks(tun)
