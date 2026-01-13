import socket
import struct
import io
import json
import threading
import cv2
import numpy as np
from PIL import Image
from pynput import keyboard, mouse

HOST = "0.0.0.0"
PORT = 8820

# Lock to ensure thread-safe sending
send_lock = threading.Lock()

def send_event(sock, event_type, data):
    """Serialize and send an event to the client safely."""
    message = {
        "type": event_type,
        "data": data
    }
    try:
        payload = (json.dumps(message) + "\n").encode()
        with send_lock:
            sock.sendall(payload)
    except OSError:
        pass # Client likely disconnected

def start_input_listeners(conn):
    """Starts pynput listeners to capture server-side inputs."""
    
    def mouse_on_click(x, y, button, pressed):
        send_event(conn, "mouse", {
            "x": x, "y": y,
            "button": str(button),
            "pressed": pressed
        })

    def on_press(key):
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        send_event(conn, "keyboard", {"key": k, "action": "press"})

    def on_release(key):
        send_event(conn, "keyboard", {"key": str(key), "action": "release"})

    # Listeners are non-blocking by default in pynput
    m_listener = mouse.Listener(on_click=mouse_on_click)
    k_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    
    m_listener.start()
    k_listener.start()
    return m_listener, k_listener

def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    print(f"Server listening on {HOST}:{PORT}...")

    conn, addr = sock.accept()
    print(f"Client connected: {addr}")

    # Start capturing input on server and sending to client
    m_list, k_list = start_input_listeners(conn)

    data = b""
    payload_size = struct.calcsize(">L")

    try:
        while True:
            # 1. Read message length (4 bytes)
            while len(data) < payload_size:
                packet = conn.recv(4096)
                if not packet: break
                data += packet

            if len(data) < payload_size:
                break 

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]

            # 2. Read the image data based on length
            while len(data) < msg_size:
                data += conn.recv(4096)

            frame_data = data[:msg_size]
            data = data[msg_size:]

            # 3. Process and Display Image using OpenCV
            # (CV2 is much faster/smoother than PIL for streams)
            image_stream = io.BytesIO(frame_data)
            image = Image.open(image_stream)
            frame = np.array(image)
            
            # Convert RGB (PIL) to BGR (OpenCV)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            cv2.imshow('Remote Desktop', frame)
            
            # Exit loop if 'q' is pressed in the window
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing connection...")
        m_list.stop()
        k_list.stop()
        conn.close()
        sock.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    start_server()