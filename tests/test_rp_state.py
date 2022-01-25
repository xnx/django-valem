from django.core.exceptions import ValidationError
from django.test import TestCase

from rp.models import State, Species, RP


class TestState(TestCase):
    def setUp(self):
        self.test_species = Species.objects.create(text="H", html="H")
        self.test_rp = RP.objects.create(species=self.test_species)
        self.test_state_kwargs = {
            "rp": self.test_rp,
            "state_type": 0,
            "text": "n=1",
            "html": "n=1",
        }

    def test_instantiation(self):
        State(**self.test_state_kwargs)
        State()

    def test_instance_creation_succeeds(self):
        self.assertEqual(len(State.objects.all()), 0)
        state = State.objects.create(**self.test_state_kwargs)
        self.assertEqual(len(State.objects.all()), 1)
        for kwarg, val in self.test_state_kwargs.items():
            self.assertEqual(getattr(State.objects.get(pk=state.pk), kwarg), val)
        self.assertIs(self.test_rp, state.rp)

    def test_unsupported_state_type(self):
        unsupported_state_types = [-1, 15]
        supported_state_types = [0, 1]
        for state_type in unsupported_state_types:
            kwargs = dict(self.test_state_kwargs, state_type=state_type)
            state = State(**kwargs)
            with self.subTest(state_type=state_type):
                with self.assertRaises(ValidationError):
                    state.clean_fields()
        for state_type in supported_state_types:
            kwargs = dict(self.test_state_kwargs, state_type=state_type)
            state = State(**kwargs)
            state.clean_fields()
            state.save()
            self.assertEqual(State.objects.get(pk=state.pk).state_type, state_type)
        self.assertEqual(len(State.objects.all()), len(supported_state_types))

    def test_str(self):
        self.assertEqual(
            str(State.objects.create(**self.test_state_kwargs)),
            self.test_state_kwargs["text"],
        )

    def test_repr(self):
        st = State.objects.create(**self.test_state_kwargs)
        self.assertEqual(repr(st), f"<S{st.pk}: n=1>")

    def test_cascade_delete(self):
        # deletion of an RP will delete all its States
        states_created = 3
        for _ in range(states_created):
            State.objects.create(**self.test_state_kwargs)
        num_rps = len(RP.objects.all())
        num_states = len(State.objects.all())
        self.test_rp.delete()
        self.assertEqual(len(RP.objects.all()), num_rps - 1)
        self.assertEqual(len(State.objects.all()), num_states - states_created)

    def test_cascade_delete_reversed(self):
        # deletion of a State will NOT delete it's RP
        state = State.objects.create(**self.test_state_kwargs)
        num_rps = len(RP.objects.all())
        num_states = len(State.objects.all())
        state.delete()
        self.assertEqual(len(State.objects.all()), num_states - 1)
        self.assertEqual(len(RP.objects.all()), num_rps)
