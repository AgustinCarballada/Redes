import threading
from socket import *


SERVER_PORT = 6063
BROADCAST_IP = "255.255.255.255"
KEY = "server123"

connection_alive = False


def log_response(message, addr):
    if type(message) == bytes:
        print(f"[UDP] {message.decode().split("\n")[0]}, HOST: {addr}")
    else:
        print(f"[TCP] {message}, HOST: {addr}")


def list_agents(admin_tcp):
    admin_tcp.send("LIST_AGENTS\n".encode())


def get_proc(admin_tcp, id):
    admin_tcp.send(f"GET_PROC {id}\n".encode())


def get_metric(admin_tcp, id, type):
    admin_tcp.send(f"GET_METRIC {id} {type}\n".encode())


def end_connection(admin_tcp):
    admin_tcp.send(f"END\n".encode())


def response_thread(admin_tcp, addr):
    global connection_alive
    buffer = ""
    connection_alive = True
    try:
        while connection_alive:
            response = admin_tcp.recv(1024).decode()

            # TODO : lo mismo verificar con el profe
            if not response:
                raise

            buffer += response
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                log_response(message, addr)

    except Exception:
        connection_alive = False
        return



def udp_discover():
    client = socket(AF_INET, SOCK_DGRAM)
    client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    client.sendto("DISCOVER\n".encode(), (BROADCAST_IP, SERVER_PORT))
    message , (server_ip, server_port) = client.recvfrom(1024)
    addr = (server_ip, int(server_port))
    log_response(message, addr)

    message = message.decode()
    
    if message.startswith("SERVER"):
        (_, cpu_rate, mem_rate, tcp_port) = message.split(" ")
        global connection_alive

        # TCP connection
        admin_tcp = socket(AF_INET, SOCK_STREAM)
        admin_tcp.connect((server_ip, int(tcp_port)))
        connection_alive = True

        admin_tcp.send(f"ADMIN {KEY}\n".encode())
        message = admin_tcp.recv(1024).decode().split("\n")[0]
        log_response(message, (server_ip, server_port))

        if message.startswith("ADMIN_RESP"):
            return admin_tcp, (server_ip, server_port)


if __name__ == "__main__":

    socket, addr = udp_discover()
    t1 = threading.Thread(target=response_thread, args=(socket, addr), daemon=True)
    t1.start()

    while connection_alive:
        message = input().strip()
        partes = message.split(" ")
        command = partes[0]
        try:
            if command == "L":
                list_agents(socket)
            elif command == "M":
                if len(partes) != 3 or not partes[1].isdigit():
                    print("ERROR Formato invalido. Uso: M <id> <CPU|MEM>")
                    continue
                get_metric(socket, partes[1], partes[2])
            elif command == "P":
                if len(partes) != 2 or not partes[1].isdigit():
                    print("ERROR Formato invalido. Uso: P <id>")
                    continue
                get_proc(socket, partes[1])
            elif command == "END":
                end_connection(socket)
                break
            else:
                print("ERROR")
        except:
            print("ERROR")

    t1.join()
    socket.close()






