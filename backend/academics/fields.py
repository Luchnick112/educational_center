from datetime import datetime

from django.utils import timezone
from rest_framework import serializers


class ScheduleDateTimeField(serializers.DateTimeField):
    """Treat schedule datetimes as wall-clock values in the app timezone."""

    def to_internal_value(self, value):
        if isinstance(value, str):
            value = value.strip()
            try:
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                self.fail('invalid', format='ISO-8601 datetime')

            parsed = parsed.replace(tzinfo=None)
            return timezone.make_aware(parsed, timezone.get_default_timezone())

        return super().to_internal_value(value)

    def to_representation(self, value):
        if value is None:
            return None

        if timezone.is_aware(value):
            value = timezone.localtime(value, timezone.get_default_timezone())
        return value.replace(tzinfo=None).isoformat(timespec='seconds')
