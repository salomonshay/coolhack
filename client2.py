import socket
import json
from pynput import mouse, keyboard
import time

# --- Configuration ---
SERVER_IP = "127.0.0.1"
PORT = 5000

# Initialize Controllers
mouse_ctrl = mouse.Controller()
keyboard_ctrl = keyboard.Controller()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, PORT))

buffer = ""
print("Connected to server. Ready to receive commands...")

while True:
    data = client.recv(1024).decode()
    if not data:
        break

    buffer += data
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        time.sleep(0.1) 
        try:
            event = json.loads(line)
            
            # 1. Handle Mouse Events
            if event["type"] == "mouse":
                d = event["data"]
                # Move the mouse to the server's coordinates
                mouse_ctrl.position = (d["x"], d["y"])
                
                # Handle Clicking
                # Note: This assumes button names like 'Button.left'
                btn_name = d["button"].split('.')[-1] # extract 'left' from 'Button.left'
                button = getattr(mouse.Button, btn_name)
                
                if d["pressed"]:
                    mouse_ctrl.press(button)
                else:
                    mouse_ctrl.release(button)

            # 2. Handle Keyboard Events
            elif event["type"] == "keyboard":
                d = event["data"]
                key_str = d["key"]
                
                # Logic to determine if it's a special key (Key.esc) or a character ('a')
                if key_str.startswith("Key."):
                    key_attr = key_str.split('.')[-1]
                    key = getattr(keyboard.Key, key_attr)
                else:
                    key = key_str

                if d["action"] == "press":
                    keyboard_ctrl.press(key)
                else:
                    keyboard_ctrl.release(key)

        except Exception as e:
            print(f"Error replaying event: {e}")

client.close()