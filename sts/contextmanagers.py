from contextlib import contextmanager
from django.conf import settings
from .models import System

DEFAULT_FAIL_STATE = getattr(settings, 'STS_FAIL_STATE', 'Fail')

@contextmanager
def transition(obj, state, event=None, start_time=None, fail_state=DEFAULT_FAIL_STATE):
    "Transition context manager."
    system = System.get(obj)
    try:
        system.start_transition(event=event, start_time=start_time)
        yield
        system.end_transition(state)
    except Exception:
        system.end_transition(fail_state)
