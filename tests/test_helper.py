import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

path = Path(__file__).resolve().parents[1] / 'mac-helper/radio_display.py'
spec = importlib.util.spec_from_file_location('radio_display', path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

class HelperTests(unittest.TestCase):
    def test_frequency(self):
        self.assertEqual(helper.parse_frequency(b'14379150\n'), 14379150)
        for bad in (b'', b'RPRT -1\n', b'0', b'1000000000', b'14.379', b'-1'):
            with self.assertRaises(ValueError):
                helper.parse_frequency(bad)

    def test_only_selected_device_is_opened(self):
        helper.DEVICE_SERIAL = 'TEST123'
        ports = [SimpleNamespace(serial_number='OTHER', device='wrong'), SimpleNamespace(serial_number='test123', device='right')]
        with patch.object(helper.list_ports, 'comports', return_value=ports), patch.object(helper.serial, 'Serial') as serial:
            result = helper.open_dial()
            self.assertEqual(result.port, 'right')
            result.open.assert_called_once()

    def test_missing_device(self):
        with patch.object(helper.list_ports, 'comports', return_value=[]):
            with self.assertRaises(OSError):
                helper.open_dial()

if __name__ == '__main__':
    unittest.main()
