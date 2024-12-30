import os
import json
import paho.mqtt.client as mqtt
import yaml
import pprint
import logging

from ws2811_mqtt.logger import log_client
from ws2811_mqtt.leds import leds, set_led, NUM_LEDS, start_alternating_colors, stop_alternating_colors
from ws2811_mqtt.utils import colr_str_to_tuple, colr_tuple_to_st


mqtt_client = None
device_config = None  # Declare a global variable for the device configuration

# MQTT settings
MQTT_BROKER = os.getenv("MQTT_BROKER") or raise ValueError("Missing MQTT_BROKEN env var")
MQTT_PORT = int(os.getenv("MQTT_PORT")) or raise ValueError("Missing MQTT_BROKEN env var"
MQTT_USER = os.getenv("MQTT_USER") or raise ValueError("Missing MQTT_BROKEN env var"
MQTT_PASS = os.getenv("MQTT_PASS") or raise ValueError("Missing MQTT_BROKEN env var"
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
    client.subscribe(f"cmnd/{MQTT_UID}/all_leds/alternate")
    client.subscribe(f"cmnd/{MQTT_UID}/all_leds/stop")
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
        if msg.topic == f"cmnd/{MQTT_UID}/all_leds/alternate":
            options = json.loads(payload)
            color_one = colr_str_to_tuple(options.get("color_one"))
            color_two = colr_str_to_tuple(options.get("color_two"))
            rate = options.get("rate", 1)
            transition = options.get("transition", False)
            start_alternating_colors(color_one, color_two, rate, transition)
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds/rgb":
            for led_index in range(len(leds)):
                leds[led_index] = {"state": "ON", "color": colr_str_to_tuple(payload) }
                set_led(led_index)
                publish_led(led_index)
                publish_all_led({"state": "ON", "color": colr_str_to_tuple(payload) })
        elif msg.topic == f"cmnd/{MQTT_UID}/all_leds":
            for led_index in range(len(leds)):
                leds[led_index]["state"] = payload
                set_led(led_index)
                publish_led(led_index)
                publish_all_led({"state": payload })
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
    led_config = {}
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
    for i in range(1, NUM_LEDS + 1):
        led_id = f"led_{i}"
        led_number = f"{i:02}"  # Format as two digits
        led_config[led_id] = {
            "p": "light",
            "clrm": "rgb",
            "ret": True,
            "unique_id": f"ws2811_led_{led_number}",
            "rgb_stat_t": f"stat/{MQTT_UID}/led_{led_number}/rgb",
            "rgb_cmd_t": f"cmnd/{MQTT_UID}/led_{led_number}/rgb",
            "name": f"Led {led_number}",
            "command_topic": f"cmnd/{MQTT_UID}/led_{led_number}",
            "state_topic": f"stat/{MQTT_UID}/led_{led_number}"
        }

    device_config["cmps"].update(led_config)
    log_client.info("[MQTT][%15s] `LED configuration generated` :", "gen_leds_conf")
    if log_client.getEffectiveLevel() == logging.INFO:
        pprint.pprint(device_config, indent=2)


def init_mqtt():
    global mqtt_client, device_config  # Declare global to modify the external variables

    # Load device configuration once during initialization
    with open('ws2811_mqtt/device_config.yaml', 'r') as file:
        device_config = yaml.safe_load(file)
        # Replace placeholder MQTT_UID, and generate as many "Lights" as there are leds in HA
        gen_leds_conf()
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(username=MQTT_USER, password=MQTT_PASS)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    for i in range(NUM_LEDS):
        publish_led(i)