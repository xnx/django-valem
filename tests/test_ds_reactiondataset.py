from django.test import TestCase
from refs.models import Ref

from rxn.models import Reaction, ProcessType
from .models import MyReactionDataSet


class TestReactionDataSet(TestCase):
    def setUp(self):
        process_types_raw = [
            ["EEX", "Excitation", "e<sup>-</sup> + A → e<sup>-</sup> + A<sup>*</sup>"],
            [
                "EXV",
                "Vibrational Excitation",
                "e<sup>-</sup> + AB → e<sup>-</sup> + AB (<i>v</i>=*)",
            ],
        ]
        self.all_process_types = {}
        for abbreviation, description, example_html in process_types_raw:
            pt = ProcessType.objects.create(
                abbreviation=abbreviation,
                description=description,
                example_html=example_html,
            )
            self.all_process_types[abbreviation] = pt

        self.test_reaction, _ = Reaction.get_or_create_from_text(
            "BeH+ v=0 + e- -> BeH+ v=10 + e-", process_type_abbreviations=("EEX", "EXV")
        )

        self.doi = "10.1016/j.adt.2016.09.002"
        Ref.objects.create(
            authors="S. Niyonzima et.al.",
            title="Low-energy collisions between electrons and BeH+",
            journal="Atomic Data and Nuclear Data Tables",
            volume="115-116",
            page_start="287",
            page_end="308",
            year=2017,
            doi=self.doi,
        )

    def test_add_dataset(self):
        json_data = '{"T_max": {"value": 5000, "units": "K"}}'
        json_comment = '{"comment": "comment"}'
        dataset = MyReactionDataSet.objects.create(
            reaction=self.test_reaction, json_comment=json_comment, json_data=json_data
        )
        ref = Ref.objects.get(doi=self.doi)
        dataset.refs.add(ref)

    def test_str(self):
        ds = MyReactionDataSet.objects.create(reaction=self.test_reaction)
        self.assertEqual(str(ds), str(self.test_reaction))

    def test_repr(self):
        ds = MyReactionDataSet.objects.create(id=42, reaction=self.test_reaction)
        self.assertEqual(repr(ds), f"<D42: {str(self.test_reaction)}>")
