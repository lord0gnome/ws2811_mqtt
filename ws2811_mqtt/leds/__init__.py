import board
import neopixel
import os
import threading  # For running the alternating color loop
import time

from ws2811_mqtt.logger import log_client


NUM_LEDS = int(os.getenv("NUM_LEDS") or 50) # Number

# Initialize the NeoPixel strip
pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, brightness=1, auto_write=os.getenv("AUTOWRITE") == "True" or False)
leds = [{"state": "OFF", "color": (255,255,255)} for _ in range(len(pixels))]
# pixels = [(0, 0, 0) for _ in range(NUM_LEDS)]

loop_thread = None
cycle_colors_active = False
alternate_colors_active = False
last_state = -1

colors_options = {
    "color_one": (255,255,0),
    "color_two": (0,255,255),
    "rate": 2,
    "transition": True,
}

def set_cc_option(key, value):
    global colors_options
    global cycle_colors_active

    log_client.info(f"[LEDS][%15s] set_cc_option called with key={key}, value={value}", "set_cc_option")
    colors_options[key] = value
    if cycle_colors_active:
        stop_cycle_colors()
        start_cycle_colors()


def manage_alternate_colors():
    global alternate_colors_active
    global colors_options
    global last_state
    try:
        state = -last_state
        while alternate_colors_active:
            state = -state
            for i in range(NUM_LEDS):
                state = -state
                set_l_on(i, colors_options.get("color_one") if state == 1 else colors_options.get("color_two"))
                if colors_options.get("transition"):
                    if not pixels.auto_write:
                        pixels.show()
                    time.sleep(colors_options.get("rate") / NUM_LEDS)
                if not alternate_colors_active:
                    break
            if not pixels.auto_write:
                pixels.show()
            log_client.info(f"[LEDS][%15s] state => {state}", "manage_alternate_colors")
            if not colors_options.get("transition"):
                time.sleep(colors_options.get("rate"))
    except Exception as e:
        log_client.error(f"[LEDS][%15s] Error in alternating colors: {e}", "manage_alternate_colors")

def start_alternate_colors():
    global loop_thread, alternate_colors_active, colors_options
    if loop_thread is not None and loop_thread.is_alive():
        stop_alternate_colors()
        loop_thread.join()  # Ensure the previous thread ends before starting a new one
    alternate_colors_active = True
    loop_thread = threading.Thread(target=manage_alternate_colors, args=())
    loop_thread.start()

def stop_alternate_colors():
    global alternate_colors_active
    alternate_colors_active = False
    if loop_thread is not None:
        loop_thread.join()

def start_cycle_colors():
    global loop_thread, cycle_colors_active, colors_options
    if loop_thread is not None and loop_thread.is_alive():
        stop_cycle_colors()
        loop_thread.join()  # Ensure the previous thread ends before starting a new one
    cycle_colors_active = True
    loop_thread = threading.Thread(target=manage_cycle_colors, args=())
    loop_thread.start()

def stop_cycle_colors():
    global cycle_colors_active
    cycle_colors_active = False
    if loop_thread is not None:
        loop_thread.join()


def manage_cycle_colors():
    global cycle_colors_active
    global colors_options
    global last_state
    try:
        state = -last_state
        while cycle_colors_active:
            state = -state
            for i in range(NUM_LEDS):
                set_l_on(i, colors_options.get("color_one") if state == 1 else colors_options.get("color_two"))
                if colors_options.get("transition"):
                    time.sleep(colors_options.get("rate") / NUM_LEDS)
                    if not pixels.auto_write:
                        pixels.show()
                if not cycle_colors_active:
                    break
            log_client.info(f"[LEDS][%15s] state => {state}", "manage_cycle_colors")
            if not colors_options.get("transition"):
                if not pixels.auto_write:
                    pixels.show()
                time.sleep(colors_options.get("rate"))
    except Exception as e:
        log_client.error(f"[LEDS][%15s] Error in alternating colors: {e}", "manage_cycle_colors")

# Function to apply changes from the leds array to the pixels array
def set_led(led_index):
    try:
        if leds[led_index]["state"] == "OFF":
            pixels[led_index] = (0, 0, 0)
        else:
            pixels[led_index] = leds[led_index]["color"]
            log_client.debug(f"[LEDS][%15s] {led_index} => {leds[led_index]['state']}", "set_led")
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
        log_client.debug(f"[LEDS][%15s] LED {led_index} color set to {color}.", "set_l_on")
    except Exception as e:
        log_client.error(f"[LEDS][%15s] Error setting LED color: {e}", "set_l_on")
