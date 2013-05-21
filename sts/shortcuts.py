def transition(obj, *args, **kwargs):
    "Creates an immediate state transition."
    from .models import System
    return System.get(obj).transition(*args, **kwargs)

def start_transition(obj, *args, **kwargs):
    "Starts a state transition given some event."
    from .models import System
    return System.get(obj).start_transition(*args, **kwargs)

def end_transition(obj, *args, **kwargs):
    "Ends a state transition with some state."
    from .models import System
    return System.get(obj).end_transition(*args, **kwargs)
