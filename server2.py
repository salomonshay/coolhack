from pynput import keyboard, mouse
import socket
import json

HOST = "0.0.0.0"
PORT = 5000

# Create socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Waiting for client...")
conn, addr = server.accept()
print("Client connected:", addr)

def send_event(event_type, data):
    message = {
        "type": event_type,
        "data": data
    }
    conn.sendall((json.dumps(message) + "\n").encode())

def mouse_on_click(x, y, button, pressed):
    send_event("mouse", {
        "x": x,
        "y": y,
        "button": str(button),
        "pressed": pressed
    })

def on_press(key):
    try:
        send_event("keyboard", {
            "key": key.char,
            "action": "press"
        })
    except AttributeError:
        send_event("keyboard", {
            "key": str(key),
            "action": "press"
        })

def on_release(key):
    send_event("keyboard", {
        "key": str(key),
        "action": "release"
    })

    if key == keyboard.Key.esc:
        print("ESC pressed, stopping")
        keyboard_listener.stop()
        mouse_listener.stop()
        conn.close()
        server.close()

keyboard_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release
)

mouse_listener = mouse.Listener(
    on_click=mouse_on_click
)

keyboard_listener.start()
mouse_listener.start()

keyboard_listener.join()
mouse_listener.join()
