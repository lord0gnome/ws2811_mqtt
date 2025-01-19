import os
import json
import paho.mqtt.client as mqtt
import yaml
import pprint
import logging
from pathlib import Path

from ws2811_mqtt.logger import log_client
from ws2811_mqtt.leds import leds, set_led, NUM_LEDS, start_cycle_colors, stop_cycle_colors, start_alternate_colors, stop_alternate_colors, set_cc_option, pixels
from ws2811_mqtt.utils import colr_str_to_tuple, colr_tuple_to_st



mqtt_client = None
device_config = None  # Declare a global variable for the device configuration

# MQTT settings
MQTT_BROKER = os.getenv("MQTT_BROKER")
if not MQTT_BROKER:
    raise ValueError("Missing MQTT_BROKER env var")
MQTT_PORT = os.getenv("MQTT_PORT")
if not MQTT_PORT:
    raise ValueError("Missing MQTT_PORT env var")
try:
    MQTT_PORT = int(MQTT_PORT)
except ValueError:
    raise ValueError("MQTT_PORT must be an integer")
MQTT_USER = os.getenv("MQTT_USER")
if not MQTT_USER:
    raise ValueError("Missing MQTT_USER env var")
MQTT_PASS = os.getenv("MQTT_PASS")
if not MQTT_PASS:
    raise ValueError("Missing MQTT_PASS env var")

MQTT_UID = os.getenv("MQTT_UID") or "ws2811-mqtt"
MQTT_TOPIC_STATUS = os.getenv("MQTT_TOPIC_STATUS") or f"homeassistant/device/{MQTT_UID}/config"


def publish_all_led(all_led_state):
    try:
        led_status = all_led_state["state"]
        topic = device_config.get("cmps").get(f"all_leds").get("state_topic")
        rgb_topic = device_config.get("cmps").get(f"all_leds").get("rgb_stat_t")
        mqtt_client.publish(f"{topic}", led_status.encode('utf-8'), retain=True)
        if "color" in all_led_state:
            led_status = colr_tuple_to_st(all_led_state["color"])
            mqtt_client.publish(f"{rgb_topic}", led_status.encode('utf-8'), retain=True)
            log_client.debug(f"[MQTT][%15s] Status: {all_led_state}", "publish_all_led")
        else:
            log_client.debug(f"[MQTT][%15s] Status: {all_led_state['state']}", "publish_all_led")
    except Exception as e:
        log_client.error(f"[MQTT][%15s] Error publishing LED status: {e}", "publish_all_led")

def publish_led(led_index):
    try:
        led = leds[led_index]
        led_status = leds[led_index]["state"]
        topic = device_config.get("cmps").get(f"led_{led_index + 1}").get("state_topic")
        rgb_topic = device_config.get("cmps").get(f"led_{led_index + 1}").get("rgb_stat_t")
        mqtt_client.publish(f"{topic}", led_status.encode('utf-8'), retain=True)
        led_status = colr_tuple_to_st(led["color"])
        mqtt_client.publish(f"{rgb_topic}", led_status.encode('utf-8'), retain=True)
        log_client.debug(f"[MQTT][%15s] Published LED status : Led #{led_index + 1} == {led['color']}", "publish_led")
    except Exception as e:
        log_client.error(f"[MQTT][%15s] Error publishing LED status: {e}", "publish_led")

def on_connect(client, userdata, flags, rc):
    log_client.info(f"[MQTT][%15s] Connected to broker", "on_connect")
    # Loop through LEDs and subscribe to their command topics
    for _, led_config in device_config['cmps'].items():
        for topic_type in ["command_topic", "rgb_cmd_t"]:
            topic = led_config.get(topic_type, False)
            if topic:
                client.subscribe(topic)
                log_client.info(f"[MQTT][%15s] Subscribed to {topic}", "on_connect")
            # rgb_command_topic = led_config['rgb_cmd_t']
            # client.subscribe(rgb_command_topic)
            # log_client.info(f"[MQTT][%15s] Subscribed to {rgb_command_topic}", "on_connect")

    # Publish initial status
    client.publish(MQTT_TOPIC_STATUS, json.dumps(device_config), retain=True)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        log_client.info(f"[MQTT][%15s] topic  : \"{msg.topic}\"", "on_message")
        log_client.info(f"[MQTT][%15s] payload: \"{msg.payload}\"", "on_message")
        if msg.topic == f"cmnd/{MQTT_UID}/all_leds/cycle_color":
            if payload == "ON":
                mqtt_client.publish(f"stat/{MQTT_UID}/all_leds", "OFF".encode('utf-8'), retain=True)
                mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate", "OFF".encode('utf-8'), retain=True)
                stop_alternate_colors()
                start_cycle_colors()
            else:
                stop_cycle_colors()
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/cycle_color", payload, retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/alternate":
            if payload == "ON":
                mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/cycle_color", "OFF".encode('utf-8'), retain=True)
                mqtt_client.publish(f"stat/{MQTT_UID}/all_leds", "OFF".encode('utf-8'), retain=True)
                stop_cycle_colors()
                start_alternate_colors()
            else:
                stop_alternate_colors()
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate", payload, retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/alternate/color_one/rgb":
            color_one = colr_str_to_tuple(payload)
            set_cc_option("color_one", color_one)
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate/color_one/rgb", payload.encode('utf-8'), retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/auto_write":
            pixels.auto_write = False if payload == "ON" else True
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/auto_write", payload.encode('utf-8'), retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/alternate/color_one":
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate/color_one", "ON".encode('utf-8'), retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/alternate/color_two/rgb":
            color_two = colr_str_to_tuple(payload)
            set_cc_option("color_two", color_two)
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate/color_two/rgb", payload.encode('utf-8'), retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/alternate/color_two":
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate/color_two", "ON".encode('utf-8'), retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/alternate/rate":
            rate = payload
            set_cc_option("rate", float(rate))
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate/rate", payload, retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/alternate/transition":
            transition = True if payload == "ON" else False
            set_cc_option("transition", transition)
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate/transition", payload, retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/rgb":
            stop_cycle_colors()
            stop_alternate_colors()
            for led_index in range(len(leds)):
                leds[led_index] = {"state": "ON", "color": colr_str_to_tuple(payload) }
                set_led(led_index)
                # publish_led(led_index)
                publish_all_led({"state": "ON", "color": colr_str_to_tuple(payload) })
            if not pixels.auto_write:
                pixels.show()
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate", "OFF".encode('utf-8'), retain=True)
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/cycle_color", "OFF".encode('utf-8'), retain=True)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds":
            stop_cycle_colors()
            stop_alternate_colors()
            for led_index in range(len(leds)):
                leds[led_index]["state"] = payload
                set_led(led_index)
                # publish_led(led_index)
                publish_all_led({"state": payload })
            if not pixels.auto_write:
                pixels.show()
            mqtt_client.publish(f"stat/{MQTT_UID}/all_leds/alternate", "OFF".encode('utf-8'), retain=True)
        elif msg.topic in [led_config.get('command_topic') for led_config in device_config['cmps'].values()]:
            led_index = int(msg.topic.split('_')[-1]) -1
            leds[led_index]["state"] = payload
            set_led(led_index)
        elif msg.topic in [led_config.get('rgb_cmd_t') for led_config in device_config['cmps'].values()]:
            led_index = int(msg.topic.split(MQTT_UID)[-1].split('/')[1].split('_')[-1]) -1
            leds[led_index] = {"state": "ON", "color": colr_str_to_tuple(payload) }
            set_led(led_index)
        # publish_led(led_index)
    except Exception as e:
        log_client.error(f"[MQTT][%15s] Error processing message: {e}", "on_message")
        log_client.debug(f"[MQTT][%15s] Message payload : {msg.payload}", "on_message")
        log_client.debug(f"[MQTT][%15s] Message topic : {msg.topic}", "on_message")

def gen_leds_conf():
    # led_config = {}
    # Iterate over each component configuration in the device configuration
    # and update string values by replacing 'MQTT_UID' with its actual value.
    for _, component_values in device_config["cmps"].items():
        for key, value in component_values.items():
            if isinstance(value, str):
                component_values[key] = value.replace("MQTT_UID", MQTT_UID)

    # This loop generates a configuration dictionary for each LED by iterating over
    # a range from 1 to the total number of LEDs (`NUM_LEDS`), inclusive.
    # For each LED, it creates a unique identifier and sets its configuration,
    # including topics for state and command, which will be used with the MQTT broker,
    # then updates the device configuration with this information.
    # for i in range(1, NUM_LEDS + 1):
    #     led_id = f"led_{i}"
    #     led_number = f"{i:02}"  # Format as two digits
    #     led_config[led_id] = {
    #         "p": "light",
    #         "clrm": "rgb",
    #         "ret": True,
    #         "unique_id": f"ws2811_led_{led_number}",
    #         "rgb_stat_t": f"stat/{MQTT_UID}/led_{led_number}/rgb",
    #         "rgb_cmd_t": f"cmnd/{MQTT_UID}/led_{led_number}/rgb",
    #         "name": f"Led {led_number}",
    #         "command_topic": f"cmnd/{MQTT_UID}/led_{led_number}",
    #         "state_topic": f"stat/{MQTT_UID}/led_{led_number}"
    #     }

    # device_config["cmps"].update(led_config)
    # log_client.info("[MQTT][%15s] `LED configuration generated` :", "gen_leds_conf")
    if log_client.getEffectiveLevel() == logging.INFO:
        pprint.pprint(device_config, indent=2)


def init_mqtt():
    global mqtt_client, device_config  # Declare global to modify the external variables

    # Load device configuration once during initialization
    path = Path(os.path.dirname(__file__)) / "../device_config.yaml"
    with open(path, 'r') as file:
        device_config = yaml.safe_load(file)
        # Replace placeholder MQTT_UID, and generate as many "Lights" as there are leds in HA
        gen_leds_conf()
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(username=MQTT_USER, password=MQTT_PASS)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    # for i in range(NUM_LEDS):
    #     publish_led(i)
