from django.db import models
from django_valem.utils.models import ProvenanceMixin, QualifiedIDMixin
from django_valem.rxn.models import Reaction
from refs.models import Ref


class ReactionDataSet(QualifiedIDMixin, ProvenanceMixin, models.Model):
    qid_prefix = 'D'

    id = models.AutoField(primary_key=True)
    reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE)
    refs = models.ManyToManyField(Ref)
    json_comment = models.TextField(null=True, blank=True)

    json_data = models.TextField(null=True, blank=True)


    class Meta:
        abstract = True


    def __str__(self):
        return str(self.reaction)
