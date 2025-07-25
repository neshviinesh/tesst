import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import random
import cv2
from PIL import Image, ImageTk
import socketio
from face_demo import recognize_faces_yolo  # your face-detection module

# ── Cooldown Configuration ────────────────────────────
COOLDOWN_SECONDS = 15
last_dot_time = 0

# ── Socket.IO client ─────────────────────────────────
sio = socketio.Client()

# ── Main window ───────────────────────────────────────
root = tk.Tk()
root.title("Proximity Alert System Demo")
root.geometry("1000x800")

# ── Status label ──────────────────────────────────────
status_label = tk.Label(root, text="Connecting to backend…", fg="blue",
                        font=("Helvetica", 12, "bold"))
status_label.pack(pady=5)

# ── Top frame: map + camera ───────────────────────────
top_frame = tk.Frame(root)
top_frame.pack(pady=5)

# Map canvas
canvas = tk.Canvas(top_frame, width=480, height=300)
canvas.pack(side="left", padx=10)

# Load and display the map background (map.png in same folder)
map_img = Image.open("map.png").resize((480, 300))
map_tk  = ImageTk.PhotoImage(map_img)
canvas.create_image(0, 0, image=map_tk, anchor="nw")
canvas.map_image = map_tk  # keep reference

# Static camera & user dots on top of map
camera_x, camera_y = 240, 140
canvas.create_oval(camera_x-10, camera_y-10, camera_x+10, camera_y+10,
                   fill="red")
canvas.create_text(camera_x, camera_y - 15, text="Camera",
                   font=("Helvetica", 10))
user_x_offset = 60
canvas.create_oval(camera_x+user_x_offset-7, camera_y-7,
                   camera_x+user_x_offset+7, camera_y+7, fill="green")
canvas.create_text(camera_x+user_x_offset, camera_y + 15,
                   text="User", font=("Helvetica", 10))

# Video feed
video_label = tk.Label(top_frame)
video_label.pack(side="left", padx=10)

# ── Alert label ────────────────────────────────────────
alert_label = tk.Label(root, text="No alerts yet", font=("Helvetica", 14),
                       fg="black")
alert_label.pack(pady=10)

# ── Log box ────────────────────────────────────────────
log_box = scrolledtext.ScrolledText(root, height=12, width=115,
                                    font=("Courier", 10), bg="black",
                                    fg="lime")
log_box.pack(padx=10, pady=10)

def append_log(msg: str):
    ts = time.strftime("%H:%M:%S")
    log_box.insert(tk.END, f"[{ts}] {msg}\n")
    log_box.see(tk.END)

def update_alert(msg: str):
    alert_label.config(text=msg, fg="red")

# ── Toast pop-up for alerts ────────────────────────────
def show_toast(message, duration=3000):
    toast = tk.Toplevel(root)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    tk.Label(toast, text=message, bg="yellow", fg="black",
             font=("Helvetica", 10, "bold"), bd=1, relief="solid"
    ).pack(padx=10, pady=5)
    # position near bottom-right of main window
    x = root.winfo_x() + root.winfo_width() - 220
    y = root.winfo_y() + root.winfo_height() - 120
    toast.geometry(f"+{x}+{y}")
    toast.after(duration, toast.destroy)

# ── Socket.IO event handlers ──────────────────────────
@sio.event
def connect():
    status_label.config(text="Connected to backend", fg="green")
    append_log("Connected to backend")

@sio.event
def disconnect():
    status_label.config(text="Disconnected", fg="red")
    append_log("Disconnected from backend")

@sio.on("log")
def on_log(data):
    append_log(data.get("message", ""))

@sio.on("alert")
def on_alert(data):
    append_log(data.get("message", "⚠️ Alert"))

# ── Detection visuals ─────────────────────────────────
detection_dot = None
detection_line = None

# ── Camera + face recognition ─────────────────────────
cap = cv2.VideoCapture("http://192.168.187.130:8080/video")  # or 0 for local webcam

def update_video():
    global detection_dot, detection_line, last_dot_time
    ret, frame = cap.read()
    if not ret:
        video_label.after(100, update_video)
        return

    # Shrink frame for display
    frame = cv2.resize(frame, (400, 300))
    detections = recognize_faces_yolo(frame)
    now = time.time()

    # Remove old dot/line each frame
    if detection_dot:
        canvas.delete(detection_dot)
        detection_dot = None

    # Handle first recognized face per cooldown interval
    for (x1, y1, x2, y2, name) in detections:
        if name == "Unknown":
            continue

        if now - last_dot_time >= COOLDOWN_SECONDS:
            # Draw new dot & line
            det_x = random.randint(100, 200)
            det_y = random.randint(50, 250)
            detection_dot = canvas.create_oval(det_x-7, det_y-7,
                                              det_x+7, det_y+7,
                                              fill="blue")
            detection_line = canvas.create_line(camera_x, camera_y,
                                                det_x, det_y,
                                                fill="blue", width=2)
            canvas.create_text(det_x, det_y-10, text=name,
                               font=("Helvetica", 9))

            update_alert(f"Alert sent to User: {name} was detected 125 meters from the Camera A1")
            append_log(f"Proximity alert sent to user for {name}")
            show_toast(f"{name} is nearby!")
            last_dot_time = now
        break  # only the first recognized face

    # Draw bounding boxes for recognized faces
    for (x1, y1, x2, y2, name) in detections:
        if name == "Unknown":
            continue
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (255, 255, 255), 2)

    # Display the video frame
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.config(image=imgtk)

    video_label.after(30, update_video)

# ── GPS Simulation ────────────────────────────────────
def simulate_gps():
    lat = 37.6019 + random.uniform(-0.005, 0.005)
    lng = -0.9807 + random.uniform(-0.005, 0.005)
    append_log(f"[GPS] Simulated location: ({lat:.6f}, {lng:.6f})")
    root.after(15000, simulate_gps)

# ── Start Socket.IO in background ─────────────────────
def start_socketio():
    try:
        sio.connect("http://localhost:8000")
        sio.wait()
    except Exception as e:
        append_log(f"Socket connection error: {e}")
        status_label.config(text="Connection failed", fg="red")

threading.Thread(target=start_socketio, daemon=True).start()

# ── Begin loops ────────────────────────────────────────
update_video()
root.after(15000, simulate_gps)
root.mainloop()
cap.release()

