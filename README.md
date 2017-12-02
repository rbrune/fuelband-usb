# Fuelband USB interface
Python script to access the "Nike+ FuelBand" (non SE version) via USB HID.
The protocol was reverse engineered from observing USB traffic between the Mac Nike+ application and the device as well as probing the interface.

Currently only some status variables and the system log of the device are read out. Reading out activity/movement data is not yet supported. To see how to access the stored activity data check out the example Android app:
https://github.com/rbrune/Fuelbandsync
The Bluetooth and USB protocol are the same as the Bluetooth chip opens up a channel to the main CPU to pass through all commands.


# Requirements
https://github.com/trezor/cython-hidapi


# Example usage
If the fuelband is not found by the script check if it shows up in your listing of usb devices. If not try plugging it in while pushing down the fuelband button.

```
python fuelband-usb.py status
python fuelband-usb.py log
```


# TODO
* finish read out of activity data
* implement initial device setup
* finish up flash memory dump functions
* finish up device firmware upgrade routines
