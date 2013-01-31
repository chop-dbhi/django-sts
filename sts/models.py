from datetime import datetime
from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType
from django.utils.timesince import timesince
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

    @transaction.commit_on_success
    def __getitem__(self, idx):
        queryset = self.transitions.order_by('start_time')
        if isinstance(idx, slice):
            if idx.step is not None:
                raise IndexError('Index stepping is not supported.')

            if idx.start is None and idx.stop is None:
                raise ValueError('List cloning is not supported.')

            if idx.start is not None and idx.stop is not None:
                # Backwards..
                if idx.stop < idx.start  or idx.start < 0 and idx.stop > 0:
                    return []

                # Equal, nothing to do
                if idx.stop == idx.start:
                    return []

            # Negative indexing.. QuerySets don't support these, so we take it
            # from the front and reverse it.
            if idx.start is not None and idx.start < 0:
                if idx.stop is None:
                    start = None
                    stop = abs(idx.start)
                else:
                    start = abs(idx.stop)
                    stop = abs(idx.stop + idx.start)

                idx = slice(start, stop)
                trans = list(queryset.order_by('-start_time')[idx])
                trans.reverse()
            elif idx.stop is not None and idx.stop < 0:
                start = idx.start
                stop = self.length + idx.stop
                idx = slice(start, stop)
                trans = list(queryset[idx])
            else:
                trans = list(queryset[idx])
        else:
            try:
                trans = queryset[idx]
            except Transition.DoesNotExist:
                raise IndexError
        return trans

    def __iter__(self):
        for transition in self.transitions.iterator():
            yield transition

    @classmethod
    def get(cls, obj_or_name, save=True):
        "Returns a System instance representing this object."
        # Already an instance
        if isinstance(obj_or_name, cls):
            return obj_or_name

        # String, so get or create a system by this name
        if isinstance(obj_or_name, basestring):
            system, created = cls.objects.get_or_create(name=obj_or_name)
            return system

        # Fallback to model object
        obj = obj_or_name

        if not isinstance(obj, models.Model):
            raise TypeError('This classmethod only supports get Systems for model objects.')
        if not obj.pk:
            raise ValueError('Model object has no primary key.')
        ct = ContentType.objects.get_for_model(obj.__class__)
        try:
            obj = cls.objects.get(content_type=ct, object_id=obj.pk)
        except cls.DoesNotExist:
            obj = cls(content_type=ct, object_id=obj.pk)
            if save:
                obj.save()
        return obj

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
    def start_transition(self, event=None, start_time=None, save=True):
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

        # Convert to milliseconds
        duration = int(round((end_time - transition.start_time).total_seconds() * 1000))

        transition.state = state
        transition.end_time = end_time
        transition.duration = duration

        if save:
            transition.save()

        return transition

    @transaction.commit_on_success
    def transition(self, state, event=None, start_time=None, end_time=None, save=True):
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

        # Convert to milliseconds
        duration = int(round((end_time - start_time).total_seconds() * 1000))

        transition = Transition(system=self, event=event, duration=duration,
            state=state, start_time=start_time, end_time=end_time)

        if save:
            transition.save()

        return transition


class Transition(models.Model):
    # The system this transition applies to
    system = models.ForeignKey(System, related_name='transitions')

    # The event that caused the state change
    event = models.ForeignKey(Event, null=True, blank=True, related_name='transitions')

    # The resulting state from this transition
    state = models.ForeignKey(State, related_name='transitions')

    # Transition start/end time
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    duration = models.PositiveIntegerField('duration in milliseconds', null=True, blank=True)

    class Meta(object):
        ordering = ('start_time',)

    def __unicode__(self):
        if self.event_id:
            text = '{} => {}'.format(self.event, self.state)
        else:
            text = unicode(self.state)
        if self.duration:
            text = '{} ({})'.format(text, self.natural_duration)
        elif self.in_transition():
            text = '{} (in transition)'.format(text)
        return text

    def in_transition(self):
        return self.state_id == State.TRANSITION.pk

    @property
    def natural_duration(self):
        if not self.duration:
            return
        if self.duration < 1000:
            return '{} milliseconds'.format(self.duration)
        if self.duration < 60000:
            return '{} seconds'.format(int(round(self.duration / 1000.0)))
        return timesince(self.start_time, self.end_time)


class STSModel(models.Model):
    "Augments model for basic object state transitions."

    def transition(self, *args, **kwargs):
        "Creates an immediate state transition."
        if not hasattr(self, '_sts'):
            self._sts = System.get(self)
        self._sts.transition(*args, **kwargs)

    def start_transition(self, *args, **kwargs):
        "Starts a state transition given some event."
        if not hasattr(self, '_sts'):
            self._sts = System.get(self)
        self._sts.start_transition(*args, **kwargs)

    def end_transition(self, *args, **kwargs):
        "Ends a state transition with some state."
        if not hasattr(self, '_sts'):
            self._sts = System.get(self)
        self._sts.end_transition(*args, **kwargs)

    class Meta(object):
        abstract = True
