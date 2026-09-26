# Third-party dependencies

Hardware support comes from Waveshare's official ESP32-S3-Knob-Touch-LCD-1.8 demo:
https://www.waveshare.com/wiki/ESP32-S3-Knob-Touch-LCD-1.8

Vendor drivers and LVGL are downloaded by scripts/prepare_vendor.py, not redistributed in this repository. The script verifies the exact archive hash before preparing the build. Vendor files retain their original copyright and license headers. Some driver files carry Espressif Apache-2.0 notices; LVGL includes LICENCE.txt (MIT). Files without an explicit license remain subject to their upstream terms; this project's license does not relicense them.

Local adaptations expose the LVGL mutex functions, remove the demo UI, and enable fonts 20/28/32. Arduino-ESP32 3.3.0 and pyserial 3.5 are separately installed dependencies under their respective upstream licenses.
