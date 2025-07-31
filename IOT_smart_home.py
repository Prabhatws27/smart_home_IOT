import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import requests
import geocoder
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------- Sensor Simulation ----------
def get_temperature():
    return round(random.uniform(18.0, 30.0), 1)

def get_humidity():
    return round(random.uniform(40.0, 80.0), 1)

def detect_smoke():
    return random.choice([True, False, False])

def detect_motion():
    return random.choice([True, False, False, False])

def get_location_and_weather():
    try:
        g = geocoder.ip('me')
        location = g.city + ", " + g.country if g.city else "Unknown Location"
        response = requests.get("https://wttr.in/?format=j1")
        temp = response.json()['current_condition'][0]['temp_C']
        return location, f"{temp} °C"
    except:
        return "Location Unknown", "N/A"

# ---------- Device Model ----------
class Device:
    def __init__(self, name):
        self.name = name
        self.on = False

    def activate(self):
        self.on = True

    def deactivate(self):
        self.on = False

    def is_on(self):
        return self.on

# ---------- Smart Controller ----------
class SmartController:
    def __init__(self):
        self.heater = Device("Heater")
        self.window_panels = Device("Window Panels")
        self.exhaust_fan = Device("Exhaust Fan")
        self.smoke_alarm = Device("Smoke Alarm")
        self.cameras = {
            "kitchen": Device("Kitchen Camera"),
            "bedroom": Device("Bedroom Camera"),
            "hallway": Device("Hallway Camera"),
            "door": Device("Door Camera")
        }
        self.motion_detected = False
        self.IDEAL_TEMP = 24
        self.HUMIDITY_HIGH = 55

    def evaluate(self, temperature, humidity, smoke, motion):
        logs = []
        self.motion_detected = motion

        if smoke:
            self.smoke_alarm.activate()
            logs.append("🚨 Smoke detected! Activating smoke alarm.")
        else:
            self.smoke_alarm.deactivate()

        if humidity > self.HUMIDITY_HIGH:
            if not self.exhaust_fan.is_on():
                logs.append("Exhaust fan activated due to high humidity.")
            self.exhaust_fan.activate()
        else:
            if self.exhaust_fan.is_on():
                logs.append("Exhaust fan deactivated.")
            self.exhaust_fan.deactivate()

        if motion:
            if temperature < self.IDEAL_TEMP - 1:
                if not self.heater.is_on():
                    logs.append("Heater ON to reach ideal temperature (24°C).")
                self.heater.activate()
                self.window_panels.deactivate()
            elif temperature > self.IDEAL_TEMP + 1:
                if not self.window_panels.is_on():
                    logs.append("Window panels OPEN to reduce temperature to 24°C.")
                self.window_panels.activate()
                self.heater.deactivate()
            else:
                if self.heater.is_on():
                    logs.append("Heater OFF - temperature within range.")
                if self.window_panels.is_on():
                    logs.append("Window panels CLOSED - temperature within range.")
                self.heater.deactivate()
                self.window_panels.deactivate()
        else:
            if self.heater.is_on() or self.window_panels.is_on():
                logs.append("No motion detected: turning off temp-control devices.")
            self.heater.deactivate()
            self.window_panels.deactivate()

        if motion:
            logs.append("🔍 Motion detected: Someone is present.")

        logs.append("Managing indoor cameras.")
        if motion:
            for name, cam in self.cameras.items():
                if name != "door":
                    if cam.is_on():
                        logs.append(f"{name.capitalize()} camera OFF (privacy - motion detected).")
                    cam.deactivate()
            if not self.cameras["door"].is_on():
                logs.append("Door camera ON (motion detected).")
            self.cameras["door"].activate()
        else:
            for name, cam in self.cameras.items():
                if not cam.is_on():
                    logs.append(f"{name.capitalize()} camera ON (no motion - security mode).")
                cam.activate()

        return {
            "heater": self.heater.is_on(),
            "window_panels": self.window_panels.is_on(),
            "exhaust_fan": self.exhaust_fan.is_on(),
            "smoke_alarm": self.smoke_alarm.is_on(),
            "alert_smoke": smoke,
            "motion_detected": motion,
            "logs": logs,
            "cameras": {name: cam.is_on() for name, cam in self.cameras.items()}
        }

# ---------- GUI ----------
class SmartHomeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Home IoT System")
        self.root.geometry("1000x720")
        self.root.configure(bg="#0f1117")

        self.controller = SmartController()
        self.occupied = tk.BooleanVar(value=True)
        self.location, self.external_temp = get_location_and_weather()

        self.temp_history = []
        self.hum_history = []

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Card.TFrame", background="#1c1f26", relief="groove", borderwidth=2)
        style.configure("TLabel", background="#1c1f26", foreground="#e0e0e0", font=("Helvetica Neue", 11))
        style.configure("Header.TLabel", font=("Helvetica Neue", 16, "bold"), foreground="#00ffe1", background="#0f1117")
        style.configure("Alert.TLabel", font=("Helvetica Neue", 12, "bold"), foreground="#ff4d4d", background="#0f1117")
        style.configure("TCheckbutton", background="#1c1f26", foreground="white", font=("Helvetica Neue", 11))

        self.build_gui()
        self.update()

    def build_gui(self):
        ttk.Label(self.root, text="SMART HOME IOT SIMULATION", style="Header.TLabel").pack(pady=10)

        fig, self.ax = plt.subplots(figsize=(5, 2.5))
        self.canvas_plot = FigureCanvasTkAgg(fig, master=self.root)
        self.canvas_plot.get_tk_widget().pack(pady=5)
        self.ax.set_title("Temperature and Humidity Trends")
        self.ax.set_xlabel("Time Steps")
        self.ax.set_ylabel("Values")

        device_frame = ttk.Frame(self.root, style="Card.TFrame")
        device_frame.pack(pady=5, padx=20, fill="x")
        ttk.Label(device_frame, text="Devices:").pack(anchor="w", padx=10)
        self.device_labels = {}
        for name in ["Heater", "Window Panels", "Exhaust Fan", "Smoke Alarm"]:
            label = ttk.Label(device_frame, text=f"{name}: OFF")
            label.pack(anchor="w", padx=20, pady=2)
            self.device_labels[name.lower().replace(" ", "_")] = label

        manual_frame = ttk.Frame(self.root, style="Card.TFrame")
        manual_frame.pack(pady=5, padx=20, fill="x")
        ttk.Label(manual_frame, text="Manual Overrides:").pack(anchor="w", padx=10)
        ttk.Checkbutton(manual_frame, text="Room Occupied", variable=self.occupied, style="TCheckbutton").pack(side="left", padx=10)
        ttk.Button(manual_frame, text="Toggle Heater", command=self.toggle_heater).pack(side="left", padx=10, pady=5)
        ttk.Button(manual_frame, text="Toggle Window Panels", command=self.toggle_windows).pack(side="left", padx=10, pady=5)
        ttk.Button(manual_frame, text="Toggle Exhaust Fan", command=self.toggle_exhaust).pack(side="left", padx=10, pady=5)
        ttk.Button(manual_frame, text="Toggle Smoke Alarm", command=self.toggle_smoke_alarm).pack(side="left", padx=10, pady=5)

        camera_frame = ttk.Frame(self.root, style="Card.TFrame")
        camera_frame.pack(pady=5, padx=20, fill="x")
        ttk.Label(camera_frame, text="Cameras:").pack(anchor="w", padx=10)
        self.camera_labels = {}
        for name in ["Kitchen", "Bedroom", "Hallway", "Door"]:
            key = name.lower()
            label = ttk.Label(camera_frame, text=f"{name} Camera: OFF")
            label.pack(anchor="w", padx=20)
            self.camera_labels[key] = label

        sensor_frame = ttk.Frame(self.root, style="Card.TFrame")
        sensor_frame.pack(pady=5, padx=20, fill="x")
        ttk.Label(sensor_frame, text="Sensor Status:").pack(anchor="w", padx=10)
        self.sensor_labels = {}
        for name in ["Temperature", "Humidity", "Smoke", "Alarm", "Motion"]:
            row = ttk.Frame(sensor_frame, style="Card.TFrame")
            row.pack(anchor="w", padx=20, pady=2)
            lbl = ttk.Label(row, text=f"{name} Sensor")
            lbl.pack(side="left", padx=5)
            canvas = tk.Canvas(row, width=15, height=15, bg="#1c1f26", highlightthickness=0)
            circle = canvas.create_oval(2, 2, 13, 13, fill="green")
            canvas.pack(side="left")
            self.sensor_labels[name.lower()] = (canvas, circle)

        ttk.Label(self.root, text=f"Location: {self.location} | Outdoor Temp: {self.external_temp}").pack(pady=5)
        self.alert_label = ttk.Label(self.root, text="", style="Alert.TLabel")
        self.alert_label.pack(pady=6)

        log_frame = ttk.Frame(self.root, style="Card.TFrame")
        log_frame.pack(pady=5, padx=20, fill="both", expand=True)
        self.log_box = tk.Text(log_frame, height=8, bg="#12151c", fg="#00FFAA", font=("Consolas", 10), borderwidth=0)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_box.insert(tk.END, "System Log:\n")
        self.log_box.config(state=tk.DISABLED)

    def log_event(self, message):
        timestamp = time.strftime("%I:%M:%S %p")
        entry = f"[{timestamp}] {message}\n"
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, entry)
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def toggle_heater(self):
        self.controller.heater.activate() if not self.controller.heater.is_on() else self.controller.heater.deactivate()
        self.log_event(f"Manual: Heater turned {'ON' if self.controller.heater.is_on() else 'OFF'}")

    def toggle_windows(self):
        self.controller.window_panels.activate() if not self.controller.window_panels.is_on() else self.controller.window_panels.deactivate()
        self.log_event(f"Manual: Window Panels {'Opened' if self.controller.window_panels.is_on() else 'Closed'}")

    def toggle_exhaust(self):
        self.controller.exhaust_fan.activate() if not self.controller.exhaust_fan.is_on() else self.controller.exhaust_fan.deactivate()
        self.log_event(f"Manual: Exhaust Fan turned {'ON' if self.controller.exhaust_fan.is_on() else 'OFF'}")

    def toggle_smoke_alarm(self):
        self.controller.smoke_alarm.activate() if not self.controller.smoke_alarm.is_on() else self.controller.smoke_alarm.deactivate()
        self.log_event(f"Manual: Smoke Alarm turned {'ON' if self.controller.smoke_alarm.is_on() else 'OFF'}")

    def update_plot(self):
        self.ax.clear()
        self.ax.plot(self.temp_history[-20:], label="Temperature (°C)", color="red")
        self.ax.plot(self.hum_history[-20:], label="Humidity (%)", color="blue")
        self.ax.set_title("Temperature and Humidity Trends")
        self.ax.set_xlabel("Time Steps")
        self.ax.set_ylabel("Values")
        self.ax.legend()
        self.canvas_plot.draw()

    def update(self):
        temp = get_temperature()
        humidity = get_humidity()
        smoke = detect_smoke()
        motion = detect_motion()

        self.temp_history.append(temp)
        self.hum_history.append(humidity)

        state = self.controller.evaluate(temp, humidity, smoke, motion)

        for key, label in self.device_labels.items():
            val = state[key]
            if key == "window_panels":
                label.config(text=f"Window Panels: {'Open' if val else 'Closed'}")
            else:
                label.config(text=f"{key.replace('_', ' ').title()}: {'ON' if val else 'OFF'}")

        self.sensor_labels['temperature'][0].itemconfig(self.sensor_labels['temperature'][1], fill="green")
        self.sensor_labels['humidity'][0].itemconfig(self.sensor_labels['humidity'][1], fill="green")
        self.sensor_labels['smoke'][0].itemconfig(self.sensor_labels['smoke'][1], fill="red" if smoke else "green")
        self.sensor_labels['alarm'][0].itemconfig(self.sensor_labels['alarm'][1], fill="red" if state['smoke_alarm'] else "green")
        self.sensor_labels['motion'][0].itemconfig(self.sensor_labels['motion'][1], fill="red" if motion else "green")

        self.log_event(f"Sensor Check: Temp={temp}C, Humidity={humidity}%, Smoke={'Yes' if smoke else 'No'}, Motion={'Yes' if motion else 'No'}")

        if state["alert_smoke"]:
            self.alert_label.config(text="🚨 ALERT: Smoke Detected!")
            messagebox.showwarning("Smoke Alert", "Smoke has been detected! Smoke alarm activated.")
        else:
            self.alert_label.config(text="")

        for key, label in self.camera_labels.items():
            status = state["cameras"][key]
            label.config(text=f"{key.capitalize()} Camera: {'ON' if status else 'OFF'}")

        for log in state["logs"]:
            self.log_event(log)

        self.update_plot()
        self.root.after(7000, self.update)

# ---------- Run App ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = SmartHomeGUI(root)
    root.mainloop()
