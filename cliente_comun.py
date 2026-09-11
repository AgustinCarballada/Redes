from socket import *
import threading
import psutil
import time

from utils import print_response


SERVER_PORT = 6063
BROADCAST_IP = "255.255.255.255"
KEY = "server123"
connection_alive = False


def response_thread(client_tcp:socket, addr):
    global connection_alive
    buffer = ""
    connection_alive = True
    try:
        while connection_alive:
            response = client_tcp.recv(1024).decode()

            # TODO : verify this
            if not response:
                raise

            buffer += response
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                print_response(message, addr)

                if message.startswith("GET_PROC"):
                    message = ""
                    for proc in psutil.process_iter(['pid', 'name']):
                        message += f" {proc.info["pid"]}:{proc.info["name"]}"
                    client_tcp.send(f"PROC{message}\n".encode())

    except Exception:
        if connection_alive:
            print("[TCP] ERROR 500 [COMMUNICATION ERROR]")
            connection_alive = False


def send_metrics(client_tcp):
    global connection_alive
    try:
        while connection_alive:
            time.sleep(5)

            cpu = psutil.cpu_percent()
            client_tcp.send(f"METRIC CPU {cpu}\n".encode())

            mem = psutil.virtual_memory().percent
            client_tcp.send(f"METRIC MEM {mem}\n".encode())
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass


def send_alerts(client_tcp, cpu_rate, mem_rate):
    global connection_alive
    try:
        while connection_alive:
            time.sleep(1)

            cpu = psutil.cpu_percent()
            if cpu > cpu_rate:
                client_tcp.send(f"ALERT CPU {cpu}\n".encode())

            mem = psutil.virtual_memory().percent
            if mem > mem_rate:
                client_tcp.send(f"ALERT MEM {mem}\n".encode())
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass


def terminal_thread(client_tcp):
    global connection_alive
    try:
        while connection_alive:
            message = input()
            client_tcp.send(f"{message}\n".encode())
            if message == "END":
                connection_alive = False
                print("wait there, shooting down ..")
    except:
        pass


def udp_discover():
    client = socket(AF_INET, SOCK_DGRAM)
    client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    client.settimeout(1)
    client.sendto("DISCOVER\n".encode(), (BROADCAST_IP, SERVER_PORT))

    try:
        message, upd_addr = client.recvfrom(1024)
    except TimeoutError:
        raise TimeoutError

    print_response(message, upd_addr)

    if message.decode().startswith("SERVER"):
        (_, cpu_rate, mem_rate, tcp_port) = message.decode().split(" ")
        cpu_rate = int(cpu_rate)
        mem_rate = int(mem_rate)
        tcp_addr = (upd_addr[0], int(tcp_port))
        global connection_alive

        # TCP connection
        client_tcp = socket(AF_INET, SOCK_STREAM)
        client_tcp.connect(tcp_addr)
        connection_alive = True

        client_tcp.send(f"REGISTER {KEY}\n".encode())
        message = client_tcp.recv(1024).decode().split("\n")[0]
        print_response(message, tcp_addr)

        if message.startswith("REG_RESP"):
            return client_tcp, tcp_addr, True, cpu_rate, mem_rate
    return _, _, False, _, _

if __name__ == "__main__":

    try:
        socket, addr, ok, cpu_rate, mem_rate = udp_discover()

        if ok:
            t1 = threading.Thread(target=response_thread, args=(socket, addr,), daemon=True)
            t2 = threading.Thread(target=send_metrics, args=(socket,), daemon=True)
            t3 = threading.Thread(target=send_alerts, args=(socket, cpu_rate, mem_rate), daemon=True)
            t4 = threading.Thread(target=terminal_thread, args=(socket,), daemon=True)

            t1.start()
            t2.start()
            t3.start()
            t4.start()

            while connection_alive:
                time.sleep(1)

            socket.close()

    except TimeoutError:
        print("[UDP] ERROR 504 [TIMEOUT ERROR]")



