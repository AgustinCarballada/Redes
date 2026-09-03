from socket import *
import threading
import time

UDP_PORT = 6063
TCP_PORT = 9999
KEY = "server123"
id = 0

# UDP connection
def udp_discover():
    server = socket(AF_INET, SOCK_DGRAM)
    server.bind(("", UDP_PORT))
    while True:
        data, addr = server.recvfrom(1024)
        print("Broadcast register.")
        if data.decode() == "DISCOVER":
            server.sendto((f"SERVER UMBRAL_CPU UMBRAL_MEM {TCP_PORT}").encode(), addr)


# TCP connection 
def init_tcp_connection():
    master = socket(AF_INET, SOCK_STREAM)
    master.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    master.bind(("", TCP_PORT))
    master.listen()
    return master


def client_handler(connSocket: socket):
    print("asdasdasd")        
    connSocket.send(f"REG_RESP".encode())
    while True:
        message, addr = connSocket.recv(1024)
        (command, message) = message.decode().split(" ")
        if command == "METRIC":
            type, value = message.split(" ")
            print(type, value)



def connect_client(master:socket, id):
    id += 1
    while True:
        connection, addr = master.accept()
        message = connection.recv(1024)
        (command, key) = message.decode().split(" ")
        if key == KEY:
            threading.Thread(
                target= client_handler,
                args = (connection),
                daemon= True
            ).start()



# main
if __name__=='__main__':

    master = init_tcp_connection()

    
    # listener UDP
    udpThread = threading.Thread(target=udp_discover, daemon=True)
    # start TCP connection
    tcpThread = threading.Thread(target=connect_client , args=(master, id), daemon=True)
    
    udpThread.start()
    tcpThread.start()
    udpThread.join()
    tcpThread.join()


    # connect client
    connect_client(master, id)    


