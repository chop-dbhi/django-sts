# State Transition System (STS) for Django

[State Transition Systems][1] have less constraints than Finite State
Automata, and can be utilized for various use cases.

The core components include:

- State
- Event
- Transition
- System

**Events** cause a **transition** from some **state** to a new state within
a given **system**.

The API supports defining _immediate_ transitions and _long-running_
transitions. Now, for a riveting example..

```python
system = System(name='Example 1')
system.save()

# Immediate transition.. event => state
system.transition('Door Opened', event='Open Door')

# 'Long-running' transitions.. event happens
system.start_transition('Close Door Slowly')

# Time passes..
time.sleep(2)

# The resulting state..
system.end_transition('Door Closed')
```

A model object can be associated directly with a `System` using Django's
ContentTypes framework generic foreign keys.

```python
door = Door.objects.get(name='Door #1')
system = System(content_object=door)
# ...
```

`System` objects have a few extra conveniences:

```python
# number of transitions
len(system) == system.length

# iteration starting with the first transition
for trans in system:
    ...

# indexing and slices
system[:3]  # first 3 transitions
system[-3:] # last 3 transitions
system[:-3] # all except the last 3 transitions
system[1:3] # arbitrary slice
system[2]   # specific transition
```

This enables bringing in django-sts to an existing model to begin tracking
states of objects.

It even comes with an abstract `STSModel` that augments a model with the above
methods for seamless integration (it does not add any model fields):

```python
class Door(STSModel):
    name = models.CharField(max_length=20)

door = Door()
door.save()
door.transition('Door Closed', event='Close Door')
```

The library leaves it up to the application to implement the constraints of a
finite state automata/machine.

[1]: http://en.wikipedia.org/wiki/State_transition_system
