from datetime import datetime
from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from .utils import classproperty


class STSError(Exception):
    pass


class State(models.Model):
    "Defines a state an event can invoke."
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    @classproperty
    def TRANSITION(cls):
        if not hasattr(cls, '_transition'):
            cls._transition = cls.objects.get(pk=1)
        return cls._transition

    @classmethod
    def get(cls, name):
        if name is None:
            return
        if isinstance(name, cls):
            return name
        if isinstance(name, int):
            return cls.objects.get(pk=name)
        return cls.objects.get_or_create(name=name)[0]


class Event(models.Model):
    "Defines an event that causes a state change."
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    @classmethod
    def get(cls, name):
        if name is None:
            return
        if isinstance(name, cls):
            return name
        if isinstance(name, int):
            return cls.objects.get(pk=name)
        return cls.objects.get_or_create(name=name)[0]


class System(models.Model):
    "A state system"
    name = models.CharField(max_length=100, null=True, blank=True)

    # The object the state applies to
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    content_object = generic.GenericForeignKey()

    class Meta(object):
        ordering = ('-modified',)

    def __len__(self):
        return self.length

    def __nonzero__(self):
        return True

    def __iter__(self):
        for transition in self.transitions.all():
            yield transition

    @property
    def length(self):
        return self.transitions.count()

    def current_state(self):
        try:
            return self.transitions.select_related('state')\
                .latest('start_time').state
        except Transition.DoesNotExist:
            pass

    def in_transition(self):
        return self.transitions.filter(state=State.TRANSITION).exists()

    @transaction.commit_on_success
    def start_transition(self, event, start_time=None, save=True):
        """Creates and starts a transition if one is not already open.

        For long-running transitions, this method can be used at the start of a
        transition and then later ended with `end_transition`.
        """
        if self.in_transition():
            raise STSError('Cannot start transition while already in one.')

        event = Event.get(event)
        # No end state, therefore this state will marked as in transition
        # until the transition is finished.
        state = State.TRANSITION

        if start_time is None:
            start_time = datetime.now()

        transition = Transition(system=self, event=event, state=state,
            start_time=start_time)

        if save:
            transition.save()

        return transition

    @transaction.commit_on_success
    def end_transition(self, state, end_time=None, save=True):
        """Ends a transition that has already been started.

        For long-running transitions, this method can be used at the end of a
        transition that had been started with `start_transition`.
        """
        if not self.in_transition():
            raise STSError('Cannot end a transition while not in one.')

        state = State.get(state)

        if end_time is None:
            end_time = datetime.now()


        transition = self.transitions.get(state=State.TRANSITION)
        transition.state = state
        transition.end_time = end_time
        transition.duration = (end_time - transition.start_time).seconds

        if save:
            transition.save()

        return transition

    @transaction.commit_on_success
    def transition(self, event, state, start_time=None, end_time=None, save=True):
        """Create a transition in state. This means of transitioning is the most
        since this does not involve long-running transitions.
        """
        if self.in_transition():
            raise STSError('Cannot start transition while already in one.')

        event = Event.get(event)
        state = State.get(state)

        # No end state, therefore this state will marked as in transition
        # until the transition is finished.
        if state is None or state == State.TRANSITION:
            raise STSError('Cannot create a transition with an empty state.')

        now = datetime.now()

        if start_time is None:
            start_time = now

        if end_time is None:
            end_time = now

        duration = (end_time - start_time).seconds

        transition = Transition(system=self, event=event, duration=duration,
            state=state, start_time=start_time, end_time=end_time)

        if save:
            transition.save()

        return transition


class Transition(models.Model):
    # The system this transition applies to
    system = models.ForeignKey(System, related_name='transitions')

    # The event that caused the state change
    event = models.ForeignKey(Event, related_name='transitions')

    # The resulting state from this transition
    state = models.ForeignKey(State, related_name='transitions')

    # Transition start/end time
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    duration = models.PositiveIntegerField(null=True, blank=True)

    class Meta(object):
        ordering = ('start_time',)

    def __unicode__(self):
        return '{} => {}'.format(self.event, self.state)

    def in_transition(self):
        return self.state_id == State.TRANSITION.pk


class STSModel(models.Model):
    "Augments model for basic object state transitions."

    def get_sts(self):
        "Returns a System instance representing this object."
        return System.objects.get_or_create(content_object=self)

    def transition(self, *args, **kwargs):
        "Creates an immediate state transition."
        if not hasattr(self, '_sts'):
            self._sts = self.get_sts()
        self._sts.transition(*args, **kwargs)

    def start_transition(self, *args, **kwargs):
        "Starts a state transition given some event."
        if not hasattr(self, '_sts'):
            self._sts = self.get_sts()
        self._sts.start_transition(*args, **kwargs)

    def end_transition(self, *args, **kwargs):
        "Ends a state transition with some state."
        if not hasattr(self, '_sts'):
            self._sts = self.get_sts()
        self._sts.end_transition(*args, **kwargs)

    class Meta(object):
        abstract = True
