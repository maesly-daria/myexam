import os

import django
from django.contrib.admin.models import LogEntry
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base_relaction.settings")
django.setup()


# Удаление всех записей старше 30 дней
LogEntry.objects.filter(
    action_time__lt=timezone.now() - timezone.timedelta(days=30)
).delete()
print("Old log entries have been deleted.")
