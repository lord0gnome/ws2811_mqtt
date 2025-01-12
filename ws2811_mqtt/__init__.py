import os

import time
from dotenv import load_dotenv

if os.name == 'nt':
    os.system('color')

load_dotenv(os.getenv("WS2811_ENV_PATH", ".env"))

from ws2811_mqtt.args import init_args
init_args()

from ws2811_mqtt.logger import init_logger
init_logger()

from ws2811_mqtt.mqtt import init_mqtt
init_mqtt()

def main():
    while True:
        time.sleep(2)

if __name__ == "__main__":
    main()