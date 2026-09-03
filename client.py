from socket import *

SERVER_PORT = 6063
BROADCAST_IP = "255.255.255.255"
KEY = "bolsoputo"

client = socket(AF_INET, SOCK_DGRAM)
client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

client.sendto("DISCOVER".encode(), (BROADCAST_IP, SERVER_PORT))
message , (server_ip, server_port) = client.recvfrom(1024)

(_, cpu_rate, mem_rate, tcp_port) = message.decode().split(" ")

print(tcp_port)

# TCP connection
client_tcp = socket(AF_INET, SOCK_STREAM)
client_tcp.connect((server_ip, int(tcp_port)))

client_tcp.send(f"REGISTER {KEY}".encode())
message = client_tcp.recv(1024)
if message.decode() == "REG_RESP":
    print("conexion succesfull!")



