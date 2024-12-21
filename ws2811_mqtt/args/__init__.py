import argparse
args_client = None


def init_args():
    global args_client
    parser = argparse.ArgumentParser(description="Control the LED strip with MQTT and API")
    parser.add_argument('-v', '--verbosity', action='count', default=0, help="increase output verbosity, each v adds a verbosity level")
    args_client = parser.parse_args()