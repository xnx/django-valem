from django.db import transaction
from django.test import TestCase
from pyvalem.formula import Formula

from rp.models import Species


class TestSpecies(TestCase):
    default_kwargs = {"text": "H", "charge": 0, "html": "H"}
    formula_text_choices = "H2", "T3", "(CH2)C(CH2)+42"

    def test_instantiation_succeeds(self):
        Species(text="foo", charge=0, html="")
        Species(text="", html=r"<tag>foo</tag>")
        Species(text=42, charge="abc", html=(42, 42.0, "42"))
        # actually instantiation succeeds with any arguments,
        # even without arguments? Errors are raised during saving.
        Species()

    def test_instantiation_defaults(self):
        sp = Species(text="H", html="H")
        self.assertEqual(sp.charge, 0)

    def test_instantiation_does_not_create(self):
        Species(**self.default_kwargs)
        self.assertEqual(len(Species.objects.all()), 0)

    def test_django_save_duplicates(self):
        # simply creating the instances through Django API can make duplicates.
        Species(**self.default_kwargs).save()
        self.assertEqual(len(Species.objects.all()), 1)
        Species(**self.default_kwargs).save()
        self.assertEqual(len(Species.objects.all()), 2)
        Species.objects.create(**self.default_kwargs)
        self.assertEqual(len(Species.objects.all()), 3)

    def test_integrity_failures(self):
        for args in [
            (None, 0, "H"),
            ("H", 0, None),
            ("H", "foo", "H"),
            ("H", "42.0", "H"),
        ]:
            kwargs = dict(zip(("text", "charge", "html"), args))
            sp = Species(**kwargs)
            with self.subTest(**kwargs):
                with self.assertRaises(Exception):
                    # exception depends on the database backend!
                    with transaction.atomic():
                        sp.save()
        self.assertEqual(len(Species.objects.all()), 0)

    def test_integrity_typecasting(self):
        for arg, passed, saved in [
            ("text", 42, "42"),
            ("text", int, "<class 'int'>"),
            ("charge", "-42", -42),
            ("charge", " 42 ", 42),
        ]:
            sp = Species(**dict(self.default_kwargs, **{arg: passed}))
            sp.save()
            with self.subTest(arg=arg, passed=passed, saved=saved):
                # the types are not converted upon saving but they are,
                # when the instance is fetched from the database...
                self.assertEqual(getattr(sp, arg), passed)
                self.assertEqual(getattr(Species.objects.get(pk=sp.pk), arg), saved)

    def test_str(self):
        sp = Species(pk=1, **self.default_kwargs)
        self.assertEqual(str(sp), self.default_kwargs["text"])

    def test_repr(self):
        sp = Species(pk=1, **self.default_kwargs)
        self.assertEqual(repr(sp), f"<F{sp.pk}: {str(sp)}>")

    def test_get_from_text_not_found(self):
        for text in self.formula_text_choices:
            with self.subTest(formula_text=text):
                # noinspection PyTypeChecker
                with self.assertRaises(Species.DoesNotExist):
                    Species.get_from_text(text)

    def test_get_from_text_found(self):
        kwargs = {"text": "H2O", "charge": 42, "html": ""}
        Species(**kwargs).save()
        species = Species.get_from_text(kwargs["text"])
        for attr, val in kwargs.items():
            self.assertEqual(getattr(species, attr), val)

    def test_get_or_create_from_text(self):
        for text in self.formula_text_choices:
            initial_num_species = len(Species.objects.all())
            # noinspection PyTypeChecker
            with self.assertRaises(Species.DoesNotExist):
                # species does not exist yet
                Species.get_from_text(text)

            with self.subTest(formula_text=text):
                # create the species
                species, created = Species.get_or_create_from_text(text)
                self.assertTrue(created)
                formula = Formula(text)
                # how does the species look?
                self.assertEqual(species.text, text)
                self.assertEqual(species.charge, formula.charge)
                self.assertEqual(species.html, formula.html)
                # was the species created?
                self.assertEqual(len(Species.objects.all()), initial_num_species + 1)
                self.assertEqual(species, Species.get_from_text(text))
                # will the species not be created again?
                species1, created = Species.get_or_create_from_text(text)
                self.assertFalse(created)
                self.assertEqual(len(Species.objects.all()), initial_num_species + 1)
                self.assertEqual(species1, species)
