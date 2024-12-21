# ws2811_mqtt

## Overview
`ws2811_mqtt` is a Python package designed to control WS2811 LED strips using MQTT, making it easier to integrate lighting controls with the Home Assistant platform.

## Local Installation
Use [Poetry](https://python-poetry.org/) to install the package:
```bash
poetry install
```

## PyPI Installation

The `ws2811_mqtt` package is also published on PyPI, allowing you to easily install it using pip. This enables seamless integration into projects without using Poetry.

```bash
pip install ws2811_mqtt
```

## Usage
Here's a quick example on how to use `ws2811_mqtt` in your project:

### env file
Multiple ways of doing this:
1. You can pass the env vars directly to the executable
2. create an env file where the script is run, and it will automatically be loaded
3. Pass the path to your env file as an Environment variable: `WS2811_ENV_PATH` and it will read from there.

```dotenv
NUM_LEDS = 50
MQTT_BROKER = "192.168.0.123"
MQTT_PORT = 1883
MQTT_USER = "your_user"
MQTT_PASS = "your_password"
MQTT_UID = "ws2811-1"
```

#### Explanation of Environment Variables:
- NUM_LEDS: This variable sets the number of LEDs in your strip. It's essential to configure
  this correctly to ensure that the program knows how many LEDs it needs to control.
- MQTT_BROKER: This is the IP address of your MQTT broker. The broker is responsible for
  managing the communication between the different parts of your system.
- MQTT_PORT: The port on which the MQTT broker is running. The default MQTT port is 1883,
  but this might need to be changed if your setup uses a different configuration.
- MQTT_USER: The username required to authenticate with the MQTT broker.
- MQTT_PASS: The password for the given MQTT user. It's used alongside the username
- MQTT_UID: A unique identifier for this particular WS2811 LED controller instance. This is
  used so the broker and corresponding systems know where messages should be routed.

## Script arguments
```
usage: ws2811-mqtt [-h] [-v]

Control the LED strip with MQTT and API

options:
  -h, --help       show this help message and exit
  -v, --verbosity  increase output verbosity, each v adds a verbosity level, (ex: -vvv)
```


## Running the script
if installed locally:
```bash
poetry run ws2811_mqtt
```
if installed as package
```
ws2811_mqtt
```
## Contributing
Contributions are welcome! Please submit a pull request or file an issue for any enhancements.

## License
`ws2811_mqtt` is licensed under the Apache License 2.0.

## Support
For issues or questions, please open an issue in this repository.
