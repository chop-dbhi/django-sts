# State Transition System (STS) for Django

[State Transition Systems][1] have less constraints than Finite State
Automata, and can be molded into various use cases.

The core components include:

- State
- Event
- Transition
- System

**Events** cause a **transition** from some **state** (or none if this is the
first transition) to a new state for a given **system**.

The API supports defining _immediate_ transitions and _long-running_
transitions. Now, for a riveting example..

```python
system = System(name='Example 1')
system.save()

# Immediate transition.. event => state
system.transition('Open Door', 'Door Opened')

# 'Long-running' transitions.. event happens
system.start_transition('Close Door Slowly')

# Time passes..
time.sleep(2)

# The resulting state..
system.end_transition('Door Closed')
```

`System`s can also be associated directly to an object using Django's
ContentType framework.

```python
door = Door.objects.get(name='Door #1')
system = System(content_object=door)
# ...
```

This enables bringing in django-sts to an existing model to begin tracking
states of objects.

If even comes with an abstract `STSModel` that augments a model with the above
methods for seamless integration (it does not add any model fields):

```python
class Door(STSModel):
    name = models.CharField(max_length=20)

door = Door()
door.save()
door.transition('Close Door', 'Door Closed')
```

The library leaves it up to the application to implement the constraints of a
finite state automata/machine.

[1]: http://en.wikipedia.org/wiki/State_transition_system
