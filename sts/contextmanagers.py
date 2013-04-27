from .models import System


class transition(object):
    "Transition context manager."
    def __init__(self, obj, state, event=None, start_time=None,
            message=None, exception_fail=True):

        self.system = System.get(obj)
        self.transition = self.system.start_transition(event=event,
            start_time=start_time)
        self.state = state
        self.message = message
        self.exception_fail = exception_fail

    def __enter__(self):
        return self.transition

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type and self.exception_fail:
            failed = True
        else:
            failed = None

        # Use the locally set message
        message = self.transition.message or self.message

        # End the transition
        self.system.end_transition(self.state, message=message, failed=failed)
