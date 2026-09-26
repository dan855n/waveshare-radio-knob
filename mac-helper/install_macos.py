#!/usr/bin/env python3
"""Install the helper as a per-user macOS login service."""
import argparse
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import serial

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--serial', required=True)
args = parser.parse_args()
label = 'local.dan.radio-knob-display'
target = Path.home() / 'Library/Application Support/RadioKnob'
target.mkdir(parents=True, exist_ok=True)
shutil.copy2(Path(__file__).with_name('radio_display.py'), target)
shutil.copytree(Path(serial.__file__).parent, target / 'serial', dirs_exist_ok=True)
plist = Path.home() / 'Library/LaunchAgents' / (label + '.plist')
plist.parent.mkdir(parents=True, exist_ok=True)
config = {'Label': label, 'ProgramArguments': ['/usr/bin/python3', '-u', str(target / 'radio_display.py'), '--serial', args.serial], 'RunAtLoad': True, 'KeepAlive': True, 'ThrottleInterval': 10, 'StandardOutPath': str(target / 'helper.log'), 'StandardErrorPath': str(target / 'helper.log')}
plist.write_bytes(plistlib.dumps(config))
domain = f'gui/{os.getuid()}'
subprocess.run(['launchctl', 'bootout', domain + '/' + label], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['launchctl', 'bootstrap', domain, str(plist)], check=True)
print(f'Installed. Status and logs: {target}')
