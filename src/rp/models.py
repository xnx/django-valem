import re
from django.db import models
from pyvalem.formula import Formula
from pyvalem.stateful_species import StatefulSpecies

from _utils.models import QualifiedIDMixin


class Species(QualifiedIDMixin, models.Model):
    qid_prefix = "F"

    id = models.AutoField(primary_key=True)

    text = models.CharField(max_length=80)
    html = models.CharField(max_length=200)
    charge = models.SmallIntegerField(default=0, null=True)

    class Meta:
        verbose_name_plural = "Species"

    def __str__(self):
        return self.text

    @classmethod
    def get_from_text(cls, text):
        """Looks for a Species with equivalent canonicalised version of the
        text. Uses pyvalem Formula.__repr__ for the canonicalisation.
        If not present, Species.DoesNotExist is raised.

        Parameters
        ----------
        text : str

        Returns
        -------
        Species
        """
        text_can = repr(Formula(text))
        return cls.objects.get(text=text_can)

    @classmethod
    def get_or_create_from_text(cls, text):
        """Looks for a Species with equivalent canonicalised version of the
        text.

        Parameters
        ----------
        text : str

        Returns
        -------
        (Species, bool)
        """
        pyvalem_formula = Formula(text)
        text_can = repr(pyvalem_formula)
        try:
            return cls.objects.get(text=text_can), False
        except cls.DoesNotExist:
            # re-instantiate the pyvalem_formula with canonicalised
            # text to canonicalise html also:
            pyvalem_formula = Formula(text_can)
            species = cls.objects.create(
                text=text_can, charge=pyvalem_formula.charge, html=pyvalem_formula.html
            )
            return species, True


class SpeciesAlias(models.Model):
    text = models.CharField(max_length=80, unique=True)
    species = models.ForeignKey(Species, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.text} -> {self.species.text}"


class RP(QualifiedIDMixin, models.Model):
    qid_prefix = "RP"

    id = models.AutoField(primary_key=True)
    species = models.ForeignKey(Species, on_delete=models.CASCADE)

    text = models.CharField(max_length=200)
    html = models.CharField(max_length=600)

    def __str__(self):
        return self.text

    @classmethod
    def get_from_text(cls, text):
        """Looks for RP with equivalent canonicalised version of the
        text. Uses pyvalem StatefulSpecies.__repr__ for the canonicalisation.
        If not present, RP.DoesNotExist is raised.

        Parameters
        ----------
        text : str

        Returns
        -------
        RP
        """
        text_can = repr(StatefulSpecies(text))
        # TODO Look up Species formula in SpeciesAlias table.
        return cls.objects.get(text=text_can)

    @classmethod
    def filter_from_text(cls, text, inchi_lookup=False):
        """Filters for RP using canonicalised version of the StatefulSpecies
        represented by text, having first resolved the Species formula into
        its canonical form for this database by looking it up in the
        SpeciesAlias table.

        Parameters
        ----------
        text : str

        Returns
        -------
        django.db.models.query.QuerySet
        """

        patt = "[A-Z]{14}-[A-Z]{10}-N"
        if text.startswith("InChI=") or text.startswith("1S/") or re.match(patt, text):
            chunks = text.split()
            species_text, states = chunks[0], chunks[1:]
            try:
                species = SpeciesAlias.objects.get(text=species_text).species
            except SpeciesAlias.DoesNotExist:
                return cls.objects.none()
            # Replace the InChI / InChIKey with the canonical text representation
            text = " ".join([species.text] + states)

        ss = StatefulSpecies(text)

        try:
            species = SpeciesAlias.objects.get(text=ss.formula).species
            rps = cls.objects.filter(species__text=species.text)
        except SpeciesAlias.DoesNotExist:
            rps = cls.objects.filter(species__text=ss.formula)

        for state in ss.states:
            rps = rps.filter(state__text=state)

        return rps

    @classmethod
    def get_or_create_from_text(cls, text):
        """Looks for a Species with equivalent canonicalised version of the
        text.

        Parameters
        ----------
        text : str

        Returns
        -------
        (RP, bool)
        """
        pyvalem_stateful_species = StatefulSpecies(text)
        text_can = repr(pyvalem_stateful_species)
        try:
            return cls.objects.get(text=text_can), False
        except cls.DoesNotExist:
            pyvalem_formula = pyvalem_stateful_species.formula
            species, _ = Species.get_or_create_from_text(repr(pyvalem_formula))
            # re-instantiate the pyvalem_stateful_species with canonicalised
            # text to canonicalise html also and sort the states consistently
            # with the text and html:
            pyvalem_stateful_species = StatefulSpecies(text_can)
            # build the RP instance:
            rp = cls.objects.create(
                species=species, text=text_can, html=pyvalem_stateful_species.html
            )
            # attach the states:
            for pyvalem_state in pyvalem_stateful_species.states:
                State.objects.create(
                    rp=rp,
                    text=repr(pyvalem_state),
                    html=pyvalem_state.html,
                    state_type=State.STATE_TYPE_MAP[pyvalem_state.__class__.__name__],
                )
            return rp, True

    @property
    def charge(self):
        """Returns the charge of RPs Species."""
        return self.species.charge


class State(QualifiedIDMixin, models.Model):
    qid_prefix = "S"

    KEY_VALUE_PAIR = 0
    GENERIC_EXCITED_STATE = 1
    ATOMIC_CONFIGURATION = 2
    ATOMIC_TERM_SYMBOL = 3
    DIATOMIC_MOLECULAR_CONFIGURATION = 4
    MOLECULAR_TERM_SYMBOL = 5
    VIBRATIONAL_STATE = 6
    ROTATIONAL_STATE = 10
    RACAH_SYMBOL = 11

    STATE_TYPE_CHOICES = (
        (KEY_VALUE_PAIR, "KeyValuePair"),
        (GENERIC_EXCITED_STATE, "GenericExcitedState"),
        (ATOMIC_CONFIGURATION, "AtomicConfiguration"),
        (ATOMIC_TERM_SYMBOL, "AtomicTermSymbol"),
        (DIATOMIC_MOLECULAR_CONFIGURATION, "DiatomicMolecularConfiguration"),
        (MOLECULAR_TERM_SYMBOL, "MolecularTermSymbol"),
        (VIBRATIONAL_STATE, "VibrationalState"),
        (ROTATIONAL_STATE, "RotationalState"),
        (RACAH_SYMBOL, "RacahSymbol"),
    )

    STATE_TYPE_MAP = {v: k for k, v in STATE_TYPE_CHOICES}

    id = models.AutoField(primary_key=True)
    rp = models.ForeignKey(RP, on_delete=models.CASCADE)

    state_type = models.SmallIntegerField(choices=STATE_TYPE_CHOICES)
    text = models.CharField(max_length=64)
    html = models.CharField(max_length=100)

    def __str__(self):
        return self.text
