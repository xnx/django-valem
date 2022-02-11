from django.test import TestCase
from pyvalem.formula import FormulaParseError
from pyvalem.states import StateParseError
from pyvalem.stateful_species import StatefulSpeciesError

from rp.models import Species, RP, State


# noinspection PyTypeChecker
class TestRP(TestCase):
    valid_states = {
        "n=1": 0,
        "**": 1,
        "1s2.2s1": 2,
        "2Po_1/2": 3,
        "1σu2": 4,
        "1Σ-": 5,
        "v=1": 6,
        "J=3/2": 10,
        # what about the Racah symbol?
    }
    valid_species = {
        "T",
        "H2",
        "D2-",
        "C3H8+2",
        "(235U)",
        "(1H)2(16O)",
        "ortho-C6H4(CH3)2",
    }
    invalid_species = ["foo"]
    invalid_states = ["foo"]

    def setUp(self):
        self.test_species = Species.objects.create(text="H", html="H")
        self.test_state1_kwargs = {"state_type": 0, "text": "n=1", "html": "n=1"}
        self.test_state2_kwargs = {"state_type": 1, "text": "**", "html": "**"}

    def test_raw_instantiation(self):
        rp = RP.objects.create(species=self.test_species)
        self.assertIs(rp.species, self.test_species)
        self.assertEqual(len(rp.state_set.all()), 0)

    def test_raw_states_assign(self):
        rp = RP.objects.create(species=self.test_species)
        State(rp=rp, **self.test_state1_kwargs).save()
        self.assertEqual(len(rp.state_set.all()), 1)
        # duplicate states are allowed by the raw django API
        State(rp=rp, **self.test_state1_kwargs).save()
        self.assertEqual(len(rp.state_set.all()), 2)

    def test_get_from_text_raises(self):
        # getting non-existing RP instances raises DoesNotExist errors
        for rp_text in [
            f"{species} {state}"
            for species in self.valid_species
            for state in self.valid_states
        ]:
            with self.subTest(text=rp_text):
                # noinspection PyTypeChecker
                with self.assertRaises(RP.DoesNotExist):
                    RP.get_from_text(rp_text)

    def test_get_from_text_non_existing(self):
        # getting RP instance from string with either non-existing species, or
        # without all states, raises DoesNotExist
        rp = RP.objects.create(species=self.test_species)
        state1 = State.objects.create(rp=rp, **self.test_state1_kwargs)
        state2 = State.objects.create(rp=rp, **self.test_state2_kwargs)
        non_existing_rp_texts = [
            f"{rp.species.text}",  # no states
            f"{rp.species.text} {state1.text}",  # only the first state
            f"{rp.species.text} {state2.text}",  # only the second state
            f"W+42 {state1.text};{state2.text}",  # corr. states, non-exist. sp
        ]  # those are all valid pyvalem-parsable RP text examples
        for rp_text in non_existing_rp_texts:
            with self.subTest(rp_text=rp_text):
                # noinspection PyTypeChecker
                with self.assertRaises(RP.DoesNotExist):
                    RP.get_from_text(rp_text)

    def test_get_from_text_existing(self):
        # get_from_text should not care about the order of the states!
        RP.get_or_create_from_text("H2+ v=2;3SIGMA+g")
        existing_rp_texts = ["H2+ v=2;3SIGMA+g", "H2+ 3Σ+g; v=2"]
        for rp_text in existing_rp_texts:
            with self.subTest(rp_text=rp_text):
                RP.get_from_text(rp_text)

    def test_get_or_create_from_text_one_state(self):
        # RP creating
        rp_text = "H2+ *"
        rp, created = RP.get_or_create_from_text(rp_text)
        self.assertTrue(created)
        self.assertEqual(len(RP.objects.all()), 1)
        # check the RP instance:
        self.assertEqual(rp.species.text, "H2+")
        self.assertEqual(rp.species.html, "H<sub>2</sub><sup>+</sup>")
        self.assertEqual(rp.species.charge, 1)
        self.assertEqual(rp.state_set.get().text, "*")
        self.assertEqual(rp.state_set.get().html, "<sup>*</sup>")
        self.assertEqual(rp.state_set.get().state_type, State.GENERIC_EXCITED_STATE)

    def test_get_or_create_from_text_swap_states(self):
        # RP get_or_creating multiple times with swapped states will not result
        # in multiple RP instances.
        rp_text = "H2 *;n=1;v=1"
        self.assertEqual(len(RP.objects.all()), 0)
        rp, created = RP.get_or_create_from_text(rp_text)
        self.assertTrue(created)
        num_rps = 1
        self.assertEqual(len(RP.objects.all()), num_rps)
        num_species = len(Species.objects.all())
        num_states = len(State.objects.all())
        # check the RP instance:
        for states_combo in [
            "*;n=1;v=1",
            "*;v=1;n=1",
            "n=1;v=1;*",
            "n=1;*;v=1",
            "v=1;*;n=1",
            "v=1;n=1;*",
        ]:
            rp_new, created = RP.get_or_create_from_text(f"H2 {states_combo}")
            self.assertEqual(rp_new, rp)
            self.assertFalse(created)
        # no new species, states or rp instances created:
        self.assertEqual(len(RP.objects.all()), num_rps)
        self.assertEqual(len(State.objects.all()), num_states)
        self.assertEqual(len(Species.objects.all()), num_species)

    def test_get_or_create_from_text_existing_species(self):
        # The existing Species instance is not re-created by
        # RP.get_or_create_from_text
        species_text = "W+42"
        Species.objects.create(text=species_text)
        num_species = len(Species.objects.all())
        num_states = len(State.objects.all())
        # Create RP instance with existing species
        _, created = RP.get_or_create_from_text(f"{species_text} key=value")
        self.assertTrue(created)
        # No new species were created
        self.assertEqual(len(Species.objects.all()), num_species)
        # New states were created
        self.assertEqual(len(State.objects.all()), num_states + 1)

    def test_get_or_create_from_invalid_text(self):
        # Testing that couple of invalid text cases raise the appropriate
        # pyvalem exceptions.
        for species_text in self.invalid_species:
            for state_text in self.valid_states:
                with self.assertRaises(FormulaParseError):
                    RP.get_or_create_from_text(f"{species_text} {state_text}")
        for species_text in self.valid_species:
            for state_text in self.invalid_states:
                with self.assertRaises(StateParseError):
                    RP.get_or_create_from_text(f"{species_text} {state_text}")
        with self.assertRaises(StatefulSpeciesError):
            RP.get_or_create_from_text("H2 *;***")
        with self.assertRaises(StatefulSpeciesError):
            RP.get_or_create_from_text("H 1s1;2p1")

    def test_text_attribute(self):
        rp_text = "(235U) l=0;n=1;***"
        rp, _ = RP.get_or_create_from_text(rp_text)
        text = rp.text
        rp.delete()
        with self.assertRaises(RP.DoesNotExist):
            RP.get_from_text(rp_text)

        equivalent_text = "(235U) l=0;***;n=1"
        rp, created = RP.get_or_create_from_text(equivalent_text)
        self.assertTrue(created)
        text_equivalent = rp.text

        self.assertEqual(text, text_equivalent)

    def test_html_attribute(self):
        rp_text = "(235U) n=2;3P"
        rp, _ = RP.get_or_create_from_text(rp_text)
        html = rp.text
        rp.delete()
        with self.assertRaises(RP.DoesNotExist):
            RP.get_from_text(rp_text)

        equivalent_text = "(235U) 3P;n=2"
        rp, _ = RP.get_or_create_from_text(equivalent_text)
        html_equivalent = rp.text

        self.assertEqual(html, html_equivalent)

    def test_str(self):
        rp, _ = RP.get_or_create_from_text("H *")
        self.assertEqual(str(rp), rp.text)

    def test_repr(self):
        rp, _ = RP.get_or_create_from_text("H *")
        self.assertEqual(repr(rp), f"<RP{rp.pk}: H *>")

    def test_cascade_delete(self):
        # deletion of a Species will delete its RP
        RP.objects.create(species=self.test_species)
        num_species = len(Species.objects.all())
        num_rps = len(RP.objects.all())
        self.test_species.delete()
        # Of course Species was deleted:
        self.assertEqual(len(Species.objects.all()), num_species - 1)
        # RP was also deleted by the deletion cascade:
        self.assertEqual(len(RP.objects.all()), num_rps - 1)

    def test_cascade_delete_reversed(self):
        # deletion of an RP will not delete its Species
        rp = RP.objects.create(species=self.test_species)
        num_species = len(Species.objects.all())
        num_rps = len(RP.objects.all())
        rp.delete()
        self.assertEqual(len(Species.objects.all()), num_species)
        self.assertEqual(len(RP.objects.all()), num_rps - 1)

    def test_canonical_state_representation(self):
        # Existing species must be found even if I pass text with e.g. SIGMA
        # instead of Σ.
        for equivalent_strings, nstates in [
            (["H2 1sigma", "H2 1σ", "H2 1sigma1", "H2 1σ1"], 1),
            (["H2 1SIGMA-", "H2 1Σ-"], 1),
            (["H2 v=0 J=2", "H2 v=0;J=2", "H2 v=0; J=2", "H2 v=0,J=2"], 2),
            (["H2 J=3/2", "H2 J=1.5"], 1),
        ]:
            num_rps = len(RP.objects.all())
            num_states = len(State.objects.all())
            base_text = equivalent_strings[0]
            base_rp, created = RP.get_or_create_from_text(base_text)
            self.assertTrue(created)
            self.assertEqual(len(RP.objects.all()), num_rps + 1)
            self.assertEqual(len(State.objects.all()), num_states + nstates)
            for equivalent_text in equivalent_strings:
                equivalent_rp, created = RP.get_or_create_from_text(equivalent_text)
                with self.subTest(base_text=base_text, equivalent_text=equivalent_text):
                    # assert that the pulled RPs are the same
                    self.assertFalse(created)
                    self.assertEqual(equivalent_rp, base_rp)
            # assert that no new RPs and States were created
            self.assertEqual(len(RP.objects.all()), num_rps + 1)
            self.assertEqual(len(State.objects.all()), num_states + nstates)

    def test_charge(self):
        self.assertEqual(RP.get_or_create_from_text("H")[0].charge, 0)
        self.assertEqual(RP.get_or_create_from_text("H+")[0].charge, 1)
        self.assertEqual(RP.get_or_create_from_text("He+2")[0].charge, 2)
        self.assertEqual(RP.get_or_create_from_text("He-2")[0].charge, -2)
