import socket
import threading
import pickle
import struct


def recvAll(s, length):
    """接收指定长度的数据"""
    data = b""
    while len(data) < length:
        more = s.recv(length - len(data))
        if not more:
            raise EOFError(
                "socket closed {} bytes into a {}-byte message".format(
                    len(data), length
                )
            )
        data += more
    return data


def recvLine(s):
    """接收一行数据，以长度为前缀"""
    # 首先接收4个字节的长度信息
    lengthbuf = recvAll(s, 4)
    (length,) = struct.unpack("!I", lengthbuf)
    line = recvAll(s, length)

    try:
        # 反序列化数据
        return pickle.loads(line)
    except pickle.UnpicklingError:
        # 如果反序列化失败，返回原始字节数据
        print("r pickle error", line)
        return line


def sendLine(s, data):
    """发送一行数据，以长度为前缀"""
    try:
        # 尝试序列化数据
        serialized_data = pickle.dumps(data)
    except TypeError:
        # 如果无法序列化，则假定数据已经是字节类型
        serialized_data = data
        print("s pickle error", data)

    # 发送数据长度信息
    length = len(serialized_data)
    s.sendall(struct.pack("!I", length))
    # 发送数据
    s.sendall(serialized_data)


def listen_on_port(handler, port, isAsync=True):
    with socket.create_server(("", port)) as sock:
        while True:
            conn, addr = sock.accept()
            # 异步处理
            if isAsync:
                threading.Thread(
                    target=handler,
                    args=(
                        conn,
                        addr,
                    ),
                ).start()
            # 串行处理
            else:
                ret = handler(conn, addr)
                if ret == "STOP":
                    break


def connect_to(handler, port, ip="localhost"):
    with socket.create_connection((ip, port)) as sock:
        ret = handler(sock)
    return ret


if __name__ == "__main__":

    def test_server(conn, addr):
        from_client = recvLine(conn)  # 接收客户端发送的数据
        print(from_client)
        # 进行任意的处理
        sendLine(conn, from_client)  # 返回处理结果给服务器（这里直接返回原数据为例）
        conn.close()

    # 服务端监听socket端口
    PORT = 44445
    t1 = threading.Thread(target=listen_on_port, args=(test_server, PORT))
    t1.start()
    print(f"listening test server on {PORT} ...")

    # 客户端发送请求
    # def handler(conn):
    #     sendLine(conn, "aa")  # 发送数据到服务器
    #     from_server = recvLine(conn)  # 接收服务器返回的数据
    #     return from_server

    # print(connect_to(handler, PORT))
