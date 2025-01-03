import board
import neopixel
import os
import threading  # For running the alternating color loop
import time

from ws2811_mqtt.logger import log_client


NUM_LEDS = int(os.getenv("NUM_LEDS") or 50) # Number

# Initialize the NeoPixel strip
pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, brightness=1, auto_write=True)
leds = [{"state": "OFF", "color": (255,255,255)} for _ in range(len(pixels))]
# pixels = [(0, 0, 0) for _ in range(NUM_LEDS)]

alternating_thread = None
alternating_colors_active = False

def manage_alternating_colors(color_one, color_two, rate, transition):
    global alternating_colors_active
    try:
        state = -1
        while alternating_colors_active:
            state = -state
            for i in range(NUM_LEDS):
                set_l_on(i, color_one if state == 1 else color_two)
                if transition:
                    time.sleep(rate / NUM_LEDS)
            log_client.info(f"[LEDS][%15s] state => {state}", "manage_alternating_colors")
            if not transition:
                time.sleep(rate)
    except Exception as e:
        log_client.error(f"[LEDS][%15s] Error in alternating colors: {e}", "manage_alternating_colors")

def start_alternating_colors(color_one, color_two, rate, transition):
    global alternating_thread, alternating_colors_active
    if alternating_thread is not None and alternating_thread.is_alive():
        stop_alternating_colors()
        alternating_thread.join()  # Ensure the previous thread ends before starting a new one
    alternating_colors_active = True
    alternating_thread = threading.Thread(target=manage_alternating_colors, args=(color_one, color_two, rate, transition))
    alternating_thread.start()

def stop_alternating_colors():
    global alternating_colors_active
    alternating_colors_active = False
    if alternating_thread is not None:
        alternating_thread.join()

# Function to apply changes from the leds array to the pixels array
def set_led(led_index):
    try:
        if leds[led_index]["state"] == "OFF":
            pixels[led_index] = (0, 0, 0)
        else:
            pixels[led_index] = leds[led_index]["color"]
            log_client.info(f"[LEDS][%15s] {led_index} => {leds[led_index]['state']}", "set_led")
    except Exception as e:
        log_client.error(f"[LEDS][%15s] Error applying LED changest to led {led_index}: {e}", "set_led")


# Function to check if an LED is on by verifying its color is not black (0, 0, 0)
def led_is_on(led_index):
    log_client.debug(f"[LEDS][%15s] LED index {led_index}", "led_is_on")
    log_client.debug(f"[LEDS][%15s] LED value {pixels[led_index]}", "led_is_on")
    led_on = leds[led_index]["state"] == "ON"
    return led_on

# Function to set a LED's color to black (0, 0, 0), effectively turning it off
def set_l_off(led_index):
    try:
        log_client.debug(f"[LEDS][%15s] LED value before {pixels[led_index]}", "set_l_off")
        pixels[led_index] = (0, 0, 0)
        log_client.debug(f"[LEDS][%15s] LED {led_index} color set to black.", "set_l_off")
        log_client.debug(f"[LEDS][%15s] LED value after  {pixels[led_index]}", "set_l_off")
    except Exception as e:
        log_client.error(f"[LEDS][%15s] Error setting LED color: {e}", "set_l_off")

# Function to set a LED's color to a specified value, defaulting to white (255, 255, 255)
def set_l_on(led_index, color=None):
    try:
        leds[led_index].update({"state": "ON", "color": color or leds[led_index]["color"]})
        set_led(led_index)
        log_client.info(f"[LEDS][%15s] LED {led_index} color set to {color}.", "set_l_on")
    except Exception as e:
        log_client.error(f"[LEDS][%15s] Error setting LED color: {e}", "set_l_on")
