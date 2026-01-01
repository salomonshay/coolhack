import socket

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", 1337))
        