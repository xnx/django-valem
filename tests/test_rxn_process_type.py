from django.test import TestCase

from rxn.models import ProcessType


class TestProcessType(TestCase):
    def test_str(self):
        process_type = ProcessType.objects.create(
            abbreviation="HDS",
            description="Dissociation",
            example_html="A + BC → A + B + C",
        )
        self.assertEqual(str(process_type), "HDS")

    def test_repr(self):
        process_type = ProcessType.objects.create(
            id=42,
            abbreviation="HDS",
            description="Dissociation",
            example_html="A + BC → A + B + C",
        )
        self.assertEqual(repr(process_type), "<P42: HDS>")
