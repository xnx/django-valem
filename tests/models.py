from django.db import models

from ds.models import ReactionDataSet


class MyReactionDataSet(ReactionDataSet):
    json_data = models.TextField(null=True, blank=True)
    json_comment = models.TextField(null=True, blank=True)
