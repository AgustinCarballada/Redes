from socket import *
import threading
import psutil
import time


SERVER_PORT = 6063
BROADCAST_IP = "172.16.132.223"
KEY = "server123"

client = socket(AF_INET, SOCK_DGRAM)
client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

client.sendto("DISCOVER".encode(), (BROADCAST_IP, SERVER_PORT))
message , (server_ip, server_port) = client.recvfrom(1024)

(_, cpu_rate, mem_rate, tcp_port) = message.decode().split(" ")

def wait_server_interrupt(client_tcp:socket):
    message = client_tcp.recv(1024)
    if message.decode() == "GET_PROC":
        # get pids
        client_tcp.send("PROC <pid>:<name>, .. , <pid>:<name>".encode())

# TCP connection
client_tcp = socket(AF_INET, SOCK_STREAM)
client_tcp.connect((server_ip, int(tcp_port)))

client_tcp.send(f"REGISTER {KEY}".encode())
message = client_tcp.recv(1024)
if message.decode() == "REG_RESP":
    print("conexion succesfull!")

    threading.Thread(target=wait_server_interrupt, args=(client_tcp), daemon=True).start()

    while True:
        time.sleep(15)
        cpu = psutil.cpu_percent()
        print(cpu)
        if cpu > cpu_rate:
            client_tcp.send(f"ALERT CPU {cpu}".encode())

        mem = psutil.vitual_memory().percent
        print(mem)
        if mem > mem_rate:
            client_tcp.send(f"ALERT MEM {mem}".encode())




