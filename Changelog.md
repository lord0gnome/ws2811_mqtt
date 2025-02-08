# 1.0.0
- Added support for MQTT protocol to control WS2811 LED strips.
- Provides a mqtt interface for seamless integration with smart home systems.
- Initial release with basic functionality and documentation.

# 1.1.0
- Improved mqtt control of alternating patterns for LED animations.
- Better management of main loop when handing changes in configuration
- Better management of persistent states when restarting the program.

# 1.1.1
- Fix path of `device_config.yaml` which was not working

# 1.2.0
- Added support for new color transition effects.
- Added control over the auto_write adafruit pixels library variable
- Changed the step range and precision

# 1.3.0
- Fixed Loop logic

# 1.3.1
- **Added FirePlace LED Mode**
Adds a new mode to create a cozy ambiance with pulsing flames, perfect for simulating a fireplace.
- Fixed lack of retain on rate