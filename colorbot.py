import cv2
import numpy as np
import win32api
import win32con
import random
import threading
import time
from capture import Capture
from mouse import Mouse
from settings import Settings


class Colorbot:
    """
    The Colorbot class handles screen capturing, color detection, and mouse control.
    It supports aiming at specific colors on the screen and triggering actions when
    the color is within a defined region.
    """
    def __init__(self, x, y, x_fov, y_fov):
        """
        Initializes the Colorbot with screen capture parameters.

        Args:
            x (int): X-coordinate for the capture starting point.
            y (int): Y-coordinate for the capture starting point.
            x_fov (int): Width of the capture area.
            y_fov (int): Height of the capture area.
        """
        self.x = x
        self.y = y
        self.x_fov = x_fov
        self.y_fov = y_fov
        self.running = False
        self.capturer = Capture(x, y, x_fov, y_fov)
        self.mouse = Mouse()
        self.settings = Settings()
        # Strafe delay range (in milliseconds)
        self.min_strafe_delay = 200  # Minimum strafe delay
        self.max_strafe_delay = 400  # Maximum strafe delay

        # Color detection settings (HSV)
        self.lower_color = np.array([45, 150, 230])
        self.upper_color = np.array([55, 195, 255])

        # Aimbot settings
        self.aim_enabled = self.settings.get_boolean('Aimbot', 'Enabled')
        self.aim_key = int(self.settings.get('Aimbot', 'toggleKey'), 16)
        self.x_speed = self.settings.get_float('Aimbot', 'xSpeed')
        self.y_speed = self.settings.get_float('Aimbot', 'ySpeed')
        self.x_fov = self.settings.get_int('Aimbot', 'xFov')
        self.y_fov = self.settings.get_int('Aimbot', 'yFov')
        self.target_offset = self.settings.get_float('Aimbot', 'targetOffset')

        # Triggerbot settings
        self.trigger_enabled = self.settings.get_boolean('Triggerbot', 'Enabled')
        self.trigger_key = int(self.settings.get('Triggerbot', 'toggleKey'), 16)
        self.min_delay = self.settings.get_int('Triggerbot', 'minDelay')
        self.max_delay = self.settings.get_int('Triggerbot', 'maxDelay')
        self.x_range = self.settings.get_int('Triggerbot', 'xRange')
        self.y_range = self.settings.get_int('Triggerbot', 'yRange')

        # Auto-Strafe settings
        self.auto_strafe_enabled = False
        self.strafe_key = int(self.settings.get('AutoStrafe', 'toggleKey'), 16)
        self.strafe_speed = self.settings.get_float('AutoStrafe', 'xSpeed')
        self.strafe_delay = self.settings.get_int('AutoStrafe', 'strafingDelay')

        # Precomputed values
        self.kernel = np.ones((3, 3), np.uint8)
        self.screen_center = (self.x_fov // 2, self.y_fov // 2)


    def listen_aimbot(self):
        """
        Continuously listens for the aimbot key press and processes aiming.
        """
        while True:
            if win32api.GetAsyncKeyState(self.aim_key) < 0:
                self.process("move")
            time.sleep(0.01)  # Small sleep to prevent high CPU usage

    def listen_triggerbot(self):
        """
        Continuously listens for the triggerbot key press and processes clicking.
        """
        while True:
            if win32api.GetAsyncKeyState(self.trigger_key) < 0:
                self.process("click")
            time.sleep(0.01)  # Small sleep to prevent high CPU usage

    def listen_auto_strafe(self):
        while True:
            if win32api.GetAsyncKeyState(self.strafe_key) < 0:
                self.toggle_auto_strafe()
                time.sleep(0.3)  # Prevent toggling too fast

    def toggle_auto_strafe(self):
        """
        Toggles the auto-strafe on and off. Starts or stops the strafing loop as needed.
        """
        self.auto_strafe_enabled = not self.auto_strafe_enabled
        print(f"Auto-strafe {'enabled' if self.auto_strafe_enabled else 'disabled'}")

        if self.auto_strafe_enabled:
            threading.Thread(target=self.auto_strafe).start()

    def press_key(self, key_code):
        """
        Simulates a key press using win32api.
        """
        win32api.keybd_event(key_code, 0, 0, 0)

    def release_key(self, key_code):
        """
        Simulates a key release using win32api.
        """
        win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)

    def auto_strafe(self):
        """
        Continuously strafes left and right using A and D keys while auto-strafe is enabled.
        Pauses when A or D is held down.
        """
        while self.auto_strafe_enabled:
            if win32api.GetAsyncKeyState(0x41) < 0 or win32api.GetAsyncKeyState(0x44) < 0:
                # If A or D is held down, pause strafing
                #time.sleep(0.1)  # Add a small delay to reduce CPU usage
                continue
            # Generate a random strafe delay
            strafe_delay = random.uniform(self.min_strafe_delay, self.max_strafe_delay) / 1000.0
            # Strafe left (A key)
            self.press_key(0x41)  # Using 0x41 for 'A'
            time.sleep(strafe_delay)
            # Stop pressing A key
            self.release_key(0x41)
            if win32api.GetAsyncKeyState(0x41) < 0 or win32api.GetAsyncKeyState(0x44) < 0:
                # If A or D is held down, pause strafing
                #time.sleep(0.1)  # Add a small delay to reduce CPU usage
                continue
            # Strafe right (D key)
            self.press_key(0x44)  # Using 0x44 for 'D'
            time.sleep(strafe_delay)
            # Stop pressing D key
            self.release_key(0x44)

    def listen(self):
        """
        Initializes listeners for aimbot, triggerbot, and auto-strafe functionalities.
        """
        if self.aim_enabled:
            threading.Thread(target=self.listen_aimbot).start()
        if self.trigger_enabled:
            threading.Thread(target=self.listen_triggerbot).start()
        threading.Thread(target=self.listen_auto_strafe).start()

    def process(self, action):
        """
        Processes the captured screen to detect the specified color and performs actions based on the detected target.

        Args:
            action (str): The action to perform, either "move" to move the mouse or "click" to trigger a click.
        """
        # Convert the captured screen to HSV color space
        hsv = cv2.cvtColor(self.capturer.get_screen(), cv2.COLOR_BGR2HSV)

        # Create a binary mask where detected colors are white, and everything else is black
        mask = cv2.inRange(hsv, self.lower_color, self.upper_color)

        # Dilate the mask to make detected regions more prominent
        dilated = cv2.dilate(mask, self.kernel, iterations=5)

        # Apply thresholding to get a binary image
        thresh = cv2.threshold(dilated, 60, 255, cv2.THRESH_BINARY)[1]

        # Find contours in the binary image
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Process the detected contours
        if contours:
            min_distance = float('inf')
            closest_center = None

            for contour in contours:
                # Find the contour closest to the center of the screen using moments
                moments = cv2.moments(contour)
                if moments['m00'] != 0:  # Avoid division by zero
                    center = (int(moments['m10'] / moments['m00']), int(moments['m01'] / moments['m00']))
                    distance = np.sqrt((center[0] - self.screen_center[0]) ** 2 + (center[1] - self.screen_center[1]) ** 2)

                    # Update the closest center if the distance is smaller
                    if distance < min_distance:
                        min_distance = distance
                        closest_center = center

            if closest_center is not None:
                # Get the coordinates of the closest center and apply target offset
                cX, cY = closest_center
                cY -= int(self.target_offset)

                if action == "move":
                    # Calculate the difference between the center of the screen and the detected target
                    x_diff = cX - self.screen_center[0]
                    y_diff = cY - self.screen_center[1]

                    # Move the mouse towards the target
                    self.mouse.move(self.x_speed * x_diff, self.y_speed * y_diff)

                elif action == "click":
                    # Check if the detected target is within the trigger range
                    if (abs(cX - self.screen_center[0]) <= self.x_range and
                        abs(cY - self.screen_center[1]) <= self.y_range):
                        # Random delay before triggering a click
                        time.sleep(random.uniform(self.min_delay / 1000.0, self.max_delay / 1000.0))
                        self.mouse.click()