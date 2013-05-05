import re
from django.utils import timezone
from django.utils.timesince import timesince


short_units = {
    'ms': re.compile(' ?milliseconds?'),
    's': re.compile(' ?seconds?'),
    'm': re.compile(' ?minutes?'),
    'h': re.compile(' ?hours?'),
    'd': re.compile(' ?days?'),
    'wk': re.compile(' ?weeks?'),
    'mth': re.compile(' ?months?'),
    'y': re.compile(' ?years?'),
}


class classproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


def get_duration(start_time, end_time=None):
    "Returns the duration in milliseconds between two times."
    if end_time is None:
        end_time = timezone.now()
    return int(round((end_time - start_time).total_seconds() * 1000))


def get_natural_duration(start_time, end_time=None, short=False):
    "Returns the natural duration down the milliseconds."
    if end_time is None:
        end_time = timezone.now()

    duration = int(round((end_time - start_time).total_seconds() * 1000))

    if duration < 1000:
        return '{0} milliseconds'.format(duration)
    if duration < 60000:
        return '{0} seconds'.format(int(round(duration / 1000.0)))
    since = timesince(start_time, end_time)

    if short:
        for short, regex in short_units.items():
            since = regex.sub(short, since)
    return since


