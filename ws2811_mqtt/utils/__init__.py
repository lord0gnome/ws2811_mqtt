from ws2811_mqtt.logger import log_client

def colr_tuple_to_st(color_tuple):
    try:
        # Check if the color tuple has exactly 3 components
        if len(color_tuple) != 3:
            raise ValueError("Color tuple must have three components")

        # Swap the first two elements back
        original_color = (color_tuple[1], color_tuple[0], color_tuple[2])

        # Convert the tuple into a comma-separated string
        color_string = ','.join(map(str, original_color))
        return color_string
    except Exception as e:
        log_client.error(f"[MQTT][%15s] Error creating color string from {color_tuple}: {e}", "colr_tuple_to_st")
        return None


def colr_str_to_tuple(color_string):
    try:
        # Parse the color string into a tuple of integers
        color = tuple(map(int, color_string.split(',')))

        # Check if the color tuple has exactly 3 components
        if len(color) != 3:
            raise ValueError("Color string must have three components")

        # Swap the first two elements
        swapped_color = (color[1], color[0], color[2])
        return swapped_color
    except Exception as e:
        log_client.error(f"[MQTT][%15s] Error parsing color string {color_string}: {e}", "colr_str_to_tuple")
        return None
