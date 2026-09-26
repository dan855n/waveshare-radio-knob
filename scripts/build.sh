#!/bin/bash
set -eu
cd "$(dirname "$0")/.."
CLI="${ARDUINO_CLI:-arduino-cli}"
args=()
if [ -n "${ARDUINO_CONFIG:-}" ]; then args+=(--config-file "$ARDUINO_CONFIG"); fi
"$CLI" compile "${args[@]}" --fqbn 'esp32:esp32:esp32s3:USBMode=default,CDCOnBoot=cdc,PSRAM=opi,FlashSize=16M,PartitionScheme=huge_app' --library "$PWD/.vendor/libraries/lvgl" --build-path "$PWD/.build" --output-dir "$PWD/dist" "$PWD/RadioKnob"
