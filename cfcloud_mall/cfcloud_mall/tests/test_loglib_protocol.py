import socket
import threading
import time

from cfcloud_mall.libs.loglib.protocol import ProtocolCodec


def start_server(host='127.0.0.1', port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        s.setblocking(True)
        print(f"Server listening on {host}:{port}")
        conn, addr = s.accept()
        codec = ProtocolCodec()
        with conn:
            print(f"Connected by {addr}")
            while True:
                time.sleep(0.1)
                data = conn.recv(1024)
                if not data:
                    break
                rs = codec.decode(data)
                print(f"Received: {rs}")

def start_client(host='127.0.0.1', port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        messages = ["Hello", "World", "This", "is", "a", "test"]
        while True:
            for message in messages:
                message = message + f'发送：{time.ctime(time.time())}'
                s.send(ProtocolCodec.encode(message))
                time.sleep(0.001)
                s.send('俺是个大帅哥'.encode())# 添加延迟以模拟粘包

if __name__ == "__main__":
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()
    t2=threading.Thread(target=start_client, daemon=True)
    t2.start()
    thread.join()