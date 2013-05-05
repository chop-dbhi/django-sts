from .models import System


class transition(object):
    "Transition context manager."
    def __init__(self, obj, state, event=None, start_time=None,
            message=None, exception_fail=True, fail_state='Fail'):

        self.system = System.get(obj)
        self.transition = self.system.start_transition(event=event,
            start_time=start_time)
        self.state = state
        self.message = message
        self.exception_fail = exception_fail
        self.fail_state = fail_state

    def __enter__(self):
        return self.transition

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type and self.exception_fail:
            failed = True
        else:
            failed = False

        # Use the locally set message
        message = self.transition.message or self.message
        state = self.fail_state if failed else self.state

        # End the transition
        self.system.end_transition(state, message=message, failed=failed)
