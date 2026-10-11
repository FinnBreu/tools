from pathlib import Path
import unittest
from unittest.mock import patch

from tools.export_csv import _filter_fields, _topic_profile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class ExportCsvTest(unittest.TestCase):
    def test_thruster_profile_resolves_topics_and_fields(self):
        with patch(
            'tools.export_csv.get_package_share_directory',
            return_value=str(PACKAGE_ROOT),
        ):
            profile = _topic_profile('thruster_loadcell', 'uuv02')

        self.assertEqual(
            profile['topics'],
            [
                '/uuv02/thruster_command',
                '/uuv02/loadcell/wrench',
                '/uuv02/battery_state',
            ],
        )
        self.assertEqual(
            profile['fields']['/uuv02/thruster_command'],
            ['control.0'],
        )
        self.assertEqual(
            profile['fields']['/uuv02/battery_state'],
            ['voltage'],
        )

    def test_filter_fields_keeps_only_profile_selection(self):
        values = {'voltage': 14.8, 'current': 2.0, 'percentage': 0.75}

        filtered = _filter_fields(
            '/uuv02/battery_state',
            values,
            {'/uuv02/battery_state': ['voltage']},
        )

        self.assertEqual(filtered, {'voltage': 14.8})

    def test_filter_fields_rejects_a_stale_profile(self):
        with self.assertRaisesRegex(ValueError, 'missing'):
            _filter_fields('/topic', {'value': 1}, {'/topic': ['missing']})


if __name__ == '__main__':
    unittest.main()
