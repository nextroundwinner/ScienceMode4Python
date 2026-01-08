# Introduction
This page describes implementation details.

# General information

## Basic information
- Starting point is using a _Device_ object matching attached hardware: _DeviceP24_ or _DeviceI24_
  - If you have multiple devices, create multiple _Device_ instances
  - With _capabilities_ it is possible to query for available layer
- To create a _Device_ object, a _Connection_ object is required, use _SerialConnection_ to connect to a serial port
  - _Connection_ must be opened and closed
- Call _device.initialize()_ to get a defined state of the device (it stops any active stimulation/measurement)
- _Device_ object has layers to access commands
  - _Layer_ object has functions to send commands to the device and process acknowledges
  - To access layer, use helper functions _get\_layer\_xxx_
  - _DeviceP24_ has layer general, low level and mid level
  - _DeviceI24_ has layer general and dyscom
  - Do not mix usage of layers because device has a single internal state, e.g. calling low level _init()_ and afterwards mid level _update()_ will not work

## Device communication
- Each device has an instance of a _PacketBuffer_
  - Should be used to read packets from connection
  - Handles extraction of packets from byte stream
- Most functions communicating with the device are async functions using name schema _xxx_, because they wait for a matching acknowledge and return values from acknowledge
  - If no matching acknowledge or no acknowledge arrives in time, an exception is raised
  - If a command has an error information and an error is set, an exception is raised
  - The async functions connection buffer handling is always identical:
    - Clear buffer
    - Send command
    - Process incoming data until the expected acknowledge arrives
    - More data remains in connection buffer
  - Do not call async functions in parallel (e.g. from different event loops), because each function expects specific commands from the device and clears incoming data buffer
- Additionally functions with naming schema _send_xxx_ are normal functions not waiting for acknowledge
  - The acknowledge needs to handled manually by using _PacketBuffer_ object from device

## Logging
- Library creates a custom logger, see class _Logger_
- By default some information is logged to console
- Set log level to DEBUG to get more detailed information
  - `logger().setLevel(logging.DEBUG)`
- For better performance, disable logger
  - `logger().disabled = True`

## General layer (all devices)
- Contains functions to get common information like device serial or firmware version

## Mid level layer (P24)
- Contains functions for mid level stimulation
- This mode is good to let the device stimulate a predefined pattern until _stop()_ is send
- Usage
  - Call _init()_ to set device in mid level mode
  - Call _update()_ with stimulation pattern
  - Call _get_current_data()_ every 1.5s to keep stimulation ongoing
  - Call _stop()_ to end stimulation and leave mid level mode

## Low level layer (P24)
- Contains functions for low level stimulation
- This mode is good to react to a external trigger to change stimulation pattern
- Without _send_channel_config()_ the device will not stimulate
- Usage
  - Call _init()_ to set device in low level mode
  - Update configuration with _send_channel_config()_ when external trigger occurs
    - As soon as _send_channel_config()_ arrives at device, it stimulates according stimulation pattern
    - It stops stimulation when stimulation pattern is over
  - Call _stop()_ to leave low level mode

## Dyscom layer (I24)
- Contains functions for dyscom level
- This mode is used by I24 to measure EMG or BI
- Usage for live data
  - Call _power_module()_ to power on measurement module
  - Call _init()_ with parameter for measurement and DyscomInitFlag for live data
  - Call _start()_ to start measurement
    - Device sends now _DlSendLiveData_ packets with measurement data
  - Call _stop()_ to end measurement
  - Call _power_module()_ to power off measurement module
- Usage for measurement data read from memory card
  - Call _power_module()_ to power on measurement module and memory card
  - Call _init()_ with parameter for measurement and DyscomInitFlag for storage mode
    - Result contains measurement id, that is the filename used later
  - Call _start()_ to start measurement
    - Device sends nothing but stores measurement data on memory card
  - Call _stop()_ to end measurement
  - Call _power_module()_ to power off measurement module
  - Call _get_meas_file_content()_ with filename from _init()_ to get measurement data
  - Call _power_module()_ to power off memory card
- IMPORTANT: not all storage related functions are tested

# Platform hints

## Using USB under Linux with Hyper-V
- On Windows
  - Install [usbipd-win](https://github.com/dorssel/usbipd-win)
  - `usbipd list`
  - `usbipd bind --busid <BUSID>`
- On Linux
  - Install _usbip_
    - `sudo apt install linux-tools-generic usbip`
  - `sudo usbip attach -r <host-ip> -b <BUSID>`
  - In case of permission error
    - `sudo chmod 666 /dev/ttyACMx`

## Using MacOS under VirtualBox
- https://www.reddit.com/r/macOSVMs/comments/1gb8egp/macos_sonoma_virtualbox_bootloop_afterduring/?rdt=48615


## I24 protocol hints

### DL_init
- Init state seems always be UNUSED
- Output data rate depends on init params filter property
- Setting a filter overwrite other settings
  - ADS129x register channel 1-4 settings
  - ADS129x config register output data rate
  - Maybe more register values are changed

### DL_get for type file system status and list of measurement info
- Return never meaningful values, probably not implemented on I24 side

### DL_get for type battery
- Dl get types (table 23)
  - 0 -> Battery (was Unused)

### DL_send_live_data
- SignalType for each sample is always 0
- Contains always 5 samples, regardless of selected signal types in DL_init
  - Fifth sample value seems always be zero