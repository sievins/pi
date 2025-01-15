#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import subprocess

# BCM pin numbering
LED_PIN = 26       # LED with resistor on GPIO26
BUTTON_PIN = 27    # Momentary button on GPIO27

def get_pihole_status():
    """
    Returns True if Pi-hole blocking is enabled, otherwise False.
    This checks Pi-hole's actual status rather than relying on a local variable.
    """
    try:
        completed_process = subprocess.run(
            ["pihole", "status"], capture_output=True, text=True
        )
        output = completed_process.stdout.lower()

        if "pi-hole blocking is enabled" in output:
            return True
        else:
            return False

    except Exception as e:
        print(f"Error checking Pi-hole status: {e}")
        # Default to False if we can't read the status
        return False

def update_led_state(is_enabled):
    """
    Turn the LED on if Pi-hole is enabled, off if disabled.
    """
    if is_enabled:
        GPIO.output(LED_PIN, GPIO.HIGH)
    else:
        GPIO.output(LED_PIN, GPIO.LOW)

def toggle_pihole(channel):
    """
    Callback function triggered by the button press event.
    It toggles Pi-hole status and updates the LED accordingly.
    """
    currently_enabled = get_pihole_status()

    if currently_enabled:
        subprocess.run(["pihole", "disable"], check=False)
        print("Pi-hole disabled.")
    else:
        subprocess.run(["pihole", "enable"], check=False)
        print("Pi-hole enabled.")

    # Update the LED to reflect the new status
    new_status = get_pihole_status()
    update_led_state(new_status)

def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # Set up the LED pin as output (default off)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.LOW)

    # Set up the button pin as input with an internal pull-up resistor
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Update LED on startup (in case Pi-hole is already enabled)
    initial_status = get_pihole_status()
    update_led_state(initial_status)

    # Detect falling edges on the button (since pull-up means press = LOW)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING,
                          callback=toggle_pihole, bouncetime=300)

    print("Monitoring button presses and Pi-hole status. Press Ctrl+C to exit.")

    last_status = initial_status
    try:
        while True:
            # Periodically check if Pi-hole was toggled elsewhere
            current_status = get_pihole_status()
            if current_status != last_status:
                update_led_state(current_status)
                last_status = current_status
            time.sleep(1)  # Adjust polling interval as desired
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
