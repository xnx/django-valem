from django.db import models
from pyvalem.reaction import Reaction as PVReaction

from _utils.models import QualifiedIDMixin
from rp.models import RP


class ProcessType(QualifiedIDMixin, models.Model):
    """A model class defining the description of a process.

    The processes described by this app fall into categories which are
    described by this model. Each category has a three-letter abbreviation
    code, description and example.

    :abbreviation: abbreviation for the process
    :description: brief text description of the process
    :example_html: a simple, generic example marked up in HTML

    """

    qid_prefix = "P"

    abbreviation = models.CharField(max_length=3, unique=True)
    description = models.CharField(max_length=200)
    example_html = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.abbreviation}"


class Reaction(QualifiedIDMixin, models.Model):
    qid_prefix = "R"

    id = models.AutoField(primary_key=True)

    reactants = models.ManyToManyField(
        RP, related_name="reactants_related", through="ReactantList"
    )
    products = models.ManyToManyField(
        RP, related_name="products_related", through="ProductList"
    )
    process_types = models.ManyToManyField(ProcessType)

    text = models.CharField(max_length=256, editable=False)
    html = models.CharField(max_length=1024, editable=False)
    comment = models.CharField(max_length=1024, blank=True)

    def __str__(self):
        return self.text

    @classmethod
    def all_from_text(cls, text):
        """Uses pyvalem to get a canonicalised version of the text and filters
        the database objects by that text. If no reactions equivalent to passed
        text are found, returns an empty query.

        Parameters
        ----------
        text : str

        Returns
        -------
        Query
        """
        text_can = repr(PVReaction(text))
        return cls.objects.filter(text=text_can)

    @classmethod
    def get_from_text(cls, text, comment="", process_type_abbreviations=()):
        """Looks for an RP with equivalent canonicalised version of the text AND
        identical comment AND the same process_type_abbreviations.
        So this should be strictly named "get_from_data" but we'll keep it like this
        for consistency reasons.

        Parameters
        ----------
        text : str
        comment : str
        process_type_abbreviations : tuple of str

        Returns
        -------
        Reaction
        """
        text_can = repr(PVReaction(text))
        all_with_text_and_comment = cls.objects.filter(text=text_can, comment=comment)
        for reaction in all_with_text_and_comment:
            if sorted(pt.abbreviation for pt in reaction.process_types.all()) == sorted(
                process_type_abbreviations
            ):
                return reaction
        raise cls.DoesNotExist

    @classmethod
    def get_or_create_from_text(cls, text, comment="", process_type_abbreviations=()):
        """

        Parameters
        ----------
        text : str
        comment : str
        process_type_abbreviations : tuple of str

        Returns
        -------
        (Reaction, bool)
        """
        try:
            return cls.get_from_text(text, comment, process_type_abbreviations), False
        except cls.DoesNotExist:
            # canonicalised text and html:
            text_can = repr(PVReaction(text))
            pyvalem_reaction = PVReaction(text_can)  # to reset the html to canonic.
            html = pyvalem_reaction.html
            # create the Reaction object:
            reaction = cls.objects.create(text=text_can, html=html, comment=comment)
            # populate the reactants and products with RP instances:
            for attr, Intermediate in zip(
                ["reactants", "products"], [ReactantList, ProductList]
            ):
                for stoich, stateful_species in getattr(pyvalem_reaction, attr):
                    for _ in range(stoich):
                        Intermediate.objects.create(
                            reaction=reaction,
                            rp=RP.get_or_create_from_text(repr(stateful_species))[0],
                        )
            # assign the ProcessTypes:
            process_types = [
                ProcessType.objects.get(abbreviation=abbrev)
                for abbrev in process_type_abbreviations
            ]
            for process_type in process_types:
                reaction.process_types.add(process_type)

            return reaction, True

    @property
    def molecularity(self):
        """Return the molecularity of the reaction (number of reactants)."""
        return self.reactants.count()

    def _reset_html(self):
        pyvalem_reaction = PVReaction(self.text)
        self.html = pyvalem_reaction.html
        self.save()


class ReactantList(models.Model):
    """ReactantList implements the ManyToMany relationship between an reaction
    and its reactant RP objects."""

    reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE)
    rp = models.ForeignKey(RP, on_delete=models.CASCADE)

    class Meta:
        db_table = "rxn_reaction_reactants"


class ProductList(models.Model):
    """ProductList implements the ManyToMany relationship between an reaction
    and its product RP objects."""

    reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE)
    rp = models.ForeignKey(RP, on_delete=models.CASCADE)

    class Meta:
        db_table = "rxn_reaction_products"
