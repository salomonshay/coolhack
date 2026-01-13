import socket
import pyautogui
import io
import struct
import threading
import json
import time
from pynput import mouse, keyboard

# --- Configuration ---
SERVER_IP = "10.0.0.17"
PORT = 8820

# Initialize Controllers
mouse_ctrl = mouse.Controller()
keyboard_ctrl = keyboard.Controller()


def receive_commands(sock):
    """
    Thread function to listen for commands from the server
    and execute them locally.
    """
    buffer = ""
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break

            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line: continue

                try:
                    event = json.loads(line)

                    # 1. Handle Mouse Events
                    if event["type"] == "mouse":
                        d = event["data"]
                        mouse_ctrl.position = (d["x"], d["y"])

                        btn_name = d["button"].split('.')[-1]
                        button = getattr(mouse.Button, btn_name, None)

                        if button:
                            if d["pressed"]:
                                mouse_ctrl.press(button)
                            else:
                                mouse_ctrl.release(button)

                    # 2. Handle Keyboard Events
                    elif event["type"] == "keyboard":
                        d = event["data"]
                        key_str = d["key"]

                        if key_str.startswith("Key."):
                            key_attr = key_str.split('.')[-1]
                            key = getattr(keyboard.Key, key_attr, None)
                        else:
                            key = key_str

                        if key:
                            if d["action"] == "press":
                                keyboard_ctrl.press(key)
                            else:
                                keyboard_ctrl.release(key)

                except json.JSONDecodeError:
                    pass  # Handle partial frames
                except Exception as e:
                    print(f"Command Error: {e}")

        except OSError:
            break


def start_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print(f"Connecting to {SERVER_IP}:{PORT}...")
        try:
            sock.connect((SERVER_IP, PORT))
            print("Connected.")
        except ConnectionRefusedError:
            print("Server not found. Make sure server is running first.")
            return

        # Start the receiver thread
        t = threading.Thread(target=receive_commands, args=(sock,), daemon=True)
        t.start()

        # Main Loop: Send Screenshots
        try:
            while True:
                # Capture screen
                screenshot = pyautogui.screenshot()

                # Compress to JPEG in memory
                frame_buffer = io.BytesIO()
                screenshot.save(frame_buffer, format="JPEG", quality=70)  # Quality 70 for speed
                frame_data = frame_buffer.getvalue()
                frame_size = len(frame_data)

                # Send size (4 bytes) then data
                sock.sendall(struct.pack(">L", frame_size))
                sock.sendall(frame_data)

                # Limit FPS slightly to prevent network flooding
                time.sleep(0.05)

        except (BrokenPipeError, ConnectionResetError):
            print("Server disconnected.")
        except KeyboardInterrupt:
            print("Stopping...")


if __name__ == "__main__":
    start_client()