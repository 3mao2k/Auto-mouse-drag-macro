import tkinter as tk
from tkinter import simpledialog, messagebox
from pynput import mouse, keyboard
import ctypes, threading, time, json, os

dragging = False
listener = None
kb_listener = None
enabled = True   # 🔥 Mở lên là Active luôn
step = 1
delay = 0.001
config_path = "guns_config.json"

guns_cfg = {}
current_gun = ""

# ---------- Windows SendInput ----------
PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

def move_mouse_rel(x, y):
    """Move chuột tương đối"""
    extra = ctypes.c_ulong(0)
    ii = Input_I()
    ii.mi = MouseInput(x, y, 0, 0x0001, 0, ctypes.pointer(extra))  # MOUSEEVENTF_MOVE
    command = Input(ctypes.c_ulong(0), ii)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

# ---------- Load & Save Config ----------
def load_config():
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                return data.get("guns", {})
        except:
            pass
    return {"M4": 2, "AKM": 3}

def save_config():
    data = {"guns": guns_cfg}
    with open(config_path, "w") as f:
        json.dump(data, f, indent=4)

# ---------- Auto (full-auto) ----------
def drag_down_auto():
    while dragging and enabled:
        move_mouse_rel(0, step)
        time.sleep(delay)

def on_click(x, y, button, pressed):
    global dragging
    if enabled and button == mouse.Button.left:
        if pressed:
            dragging = True
            t = threading.Thread(target=drag_down_auto, daemon=True)
            t.start()
        else:
            dragging = False

# ---------- Toggle CapsLock ----------
def toggle_enable():
    global enabled
    enabled = not enabled
    status_var.set("ON" if enabled else "OFF")
    status_label.config(fg="green" if enabled else "red")

def on_key(key):
    if key == keyboard.Key.caps_lock:
        toggle_enable()

# ---------- GUI Handlers ----------
def select_gun(event=None):
    global current_gun, step
    current_gun = gun_var.get()
    step = guns_cfg[current_gun]
    speed_scale.set(step)

def update_speed(val):
    global step
    step = int(val)
    guns_cfg[current_gun] = step
    save_config()

def add_new_gun():
    name = simpledialog.askstring("Thêm Súng Mới", "Nhập tên súng:")
    if not name:
        return
    if name in guns_cfg:
        messagebox.showerror("Lỗi", "Súng này đã tồn tại!")
        return
    guns_cfg[name] = 2
    gun_menu["menu"].add_command(label=name, command=tk._setit(gun_var, name, select_gun))
    save_config()
    messagebox.showinfo("Thành công", f"Đã thêm súng {name}!")

# ---------- GUI ----------
guns_cfg = load_config()
if not guns_cfg:
    guns_cfg = {"M4": 2, "AKM": 3}
    save_config()

current_gun = list(guns_cfg.keys())[0]
step = guns_cfg[current_gun]

root = tk.Tk()
root.title("Auto Drag Down (Auto Active)")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

tk.Label(frame, text="Status:").grid(row=0, column=0)
status_var = tk.StringVar(value="ON")  # 🔥 Active ngay từ đầu
status_label = tk.Label(frame, textvariable=status_var, fg="green")
status_label.grid(row=0, column=1)

add_btn = tk.Button(frame, text="Thêm Súng", width=22, command=add_new_gun)
add_btn.grid(row=1, column=0, columnspan=2, pady=5)

tk.Label(frame, text="Gun:").grid(row=2, column=0)
gun_var = tk.StringVar(value=current_gun)
gun_menu = tk.OptionMenu(frame, gun_var, *guns_cfg.keys(), command=select_gun)
gun_menu.grid(row=2, column=1)

tk.Label(frame, text="Lực kéo:").grid(row=3, column=0)
speed_scale = tk.Scale(frame, from_=1, to=10, orient="horizontal", command=update_speed)
speed_scale.set(step)
speed_scale.grid(row=3, column=1)

tk.Label(frame, text="(CapsLock = Bật/Tắt)").grid(row=4, column=0, columnspan=2, pady=5)

# ---------- Bắt sự kiện ngay khi mở ----------
listener = mouse.Listener(on_click=on_click)
listener.start()
kb_listener = keyboard.Listener(on_press=on_key)
kb_listener.start()

root.mainloop()
