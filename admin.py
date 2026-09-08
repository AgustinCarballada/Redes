from socket import *
from time import sleep

SERVER_PORT = 6063
BROADCAST_IP = "255.255.255.255"
KEY = "server123"

def log_response(message, addr):
    print(message, addr)

def list_agents(admin_tcp, addr):
    admin_tcp.send("LIST_AGENTS\n".encode())

    message = admin_tcp.recv(1024).decode()
    log_response(message, addr)

def get_proc(admin_tcp, addr, id):
    admin_tcp.send(f"GET_PROC {id}\n".encode())

    message = admin_tcp.recv(1024).decode()
    log_response(message, addr)

def get_metric(admin_tcp, addr, id, type):
    admin_tcp.send(f"GET_METRIC {id} {type}\n".encode())

    message = admin_tcp.recv(1024).decode()
    log_response(message, addr)

def udp_discover():
    client = socket(AF_INET, SOCK_DGRAM)
    client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    client.sendto("DISCOVER\n".encode(), (BROADCAST_IP, SERVER_PORT))
    message , (server_ip, server_port) = client.recvfrom(1024)
    log_response(message, (server_ip, server_port))
    
    if message.decode().startswith("SERVER"):
        (_, cpu_rate, mem_rate, tcp_port) = message.decode().split(" ")

        # TCP connection
        admin_tcp = socket(AF_INET, SOCK_STREAM)
        admin_tcp.connect((server_ip, int(tcp_port)))  

        admin_tcp.send(f"ADMIN {KEY}\n".encode())
        message = admin_tcp.recv(1024)
        log_response(message, (server_ip, server_port))

        if message.decode().startswith("ADMIN_RESP"):
            list_agents(admin_tcp, (server_ip, server_port))
            get_proc(admin_tcp, (server_ip, server_port), 1)
            get_metric(admin_tcp, (server_ip, server_port), 1, "CPU")

if __name__ == "__main__":

    udp_discover()






