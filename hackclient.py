import socket
import pyautogui
import io
import struct
if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", 1337))

        while True:
            frame_buffer = io.BytesIO()
            screenshot = pyautogui.screenshot()
            screenshot.save(buffer, format="jpeg")

            frame_data = frame_buffer.getvalue()
            frame_size =len(frame_data)
            

            sock.sendall(struct.pack(">L", frame_size))
            sock.sendall(frame_data)
