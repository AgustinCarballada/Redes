import time
import threading
from socket import *

from utils import print_response, parse_admin_message


SERVER_PORT = 6063
BROADCAST_IP = "255.255.255.255"
KEY = "server123"
connection_alive = False


def response_thread(admin_tcp, addr):
    global connection_alive
    buffer = ""
    connection_alive = True
    try:
        while connection_alive:
            response = admin_tcp.recv(1024).decode()

            if not response:
                raise

            buffer += response
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                print_response(message, addr)

    except Exception:
        if connection_alive:
            print("[TCP] ERROR 500 [COMMUNICATION ERROR]")
            connection_alive = False


def udp_discover():
    client = socket(AF_INET, SOCK_DGRAM)
    client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    client.settimeout(2)

    message = None
    for trial in range(3):
        client.sendto("DISCOVER\n".encode(), (BROADCAST_IP, SERVER_PORT))
        try:
            message, udp_addr = client.recvfrom(1024)
            break
        except TimeoutError:
            print(f"[UDP] ERROR 503 [SERVICE UNAVAILABLE]")

    client.close()
    if message is None:
        raise TimeoutError

    print_response(message, udp_addr)

    if message.decode().startswith("SERVER"):
        (_, cpu_rate, mem_rate, tcp_port) = message.decode().split(" ")
        tcp_addr = (udp_addr[0], int(tcp_port))
        global connection_alive

        # TCP connection
        admin_tcp = socket(AF_INET, SOCK_STREAM)
        admin_tcp.connect(tcp_addr)
        connection_alive = True

        admin_tcp.send(f"ADMIN {KEY}\n".encode())
        message = admin_tcp.recv(1024).decode().split("\n")[0]
        print_response(message, tcp_addr)

        if message.startswith("ADMIN_RESP"):
            return admin_tcp, tcp_addr, True
    return _, _, False

def terminal_thread(client_tcp):
    global connection_alive
    try:
        while connection_alive:
            message = input()
            request = parse_admin_message(message)
            client_tcp.send(request.encode())
            if message == "END":
                connection_alive = False
                print("wait there, shooting down ..")
    except:
        pass


if __name__ == "__main__":
    try:
        socket, addr, ok = udp_discover()

        if ok:
            t1 = threading.Thread(target=response_thread, args=(socket, addr), daemon=True)
            t2 = threading.Thread(target=terminal_thread, args=(socket,), daemon=True)

            t1.start()
            t2.start()

            while connection_alive:
                time.sleep(1)

            socket.close()

    except TimeoutError:
        print("[UDP] ERROR 504 [TIMEOUT ERROR]")









