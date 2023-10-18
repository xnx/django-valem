from django.test import TestCase
from django.db.utils import IntegrityError
from rp.models import Species, SpeciesAlias, RP


# noinspection PyTypeChecker
class TestSpeciesAlias(TestCase):
    def setUp(self):
        self.HD = Species.objects.create(text="HD")
        self.HD_aliases = ["DH", "H(2H)", "(2H)H", "(1H)(2H)", "(2H)(1H)"]
        for HD_alias in self.HD_aliases:
            SpeciesAlias.objects.create(species=self.HD, text=HD_alias)
        self.Xep34 = Species.objects.create(text="Xe+34")
        self.Xep34_inchi = SpeciesAlias.objects.create(
            species=self.Xep34, text="InChI=1S/Xe/q+34"
        )
        self.Xep34_inchi2 = SpeciesAlias.objects.create(
            species=self.Xep34, text="1S/Xe/q+34"
        )
        self.Xep34_inchikey = SpeciesAlias.objects.create(
            species=self.Xep34, text="CBYSBAHMMKPXKC-UHFFFAOYSA-N"
        )

    def test_HD_aliases(self):
        for HD_alias in self.HD_aliases:
            species = SpeciesAlias.objects.get(text=HD_alias).species
            self.assertEqual(species, self.HD)

            with self.assertRaises(SpeciesAlias.DoesNotExist):
                SpeciesAlias.objects.get(text="xx")

    def test_create_nonunique_alias(self):
        species = Species.objects.create(text="H(35Cl)")
        SpeciesAlias.objects.create(species=species, text="(1H)(35Cl)")
        with self.assertRaises(IntegrityError):
            SpeciesAlias.objects.create(species=species, text="(1H)(35Cl)")

    def test_filter_RP_from_text(self):
        rp1, _ = RP.get_or_create_from_text(text="HD v=0 X(1SIGMA+g)")
        rp2, _ = RP.get_or_create_from_text(text="HD v=1 X(1SIGMA+g)")

        for text in "HD", "HD X(1SIGMA+g)":
            rps = RP.filter_from_text(text)
            self.assertEqual(rps.count(), 2)
            self.assertEqual(rps[0], rp1)
            self.assertEqual(rps[1], rp2)

        rps = RP.filter_from_text("H(2H) v=0")
        self.assertEqual(rps.count(), 1)
        self.assertEqual(rps[0], rp1)

        rps = RP.filter_from_text("DH X(1SIGMA+g)")
        self.assertEqual(rps.count(), 2)
        self.assertEqual(rps[0], rp1)
        self.assertEqual(rps[1], rp2)

        rps = RP.filter_from_text("LiH")
        self.assertFalse(rps.exists())

    def test_inchi_aliases(self):
        rp1, _ = RP.get_or_create_from_text(text="Xe+34 1s2.2p3 3P_1")
        for inchi_alias in (
            self.Xep34,
            self.Xep34_inchi,
            self.Xep34_inchi2,
            self.Xep34_inchikey,
        ):
            rps = RP.filter_from_text(inchi_alias.text, inchi_lookup=True)
            self.assertEqual(rps.count(), 1)
            self.assertEqual(rps[0], rp1)

            rps = RP.filter_from_text(inchi_alias.text + " 3P_1", inchi_lookup=True)
            self.assertEqual(rps.count(), 1)
            self.assertEqual(rps[0], rp1)

        # A non-existent InChI
        rps = RP.filter_from_text("InChI=1S/He/q+3", inchi_lookup=True)
        self.assertEqual(rps.count(), 0)
