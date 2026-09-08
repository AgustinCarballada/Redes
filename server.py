from socket import *
import threading
import time
import random

UDP_PORT = 6063
TCP_PORT = 9999
KEY = "server123"
id = 0
cpu_rate = 30
mem_rate = 80
clients = {}

def log_response(message, addr):
    print(message, addr)


# UDP connection
def udp_discover():
    server = socket(AF_INET, SOCK_DGRAM)
    server.bind(("", UDP_PORT))
    while True:
        data, addr = server.recvfrom(1024)
        log_response(data, addr)
        if data.decode().startswith("DISCOVER"):
            server.sendto(f"SERVER {cpu_rate} {mem_rate} {TCP_PORT}\n".encode(), addr)
        else:
            server.sendto(("ERROR\n".encode()), addr)

# TCP connection
def update_value(array, value):
    for i in range(9, 0, -1):
        array[i] = array[i - 1]
    array[0] = value
    return array


def client_handler(connSocket: socket, id:int, addr):
    connSocket.send(f"REG_RESP\n".encode())

    #TODO: borrar cuando se añanda el admin
    connSocket.send("GET_PROC\n".encode())

    buffer = ""
    close_connection = True
    while close_connection:
        data = connSocket.recv(1024).decode()
        if not data:
            print("haosials")
            connSocket.send("ERROR\n".encode())
            continue
        buffer += data
        while "\n" in buffer:
            message, buffer = buffer.split("\n", 1)
            log_response(message, addr)
            if message.startswith("METRIC"):
                (_, type, value) = message.split(" ")
                clients[id][type] = update_value(clients[id][type], value)
            elif message.startswith("ALERT"):
                (_, type, value) = message.split(" ")
                clients[id][type] = update_value(clients[id][type], value)
            elif message.startswith("PROC"):
                # logica admin q consulto
                print("Hacer logica admin")
            elif message.startswith("END"):
                clients[id] = ""
                connSocket.close()
                close_connection = False
                break
            else:
                connSocket.send("ERROR".encode())



def connect_client(id):
    master = socket(AF_INET, SOCK_STREAM)
    master.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    master.bind(("", TCP_PORT))
    master.listen()

    id += 1
    while True:
        connection, addr = master.accept()
        message = connection.recv(1024).decode().strip()
        log_response(message, addr)
        if message.startswith("REGISTER"):
            (_, key) = message.strip().split(" ")
            if key == KEY:
                clients[id] = {
                    "socket": connection,
                    "CPU": [0] * 10,
                    "MEM": [0] * 10,
                }
                threading.Thread(
                    target= client_handler,
                    args = (connection, id, addr),
                    daemon= True
                ).start()
                id += 1
            else:
                connection.send("ERROR".encode())



# main
if __name__=='__main__':

   # listener UDP
   udpThread = threading.Thread(target=udp_discover, daemon=True)
   # start TCP connection
   tcpThread = threading.Thread(target=connect_client , args=(id, ), daemon=True)

   udpThread.start()
   tcpThread.start()



   udpThread.join()
   tcpThread.join()



