#!/usr/bin/env python3
"""Fetch pinned Waveshare dependencies into ignored directories."""
import argparse
import hashlib
from pathlib import Path
import re
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://files.waveshare.com/wiki/ESP32-S3-Knob-Touch-LCD-1.8/ESP32-S3-Knob-Touch-LCD-1.8-Demo.zip'
SHA256 = '11e382444fe93470fbe463829c1e0ebad5bdb5115fd2d72f6159cd7700015030'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, help='Use a previously downloaded official demo ZIP')
    args = parser.parse_args()
    vendor = ROOT / '.vendor'
    vendor.mkdir(exist_ok=True)
    archive = args.archive or vendor / 'demo.zip'
    if not archive.exists():
        urllib.request.urlretrieve(URL, archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise SystemExit('Vendor archive checksum mismatch; review upstream changes before updating the pin.')
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name.endswith('/'):
                continue
            if '/Arduino/libraries/' in name:
                relative = Path(name.split('/Arduino/libraries/', 1)[1])
                if '..' in relative.parts or relative.is_absolute():
                    raise ValueError('Unsafe archive path')
                out = vendor / 'libraries' / relative
            elif '/Arduino/examples/08_LVGL_Test/' in name and not name.endswith('.ino'):
                out = ROOT / 'RadioKnob' / Path(name).name
            elif '/Arduino/examples/04_Encoder_Test/' in name and Path(name).name in ('bidi_switch_knob.c', 'bidi_switch_knob.h'):
                out = ROOT / 'RadioKnob' / Path(name).name
            else:
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(z.read(name))
    for name in ('lcd_bsp.c', 'lcd_bsp.h'):
        p = ROOT / 'RadioKnob' / name
        s = p.read_text().replace('static bool example_lvgl_lock', 'bool example_lvgl_lock').replace('static void example_lvgl_unlock', 'void example_lvgl_unlock').replace('lv_demo_widgets();', '/* UI supplied by RadioKnob.ino */')
        p.write_text(s)
    p = vendor / 'libraries/lv_conf.h'
    s = p.read_text()
    for font in (20, 28, 32):
        s = re.sub(r'(#define LV_FONT_MONTSERRAT_'+str(font)+r'\s+)0', r'\g<1>1', s)
    p.write_text(s)
    print('Vendor drivers and LVGL prepared.')

if __name__ == '__main__':
    main()
