from socket import *
import threading
import psutil
import time


SERVER_PORT = 6063
BROADCAST_IP = "255.255.255.255"
KEY = "server123"

connection_alive = False

def log_response(message, addr):
    print(message, addr)


def wait_server_interrupt(client_tcp:socket, addr):
    global connection_alive
    try:
        while connection_alive:
            response = client_tcp.recv(1024).decode()
            log_response(response, addr)
            if not response:
                raise
            if response.startswith("GET_PROC"):
                message = ""
                for proc in psutil.process_iter(['pid', 'name']):
                    message += f" {proc.info["pid"]}:{proc.info["name"]}"
                client_tcp.send(f"PROC{message}\n".encode())
    except:
        connection_alive = False
        return


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
        return

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
        return


if __name__ == "__main__":

    client = socket(AF_INET, SOCK_DGRAM)
    client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    client.sendto("DISCOVER\n".encode(), (BROADCAST_IP, SERVER_PORT))
    message, (server_ip, server_port) = client.recvfrom(1024)
    log_response(message, (server_ip, server_port))

    if message.decode().startswith("SERVER"):
        (_, cpu_rate, mem_rate, tcp_port) = message.decode().split(" ")
        cpu_rate = int(cpu_rate)
        mem_rate = int(mem_rate)

        # TCP connection
        client_tcp = socket(AF_INET, SOCK_STREAM)
        client_tcp.connect((server_ip, int(tcp_port)))
        connection_alive = True

        client_tcp.send(f"REGISTER {KEY}\n".encode())
        message = client_tcp.recv(1024)
        log_response(message, (server_ip, server_port))
        if message.decode().startswith("REG_RESP"):

            t1 = threading.Thread(target=wait_server_interrupt, args=(client_tcp, (server_ip, int(tcp_port)), ), daemon=True)
            t1.start()
            t2 = threading.Thread(target=send_metrics, args=(client_tcp, ), daemon=True)
            t2.start()
            t3 = threading.Thread(target=send_alerts, args=(client_tcp, cpu_rate, mem_rate), daemon=True)
            t3.start()

            while connection_alive:
                message = input()
                if message == "END":
                    client_tcp.send(f"END\n".encode())
                    connection_alive = False

            t1.join()
            t2.join()
            t3.join()

        client_tcp.close()
