import threading
from socket import *


SERVER_PORT = 6063
BROADCAST_IP = "255.255.255.255"
KEY = "server123"

connection_alive = False


def log_response(message, addr):
    print(message, addr)


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
            data = admin_tcp.recv(1024).decode()
            if not data:
                admin_tcp.send("ERROR\n".encode())
                continue
            # TODO : lo mismo verificar con el profe
            buffer += data
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                log_response(message, addr)
    except Exception:
        return
    finally:
        connection_alive = False


def udp_discover():
    client = socket(AF_INET, SOCK_DGRAM)
    client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    client.sendto("DISCOVER\n".encode(), (BROADCAST_IP, SERVER_PORT))
    message , (server_ip, server_port) = client.recvfrom(1024)
    message = message.decode()
    log_response(message, (server_ip, server_port))
    
    if message.startswith("SERVER"):
        (_, cpu_rate, mem_rate, tcp_port) = message.split(" ")
        global connection_alive

        # TCP connection
        admin_tcp = socket(AF_INET, SOCK_STREAM)
        admin_tcp.connect((server_ip, int(tcp_port)))
        connection_alive = True

        admin_tcp.send(f"ADMIN {KEY}\n".encode())
        message = admin_tcp.recv(1024)
        log_response(message, (server_ip, server_port))

        if message.decode().startswith("ADMIN_RESP"):
            return admin_tcp, (server_ip, server_port)


if __name__ == "__main__":

    socket, addr = udp_discover()
    t1 = threading.Thread(target=response_thread, args=(socket, addr), daemon=True)
    t1.start()

    while connection_alive:
        message = input()
        try:
            if message.startswith("L"):
                list_agents(socket)
            elif message.startswith("M"):
                (_, agent_id, metric) = message.split(" ")
                get_metric(socket, agent_id, metric)
            elif message.startswith("P"):
                (_, agent_id) = message.split(" ")
                get_proc(socket, agent_id)
            elif message == "END":
                end_connection(socket)
                break
            else:
                print("ERROR")
        except:
            print("ERROR")

    t1.join()
    socket.close()






