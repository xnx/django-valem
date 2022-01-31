import warnings

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
        text are found, returns an empty query."""
        text_can = repr(PVReaction(text))
        return cls.objects.filter(text=text_can)

    @classmethod
    def create_from_text(cls, text, comment="", process_type_abbreviations=()):
        """Create a reaction instance. Always creates, even if an instance
        with equivalent text already exists. In this case, it raises a
        UserWarning. This is because multiple equivalent reactions might need
        to exist with different comments and process types.
        If some of the species from the reaction text do not exist, they
        will be created to create the reaction.
        The process types with abbreviations passed must exits already."""
        process_types = [
            ProcessType.objects.get(abbreviation=abbrev)
            for abbrev in process_type_abbreviations
        ]

        # WARNING: this will not stop creating a duplicate
        # (although it will raise a Warning.)
        found_instances = cls.all_from_text(text)
        if len(found_instances):
            msg = (
                f'Creating a new instance of reaction "{text}" '
                f"({comment}, {process_type_abbreviations}), "
                f"while the following reactions are already present"
                f"in the database:\n"
            )
            for r in found_instances:
                r_pt = ", ".join(pt.abbreviation for pt in r.process_types.all())
                msg += f"{str(r)} ({r.comment}, ({r_pt}))\n"
            warnings.warn(msg)

        pyvalem_reaction = PVReaction(text)
        text_can = repr(pyvalem_reaction)
        # re-instantiate to sync html representation with the
        # canonicalised text returned by PVReaction.__repr__:
        pyvalem_reaction = PVReaction(text_can)
        html = pyvalem_reaction.html

        # create the Reaction object:
        reaction = cls.objects.create(text=text_can, html=html, comment=comment)
        for attr, Intermediate in zip(
            ["reactants", "products"], [ReactantList, ProductList]
        ):
            for stoich, stateful_species in getattr(pyvalem_reaction, attr):
                for _ in range(stoich):
                    Intermediate.objects.create(
                        reaction=reaction,
                        rp=RP.get_or_create_from_text(repr(stateful_species)),
                    )
        for process_type in process_types:
            reaction.process_types.add(process_type)

        return reaction

    @property
    def molecularity(self):
        """Return the molecularity of the reaction (number of reactants)."""
        return self.reactants.count()


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
