import socket
import threading
import pickle  # 导入pickle模块

def recvUntil(s, suffix):
    suffix = suffix.encode() if isinstance(suffix, str) else suffix
    ret = b""
    while True:
        c = s.recv(1)
        ret += c
        if ret.endswith(suffix):
            break
    return ret

def recvLine(s):
    line = recvUntil(s, "\n")
    try:
        # 反序列化数据
        return pickle.loads(line[:-1])  # 移除行尾的换行符
    except pickle.UnpicklingError:
        # 如果反序列化失败，返回原始字节数据
        return line

def sendLine(s, data):
    try:
        # 尝试序列化数据
        serialized_data = pickle.dumps(data)
    except TypeError:
        # 如果无法序列化，则假定数据已经是字节类型
        serialized_data = data
    s.sendall(serialized_data + b"\n")  # 发送序列化后的数据

def listen_on_port(handler, port):
    with socket.create_server(("", port)) as sock:
        while True:
            conn, addr = sock.accept()
            threading.Thread(
                target=handler,
                args=(
                    conn,
                    addr,
                ),
            ).start()

def connect_to(handler, port, ip="localhost"):
    with socket.create_connection((ip, port)) as sock:
        ret = handler(sock)
    return ret



if __name__ == "__main__":
    import sys

    def test_server(conn, addr):
        from_client = recvLine(conn)  # 接收客户端发送的数据
        # 进行任意的处理
        sendLine(conn, from_client)  # 返回处理结果给服务器（这里直接返回原数据为例）
        conn.close()
        return

    # 服务端监听socket端口
    PORT = 10001
    t1 = threading.Thread(target=listen_on_port, args=(test_server, PORT))
    t1.start()
    print(f"listening test server on {PORT} ...")

    # 客户端发送请求
    def handler(conn):
        sendLine(conn, "aa")  # 发送数据到服务器
        from_server = recvLine(conn)  # 接收服务器返回的数据
        return from_server

    print(connect_to(handler, PORT))
