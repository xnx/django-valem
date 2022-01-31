import django
from django.conf import settings
from django.core.management import call_command

if __name__ == "__main__":
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=("rp", "rxn"),
    )

    django.setup()
    call_command("makemigrations", "rp")
    call_command("makemigrations", "rxn")
    # I cannot make migrations for ReactionDataSet, as it is an abstract Model and one
    # cannot inherit from a model with migrations!
