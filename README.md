# Radio Knob for SDR-Control

Turn a **Waveshare ESP32-S3-Knob-Touch-LCD-1.8** into a USB tuning dial with a live frequency display for **SDR-Control on macOS**.

Built and tested with an **Icom IC-7300MK2 connected over Ethernet**. This is an independent hobby project, not an official Icom, Waveshare, or SDR-Control product.

## Features

- Rotary tuning via USB MIDI; touchscreen switches FINE x1 / FAST x10.
- Live main-VFO frequency on the round screen, updated about five times per second.
- Python Mac helper reads SDR-Control's local CAT server and sends the frequency over USB serial.
- Reconnects automatically; clears stale frequency after three seconds without updates.
- Firmware and helper contain no transmit/PTT commands.

USB carries both MIDI tuning and serial display updates. SDR-Control controls the radio over Ethernet. Wi-Fi operation is not implemented.

## Requirements

- Waveshare ESP32-S3-Knob-Touch-LCD-1.8 (tested: 16 MB flash, 8 MB OPI PSRAM).
- Data-capable USB cable connected to the board's **ESP32-S3** interface. On the tested board reversing the plug selected the other processor; an audio-only or CH340 interface is not the S3 interface used here.
- Mac with SDR-Control and a working radio connection.
- Python 3.9+, Arduino CLI, Arduino-ESP32 **3.3.0**.

## Build firmware

Install Arduino CLI, then run these commands from the repository root:

```sh
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.0 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
python3 scripts/prepare_vendor.py
bash scripts/build.sh
```

The preparation script downloads the official Waveshare demo, verifies its SHA-256 checksum, and prepares the hardware drivers and bundled LVGL. These generated dependencies are ignored by Git. A previously downloaded matching archive can be supplied with `--archive /path/to/demo.zip`.

The build uses USB-OTG/TinyUSB, USB CDC on boot, OPI PSRAM, 16 MB flash, and the huge_app partition scheme. Firmware outputs appear in `dist/`. Optional environment variables `ARDUINO_CLI` and `ARDUINO_CONFIG` select an existing CLI installation and configuration.

## Back up and flash

Back up your own board before replacing firmware. Keep that backup private: it can contain saved credentials. Confirm the S3 port with `python -m serial.tools.list_ports -v`.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install esptool==4.11.0 -r mac-helper/requirements.txt
# Replace PORT with your board's actual serial device.
python -m esptool --chip esp32s3 --port PORT read_flash 0 0x1000000 factory-backup.bin
python -m esptool --chip esp32s3 --port PORT verify_flash 0 factory-backup.bin
python -m esptool --chip esp32s3 --port PORT write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB 0 dist/RadioKnob.ino.merged.bin
```

Use the vendor's BOOT/reset procedure if the port will not enter download mode. The port can change after flashing. Do not flash the separate ESP32 audio processor. Restore a verified full backup with `write_flash 0 factory-backup.bin` if needed.

## Configure SDR-Control

1. Connect SDR-Control to your radio normally.
2. Open **Tools → Controller → MIDI Controller**.
3. Select **ESP32S3_DEV**, choose **DJ2GO2**, and enable it.
4. Map **Control 16 → Frequency** (not “2nd VFO Frequency”). Set wheel sensitivity to **1**.
5. Test direction and tuning increments. The knob sends center-64 relative values: 65/63 for fine and 74/54 for fast. Actual Hz per turn depends on SDR-Control settings.
6. Open **Radio → CAT Server**. Configure an unused server for **RigCtrl / Hamlib**, port **4532**, and enable it. Enable CAT on app startup if desired.

The helper connects only to `127.0.0.1`; SDR-Control controls the CAT server's listening interfaces. No router port forwarding is needed for this helper.

## Run the display helper

```sh
source .venv/bin/activate
python -m serial.tools.list_ports -v
python mac-helper/radio_display.py --serial YOUR_USB_SERIAL_NUMBER
```

Use the USB **serial number**, not the `/dev/cu...` path; the two can differ. Keep SDR-Control open and connected. The helper sends only the Hamlib `f` query, then sends `FREQ <Hz>` to the knob. `status.json` includes the last firmware acknowledgement.

For automatic startup on macOS (requires `/usr/bin/python3`, normally provided with Apple's Command Line Tools):

```sh
python mac-helper/install_macos.py --serial YOUR_USB_SERIAL_NUMBER
```

This installs the helper and pyserial into `~/Library/Application Support/RadioKnob` and a login service at `~/Library/LaunchAgents/local.dan.radio-knob-display.plist`. It replaces an existing service with that name. Status and logs are stored in the Application Support directory.

To stop it:

```sh
launchctl bootout gui/$(id -u)/local.dan.radio-knob-display
```

To disable future automatic startup, remove that specific plist after stopping it.

## Troubleshooting

- **63 Hz jumps:** use v1.2 firmware and the DJ2GO2 settings above.
- **No tuning after a firmware update:** toggle MIDI Enabled off/on; check wheel sensitivity is 1.
- **Waiting for radio:** check CAT server port 4532, the helper's USB serial selection, and `helper.log`.
- **USB port busy while flashing:** stop the helper first, then restart it afterward.
- **No Mac audio:** this firmware does not carry radio audio; check SDR-Control's audio output separately.

## Validation and limitations

The original v1.2 installation was compiled and hash-verified on hardware. CAT frequency and firmware acknowledgement matched; the stale-data timeout was checked. The public packaging makes USB identity configurable. Other radio models and macOS configurations have not been tested. This is not a standalone radio controller: it requires the Mac and SDR-Control.

Original code is MIT licensed. Vendor dependencies retain their own terms; see [THIRD_PARTY.md](THIRD_PARTY.md).

References: [Waveshare hardware](https://www.waveshare.com/wiki/ESP32-S3-Knob-Touch-LCD-1.8) · [SDR-Control manual](https://documents.roskosch.de/sdr-control-mac/)
