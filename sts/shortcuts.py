from django.contrib.contenttypes.models import ContentType
from .models import System


def _get_sts(obj):
    "Returns a System instance representing this object."
    ct = ContentType.objects.get_for_model(obj.__class__)
    return System.objects.get_or_create(content_type=ct, object_id=obj.pk)[0]

def transition(obj, *args, **kwargs):
    "Creates an immediate state transition."
    _get_sts(obj).transition(*args, **kwargs)

def start_transition(obj, *args, **kwargs):
    "Starts a state transition given some event."
    _get_sts(obj).start_transition(*args, **kwargs)

def end_transition(obj, *args, **kwargs):
    "Ends a state transition with some state."
    _get_sts(obj).end_transition(*args, **kwargs)
