import tkinter as tk
from tkinter import messagebox
from colorbot import Colorbot
from settings import Settings
import pyautogui
import os
import threading

class AimbotGUI:
    def __init__(self, master):
        self.master = master
        master.title("Aimbot Control Panel")

        self.settings = Settings()
        self.monitor = pyautogui.size()
        self.center_x, self.center_y = self.monitor.width // 2, self.monitor.height // 2
        self.x_fov = self.settings.get_int('Aimbot', 'xFov')
        self.y_fov = self.settings.get_int('Aimbot', 'yFov')

        self.colorbot = Colorbot(
            self.center_x - self.x_fov // 2,
            self.center_y - self.y_fov // 2,
            self.x_fov,
            self.y_fov
        )

        self.is_running = False

        # UI Elements
        self.start_button = tk.Button(master, text="Start Aimbot", command=self.start_aimbot)
        self.start_button.pack()

        self.stop_button = tk.Button(master, text="Stop Aimbot", command=self.stop_aimbot)
        self.stop_button.pack()

        self.fov_label = tk.Label(master, text=f"FOV: {self.x_fov}x{self.y_fov}")
        self.fov_label.pack()

        # Add sliders for adjustable settings
        self.x_fov_scale = tk.Scale(master, from_=50, to=200, orient=tk.HORIZONTAL, label="X FOV", command=self.update_x_fov)
        self.x_fov_scale.set(self.x_fov)
        self.x_fov_scale.pack()

        self.y_fov_scale = tk.Scale(master, from_=50, to=200, orient=tk.HORIZONTAL, label="Y FOV", command=self.update_y_fov)
        self.y_fov_scale.set(self.y_fov)
        self.y_fov_scale.pack()

    def start_aimbot(self):
        if not self.is_running:
            os.system('cls')  # Clear console
            os.system('title Aimbot Running')
            print('Aimbot started')
            self.is_running = True
            # Start the aimbot logic in a separate thread
            self.colorbot.listen_in_background()  # Implement this method in Colorbot

    def stop_aimbot(self):
        if self.is_running:
            print('Aimbot stopped')
            self.colorbot.stop_listening()  # Implement this method in Colorbot
            self.is_running = False

    def update_x_fov(self, value):
        self.x_fov = int(value)
        self.fov_label.config(text=f"FOV: {self.x_fov}x{self.y_fov}")
        self.colorbot.x_fov = self.x_fov  # Ensure Colorbot uses updated FOV

    def update_y_fov(self, value):
        self.y_fov = int(value)
        self.fov_label.config(text=f"FOV: {self.x_fov}x{self.y_fov}")
        self.colorbot.y_fov = self.y_fov  # Ensure Colorbot uses updated FOV


if __name__ == "__main__":
    root = tk.Tk()
    gui = AimbotGUI(root)
    root.mainloop()
