from socket import *
import threading
import psutil
import time

def log_response(message, addr):
    print(message, addr)

SERVER_PORT = 6063
BROADCAST_IP = "255.255.255.255"
KEY = "server123"

client = socket(AF_INET, SOCK_DGRAM)
client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
client.sendto("DISCOVER\n".encode(), (BROADCAST_IP, SERVER_PORT))
message , (server_ip, server_port) = client.recvfrom(1024)
log_response(message, (server_ip, server_port))

if message.decode().startswith("SERVER"):
    (_, cpu_rate, mem_rate, tcp_port) = message.decode().split(" ")
    cpu_rate = int(cpu_rate)
    mem_rate = int(mem_rate)

    def wait_server_interrupt(client_tcp:socket, addr):
        try:
            while True:
                message = client_tcp.recv(1024).decode()
                log_response(message, addr)
                if message.startswith("GET_PROC"):
                    message = "SE PROCESARON PROCESOS"
                    # for proc in psutil.process_iter(['pid', 'name']):
                    #     message += f"{proc.info["pid"]}:{proc.info["name"]} "
                    client_tcp.send(f"PROC {message}\n".encode())
        except OSError:
            return

    # TCP connection
    client_tcp = socket(AF_INET, SOCK_STREAM)
    client_tcp.connect((server_ip, int(tcp_port)))

    client_tcp.send(f"REGISTER {KEY}\n".encode())
    message = client_tcp.recv(1024)
    log_response(message, (server_ip, server_port))
    if message.decode().startswith("REG_RESP"):

        def send_metrics(client_tcp, cpu_rate, mem_rate):
            try:
                while True:
                    time.sleep(1)

                    cpu = psutil.cpu_percent()
                    if cpu > cpu_rate:
                        client_tcp.send(f"ALERT CPU {cpu}\n".encode())
                    else:
                        client_tcp.send(f"METRIC CPU {cpu}\n".encode())

                    mem = psutil.virtual_memory().percent
                    if mem > mem_rate:
                        client_tcp.send(f"ALERT MEM {mem}\n".encode())
                    else:
                        client_tcp.send(f"METRIC MEM {mem}\n".encode())
            except OSError:
                return

        threading.Thread(target=wait_server_interrupt, args=(client_tcp, (server_ip, int(tcp_port)), ), daemon=True).start()
        threading.Thread(target=send_metrics, args=(client_tcp, cpu_rate, mem_rate), daemon=True).start()

        time.sleep(60)

    client_tcp.send(f"END\n".encode())
    client_tcp.close()


