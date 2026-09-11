import datetime


def print_response(message, addr):
    if type(message) == bytes:
        print(f"[UDP] {message.decode().split("\n")[0]}, HOST: {addr}")
    else:
        print(f"[TCP] {message}, HOST: {addr}")


def parse_admin_message(message):
    parts = message.split(" ")
    if len(parts) == 1:
        params = (parts[0], "", "")
    elif len(parts) == 2:
        params = (parts[0], parts[1], "")
    else:
        params = (parts[0], parts[1], parts[2])

    if params[0] == "END":
        return "END\n"
    elif params[0] == "L":
        return "LIST_AGENTS\n"
    elif params[0] == "P":
        return f"GET_PROC {params[1]}\n"
    elif params[0] == "M":
        return f"GET_METRIC {params[1]} {params[2]}\n"
    else:
        return f"{message}\n"


def print_response(message, addr):
    if type(message) == bytes:
        print(f"[UDP] {message.decode().split("\n")[0][:1024]}, HOST: {addr}")
    else:
        print(f"[TCP] {message[:1024]}, HOST: {addr}")


def update_value(array, value):
    for i in range(9, 0, -1):
        array[i] = array[i - 1]
    array[0] = value
    return array


def parse_params(message):
    parts = message.split(" ")
    command = parts[0]
    if command == "PROC":
        return (command, " ".join(parts[1:]), "")
    parts += ["", ""]
    return (command, parts[1], parts[2])


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


def document_log(client_id, addr, param1, param2):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("LOG_DOCUMENTATION", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] ALERT {param1}:{param2}, CLIENT:{client_id}, HOST = {addr}\n")