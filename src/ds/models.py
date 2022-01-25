from django.db import models
from refs.models import Ref

from _utils.models import ProvenanceMixin, QualifiedIDMixin
from rxn.models import Reaction


class ReactionDataSet(QualifiedIDMixin, ProvenanceMixin, models.Model):
    qid_prefix = "D"

    id = models.AutoField(primary_key=True)
    reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE)
    refs = models.ManyToManyField(Ref)
    comment = models.TextField(null=True, blank=True)

    json_data = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.reaction)
