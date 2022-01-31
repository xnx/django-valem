from django.db import models
from refs.models import Ref

from _utils.models import ProvenanceMixin, QualifiedIDMixin
from rxn.models import Reaction


class ReactionDataSet(QualifiedIDMixin, ProvenanceMixin, models.Model):
    """An Abstract Base Class representing a dataset.

    Links a `Reaction` instance and one or more `Ref` reference instances.
    The subclasses are responsible for implementing any data fields relevant to their
    scope.
    """

    qid_prefix = "D"

    id = models.AutoField(primary_key=True)
    reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE)
    refs = models.ManyToManyField(Ref)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.reaction)
