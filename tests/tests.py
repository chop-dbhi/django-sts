import time
from django.test import TestCase
from sts.models import STSError, System, State, Event


__all__ = ('StateTestCase', 'SystemTestCase')


class StateTestCase(TestCase):
    def test_get(self):
        # Create (or get) by name
        state = State.get('foo')

        self.assertTrue(state.pk is not None)

        # Get by pk
        self.assertEqual(state, State.get(state.pk))

        # Return an instance
        self.assertEqual(state, State.get(state))


class SystemTestCase(TestCase):
    def setUp(self):
        self.system = System()
        self.system.save()

    def test_simple(self):
        system = self.system

        system.transition('Initialize', 'Initialized')
        self.assertEqual(len(system), 1)

    def test_long(self):
        system = self.system

        # Specify the event..
        system.start_transition('Initialize')

        self.assertTrue(system.in_transition())
        self.assertEqual(system.current_state(), State.TRANSITION)
        self.assertEqual(len(system), 1)
        self.assertRaises(STSError, system.start_transition, 'Initialize')

        # Sleep for 2 seconds..
        time.sleep(2)

        # Specify the state..
        trans = system.end_transition('Initialized')

        self.assertTrue(trans.duration, 2)
        self.assertFalse(system.in_transition())
        self.assertEqual(system.current_state().name, 'Initialized')
        self.assertEqual(len(system), 1)
        self.assertRaises(STSError, system.end_transition, 'Initialized')

        system.transition('Save by foobar', 'Saved')
        system.transition('Save by admin', 'Saved')

        self.assertEqual(len(system), 3)
        self.assertEqual(State.objects.count(), 3)
        self.assertEqual(Event.objects.count(), 3)

    def test_iteration(self):
        system = self.system

        system.transition('Buckle Shoe', 'Shoe Buckled')
        system.transition('Close Door', 'Door Closed')

        # Test iteration
        self.assertEqual([str(t.state) for t in system], [
            'Shoe Buckled',
            'Door Closed',
        ])
