from django.db import models


# noinspection PyUnresolvedReferences
class QualifiedIDMixin:
    qid_prefix = "-"

    @property
    def qualified_id(self):
        return f"{self.qid_prefix}{self.id}"

    def __repr__(self):
        """By default, prepend the qualified ID to the class' __repr__()"""
        return f"<{self.qualified_id}: {self}>"


class ProvenanceMixin:
    added_by_user_id = models.IntegerField(null=True, blank=True)
    time_added = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)
