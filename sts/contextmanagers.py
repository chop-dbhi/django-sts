from django.conf import settings
from .models import System

DEFAULT_FAIL_STATE = getattr(settings, 'STS_FAIL_STATE', 'Fail')


class transition(object):
    "Transition context manager."
    def __init__(self, obj, state, event=None, start_time=None, message=None,
            fail_state=DEFAULT_FAIL_STATE):
        self.system = System.get(obj)
        self.transition = self.system.start_transition(event=event,
            start_time=start_time)

        self.state = state
        self.fail_state = fail_state
        self.message = message

    def __enter__(self):
        return self.transition

    def __exit__(self, exc_type, exc_value, traceback):
        # Use the fail state if an exception occurred
        state = self.fail_state if exc_type else self.state
        # Use the locally set message
        message = self.transition.message or self.message
        # End the transition
        self.system.end_transition(state, message=message)
