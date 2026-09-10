from socket import *
import threading
import time


KEY = "server123"
UDP_PORT = 6046
TCP_PORT = 9999
cpu_rate = 30
mem_rate = 90
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


def client_handler(conn_socket: socket, client_id:int, addr):
    conn_socket.send("REG_RESP\n".encode())

    buffer = ""
    connection_alive = True
    try:
        while connection_alive:
            data = conn_socket.recv(1024).decode()
            
            if not data:
                conn_socket.send("ERROR\n".encode())
                continue
            #TODO: Verificar con el profesor


            buffer += data
            while "\n" in buffer:

                message, buffer = buffer.split("\n", 1)
                log_response(message, addr)
      
                if message.startswith("METRIC"):
                    (_, type, value) = message.split(" ")
                    clients[client_id][type] = update_value(clients[client_id][type], value)
                elif message.startswith("ALERT"):
                    (_, type, value) = message.split(" ")
                    clients[client_id][type] = update_value(clients[client_id][type], value)
                elif message.startswith("PROC"):
                    (_, message) = data.split(" ", 1)
                    clients[client_id]["last_process"] = message
                elif message.startswith("END"):
                    connection_alive = False
                    break
                else:
                    conn_socket.send("ERROR".encode())
    except:
        return
    finally:
        del clients[client_id]
        conn_socket.close()


def admin_handler(connSocket: socket, addr):
    buffer = ""
    connection_alive = True
    connSocket.send("ADMIN_RESP\n".encode())
    try:
        while connection_alive:
            data = connSocket.recv(1024).decode()
            if not data:
                connSocket.send("ERROR\n".encode())
                continue
            #TODO : lo mismo verificar con el profe

            buffer += data
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                log_response(message, addr)
                if message.startswith("LIST_AGENTS"):
                    client_list = str(len(clients))
                    for cliente in clients:
                        client_list += " " + str(cliente)
                    connSocket.send((f"AGENTS {client_list}\n").encode())
                elif message.startswith("GET_PROC"):
                    (_, id) = message.split(" ")
                    id = int(id)

                    client_socket = clients[id]["socket"]
                    client_socket.send("GET_PROC\n".encode())
                    time.sleep(1) 
                    if clients[id]["last_process"]:
                        message = f"PROC {id} {clients[id]["last_process"]}"
                        clients[id]["last_process"] = ""
                    else:
                        message = "ERROR\n"  

                    connSocket.send(message.encode())
                elif message.startswith("GET_METRIC"):
                    (_, id, type) = message.split(" ")
                    id = int(id)
                    message = f"MEASURMENTS {id} {type}"
                    for i in clients[id][type]:
                        message +=  f" {i}"
                    message += "\n"
                    connSocket.send(message.encode())
    except:
        return
    finally:
        connSocket.close()


def connect_agent(id):
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
                connection.send("ERROR\n".encode())


        elif message.startswith("ADMIN"):
            (_, key) = message.strip().split(" ")
            if key == KEY:
                threading.Thread(
                    target = admin_handler,
                    args = (connection, addr),
                    daemon = True
                ).start()
            else:
                connection.send("ERROR\n".encode())


# main
if __name__=='__main__':

   # listener UDP
   udpThread = threading.Thread(target=udp_discover, daemon=True)
   # start TCP connection
   tcpThread = threading.Thread(target=connect_agent , args=(0, ), daemon=True)

   udpThread.start()
   tcpThread.start()

   udpThread.join()
   tcpThread.join()



