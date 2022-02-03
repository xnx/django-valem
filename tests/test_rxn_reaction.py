import warnings

from django.test import TestCase
from pyvalem.reaction import Reaction as PVReaction

from rp.models import RP, Species, State
from rxn.models import Reaction, ProcessType, ReactantList, ProductList


class TestReaction(TestCase):
    def setUp(self):
        self.pt_hds = ProcessType.objects.create(
            abbreviation="HDS",
            description="Dissociation",
            example_html="A + BC → A + B + C",
        )
        self.pt_oth = ProcessType.objects.create(
            abbreviation="___", description="", example_html=""
        )
        ProcessType.objects.create(
            abbreviation="ENI",
            description="Negative Ion Formation",
            example_html="e- + A → A-",
        )
        ProcessType.objects.create(
            abbreviation="EDS",
            description="Electron-Impact Dissociation",
            example_html="e- + AB → A + B + e-",
        )

    def test_all_from_text_single(self):
        r_str = "H + H + He -> H + H **;n=2 + He *;n=0"
        self.assertEqual(len(Reaction.all_from_text(r_str)), 0)
        self.assertEqual(len(RP.objects.all()), 0)

        pyvalem_reaction = PVReaction(r_str)

        r = Reaction.objects.create(
            text=repr(pyvalem_reaction), html=pyvalem_reaction.html
        )
        for _, pyvalem_stateful_species in pyvalem_reaction.reactants:
            ReactantList.objects.create(
                reaction=r,
                rp=RP.get_or_create_from_text(repr(pyvalem_stateful_species)),
            )
        for _, pyvalem_stateful_species in pyvalem_reaction.products:
            ProductList.objects.create(
                reaction=r,
                rp=RP.get_or_create_from_text(repr(pyvalem_stateful_species)),
            )
        r.process_types.add(self.pt_oth)

        for r_text in [
            "2H + He -> H + H **;n=2 + He *;n=0",
            "H + H + He -> H + H **;n=2 + He *;n=0",
            "2H + He -> H + H n=2;** + He *;n=0",
            "2H + He -> H + H n=2;** + He n=0;*",
            "H + H + He -> H + H n=2;** + He n=0;*",
        ]:
            with self.subTest(r_text=r_text):
                self.assertEqual(len(Reaction.all_from_text(r_text)), 1)

        self.assertEqual(len(RP.objects.all()), 4)
        self.assertEqual(len(Species.objects.all()), 2)

    def test_all_from_text_multiple(self):
        Reaction.create_from_text("He + H + H -> 2H + He *;n=2")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            Reaction.create_from_text("He + 2H -> H + H + He *;n=2")
            Reaction.create_from_text("He + 2H -> 2H + He *;n=2")
            Reaction.create_from_text("He + 2H -> 2H + He n=2;*")
        self.assertEqual(len(Reaction.all_from_text("He + 2H -> 2H + He n=2;*")), 4)
        self.assertEqual(len(Reaction.objects.all()), 4)

    def test_all_from_text_non_existent(self):
        self.assertEqual(len(Reaction.all_from_text("H + H -> H + H")), 0)

    def test_create_duplicate_warning(self):
        Reaction.create_from_text("H + H -> H + H", comment="foo")
        with self.assertWarns(UserWarning):
            Reaction.create_from_text("2H -> 2H", comment="foo")
        self.assertEqual(len(Reaction.all_from_text("H + H -> 2H")), 2)
        self.assertEqual(len(RP.objects.all()), 1)

    def test_create_non_existing_rps(self):
        RP.get_or_create_from_text("He *;n=2")
        self.assertEqual(len(RP.objects.all()), 1)
        self.assertEqual(len(State.objects.all()), 2)
        self.assertEqual(len(Species.objects.all()), 1)
        self.assertEqual(len(Reaction.objects.all()), 0)

        Reaction.create_from_text("He n=2;* + 2H -> H + H + He n=2;*")
        self.assertEqual(len(RP.objects.all()), 2)
        self.assertEqual(len(State.objects.all()), 2)
        self.assertEqual(len(Species.objects.all()), 2)
        self.assertEqual(len(Reaction.objects.all()), 1)

    def test_get_or_create_rxn(self):
        r1, created = Reaction.get_or_create_from_text(
            "H2 + e- -> H + H-", comment="the first"
        )
        self.assertEqual(str(r1), "e- + H2 → H + H-")
        self.assertTrue(created)
        r2, created = Reaction.get_or_create_from_text(
            "e- + H2 -> H + H-", comment="the first"
        )
        self.assertEqual(r1, r2)
        self.assertFalse(created)
        r3, created = Reaction.get_or_create_from_text(
            "H2 + e- -> H + H-", comment="the second"
        )
        self.assertNotEqual(r1, r3)
        self.assertTrue(created)

        r1, created = Reaction.get_or_create_from_text(
            "H2 + e- -> H + H-", process_type_abbreviations=("EDS",)
        )
        self.assertEqual(str(r1), "e- + H2 → H + H-")
        self.assertTrue(created)
        r2, created = Reaction.get_or_create_from_text(
            "H2 + e- -> H + H-", process_type_abbreviations=("EDS",)
        )
        self.assertEqual(str(r2), "e- + H2 → H + H-")
        self.assertEqual(r1, r2)
        self.assertFalse(created)
        r3, created = Reaction.get_or_create_from_text(
            "e- + H2 -> H + H-", process_type_abbreviations=("EDS", "ENI")
        )
        self.assertEqual(str(r3), "e- + H2 → H + H-")
        self.assertNotEqual(r1, r3)
        self.assertTrue(created)

    def test_molecularity(self):
        reaction = Reaction.create_from_text("5H + 5e- -> H- + H- + 3H-")
        self.assertEqual(reaction.molecularity, 10)
        self.assertEqual(len(RP.objects.all()), 3)
        self.assertEqual(len(State.objects.all()), 0)
        self.assertEqual(len(Species.objects.all()), 3)
        self.assertEqual(len(Reaction.objects.all()), 1)

    def test_process_types(self):
        r = Reaction.create_from_text(
            "H + H -> H + H", process_type_abbreviations=["___"]
        )
        self.assertEqual(list(r.process_types.all()), [self.pt_oth])
        self.assertEqual(list(self.pt_oth.reaction_set.all()), [r])

    def test_comment(self):
        r = Reaction.create_from_text("H + H -> H + H", comment="foo")
        self.assertEqual(r.comment, "foo")

    def test_str(self):
        r = Reaction.create_from_text("2H -> 2H", comment="foo")
        self.assertEqual(str(r), "H + H → H + H")

    def test_repr(self):
        r = Reaction.create_from_text("2H -> H + H", comment="foo")
        self.assertEqual(repr(r), f"<R{r.id}: H + H → H + H>")
