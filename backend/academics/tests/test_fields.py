from datetime import datetime

from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from academics.fields import ScheduleDateTimeField


@override_settings(TIME_ZONE='Europe/Kyiv', USE_TZ=True)
class ScheduleDateTimeFieldTests(SimpleTestCase):
    def test_naive_input_preserves_wall_clock_time(self):
        field = ScheduleDateTimeField()

        value = field.to_internal_value('2026-01-15T10:30:00')

        self.assertEqual(
            timezone.localtime(value).replace(tzinfo=None),
            datetime(2026, 1, 15, 10, 30),
        )
        self.assertEqual(field.to_representation(value), '2026-01-15T10:30:00')

    def test_timezone_suffix_does_not_shift_wall_clock_time(self):
        field = ScheduleDateTimeField()

        value = field.to_internal_value('2026-01-15T10:30:00-08:00')

        self.assertEqual(
            timezone.localtime(value).replace(tzinfo=None),
            datetime(2026, 1, 15, 10, 30),
        )
