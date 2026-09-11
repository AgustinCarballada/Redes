from socket import *
import threading
import time

KEY = "server123"
UDP_PORT = 6063
TCP_PORT = 9999
cpu_rate = 30
mem_rate = 90
clients = {}

# UTILS
def log_response(message, addr):
    if type(message) == bytes:
        print(f"[UDP] {message.decode().split("\n")[0][:1024]}, HOST: {addr}")
    else:
        print(f"[TCP] {message[:1024]}, HOST: {addr}")


def update_value(array, value):
    for i in range(9, 0, -1):
        array[i] = array[i - 1]
    array[0] = value
    return array


def parse_client_list():
    client_list = str(len(clients))
    for client in clients:
        client_list += f" {client}"
    return client_list


def parse_get_proc(client_id):
    client_socket = clients[client_id]["socket"]
    client_socket.send("GET_PROC\n".encode())
    time.sleep(1)
    if clients[client_id]["last_process"]:
        message = f"PROC {client_id} {clients[client_id]["last_process"]}\n"
        clients[client_id]["last_process"] = ""
    else:
        message = "ERROR 504 [AGENT TIMEOUT]\n"
    return message


def parse_metrics(client_id, metric_type):
    message = f"MEASURMENTS {client_id} {metric_type}"
    for i in clients[client_id][metric_type]:
        message += f" {i}"
    return f"{message}\n"


def parse_params(message):
    parts = message.split(" ")
    command = parts[0]
    if command == "PROC":
        return (command, " ".join(parts[1:]), "")
    parts += ["", ""]
    return (command, parts[1], parts[2])

# UDP CONNECTION
def udp_discover():
    server = socket(AF_INET, SOCK_DGRAM)
    server.bind(("", UDP_PORT))
    while True:
        data, addr = server.recvfrom(1024)
        log_response(data, addr)
        if data.decode().startswith("DISCOVER"):
            server.sendto(f"SERVER {cpu_rate} {mem_rate} {TCP_PORT}\n".encode(), addr)
        else:
            server.sendto(("ERROR 400 [BAD REQUEST]\n".encode()), addr)


def is_number(number):
    try:
        float(number)
        return True
    except ValueError:
        try:
            int(number)
            return True
        except ValueError:
            return False


# TCP CONNECTION
def client_handler(conn_socket: socket, client_id:int, addr):
    conn_socket.send("REG_RESP\n".encode())

    buffer = ""
    connection_alive = True
    try:
        while connection_alive:
            data = conn_socket.recv(1024).decode()

            # TODO : lo mismo verificar con el profe
            if not data:
                conn_socket.send("ERROR 500 [COMMUNICATION ERROR]\n".encode())
                break

            buffer += data
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                log_response(message, addr)
                (command, param1, param2) = parse_params(message)
                if command == "METRIC" and param1 in ("MEM", "CPU") and is_number(param2):
                    clients[client_id][param1] = update_value(clients[client_id][param1], param2)
                elif command == "ALERT" and param1 in ("MEM", "CPU") and is_number(param2):
                    clients[client_id][param1] = update_value(clients[client_id][param1], param2)
                elif command == "PROC" and param1 and not param2:
                    clients[client_id]["last_process"] = param1
                elif command == "END" and not param1 and not param2:
                    connection_alive = False
                    break
                else:
                    conn_socket.send("ERROR 400 [BAD REQUEST]\n".encode())
    except:
        pass
    finally:
        del clients[client_id]
        conn_socket.close()


def admin_handler(conn_socket: socket, addr):
    buffer = ""
    connection_alive = True
    conn_socket.send("ADMIN_RESP\n".encode())
    try:
        while connection_alive:
            data = conn_socket.recv(1024).decode()

            # TODO : lo mismo verificar con el profe
            if not data:
                conn_socket.send("ERROR 500 [COMMUNICATION ERROR]\n".encode())
                break


            buffer += data
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                log_response(message, addr)

                (command, param1, param2) = parse_params(message)
                if command == "LIST_AGENTS" and not param1 and not param2:
                    client_list = parse_client_list()
                    conn_socket.send((f"AGENTS {client_list}\n").encode())
                elif command == "GET_PROC" and is_number(param1) and not param2 :
                    client_id = int(param1)
                    if client_id not in clients:
                        conn_socket.send("ERROR 404 [NOT FOUND]\n".encode())
                        continue
                    message = parse_get_proc(client_id)
                    conn_socket.send(message.encode())
                elif command == "GET_METRIC" and is_number(param1) and param2 in ("MEM", "CPU"):
                    client_id = int(param1)
                    metric_type = param2
                    if client_id not in clients:
                        conn_socket.send("ERROR 404 [NOT FOUND]\n".encode())
                        continue
                    message = parse_metrics(client_id, metric_type)
                    conn_socket.send(message.encode())
                elif command == "END":
                    connection_alive = False
                    break
                else:
                    conn_socket.send("ERROR 400 [BAD REQUEST]\n".encode())
    except:
        pass
    finally:
        conn_socket.close()


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
                    "last_process": ""
                }
                threading.Thread(
                    target= client_handler,
                    args = (connection, id, addr),
                    daemon= True
                ).start()
                id += 1
            else:
                connection.send("ERROR 403 [FORBIDDEN]\n".encode())

        elif message.startswith("ADMIN"):
            (_, key) = message.strip().split(" ")
            if key == KEY:
                threading.Thread(
                    target = admin_handler,
                    args = (connection, addr),
                    daemon = True
                ).start()
            else:
                connection.send("ERROR 403 [FORBIDDEN]\n".encode())


# main
if __name__=='__main__':

   # UDP listener
   udpThread = threading.Thread(target=udp_discover, daemon=True)
   # TCP connection
   tcpThread = threading.Thread(target=connect_agent , args=(0, ), daemon=True)

   udpThread.start()
   tcpThread.start()

   udpThread.join()
   tcpThread.join()



