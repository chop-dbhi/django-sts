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

        system.transition('Saved', event='Save by foobar')
        system.transition('Saved', event='Save by admin')

        self.assertEqual(len(system), 3)
        self.assertEqual(State.objects.count(), 3)
        self.assertEqual(Event.objects.count(), 3)

    def test_iteration(self):
        system = self.system

        system.transition('Shoe Buckled', event='Buckle Shoe')
        system.transition('Door Closed', event='Close Door')

        # Test iteration
        self.assertEqual([str(t.state) for t in system], [
            'Shoe Buckled',
            'Door Closed',
        ])

    def test_getitem(self):
        system = self.system

        self.assertEqual(system[:3], [])
        self.assertEqual(system[2:3], [])
        self.assertRaises(IndexError, system.__getitem__, 5)
        self.assertRaises(IndexError, system.__getitem__, slice(None, None, 2))
        self.assertRaises(ValueError, system.__getitem__, slice(None, None))

        for i in range(1, 6):
            system.transition('Count {}'.format(i), event='Incr 1')

        # Don't be confused.. indexing is zero-based, while counting is 1-based
        self.assertEqual([str(t.state) for t in system[:3]],
            ['Count 1', 'Count 2', 'Count 3'])

        self.assertEqual([str(t.state) for t in system[-3:]],
            ['Count 3', 'Count 4', 'Count 5'])

        self.assertEqual([str(t.state) for t in system[:-3]],
            ['Count 1', 'Count 2'])

        self.assertEqual([str(t.state) for t in system[1:3]],
            ['Count 2', 'Count 3'])

        self.assertEqual(str(system[3].state), 'Count 4')

        self.assertEqual(str(system[-1].state), 'Count 5')

        # Bad slices..
        self.assertEqual(system[-1:-3], [])
        self.assertEqual(system[-1:2], [])
        self.assertEqual(system[1:1], [])

    def test_shortcuts(self):
        from django.contrib.auth.models import User
        from sts.shortcuts import transition, start_transition, end_transition

        user = User.objects.create_user(username='test', password='test',
            email='test@example.com')

        transition(user, 'Creating User', 'User Created')
        start_transition(user, 'Creating User')
        end_transition(user, 'User Created')

    def test_context_manager(self):
        from sts.contextmanagers import transition

        with transition('Sleeper', 'Awake', event='Nap'):
            time.sleep(2)

        system = System.objects.get(name='Sleeper')
        self.assertEqual(system.current_state().name, 'Awake')

        trans = system[0]
        self.assertTrue(2000 < trans.duration < 3000)


        with transition('Sleeper', 'Awake', event='Nap', fail_state='Annoyed'):
            raise Exception

        self.assertEqual(system.current_state().name, 'Annoyed')
