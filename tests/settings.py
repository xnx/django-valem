SECRET_KEY = "dummy-secret-key"
DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}
INSTALLED_APPS = ["tests", "rp", "rxn", "ds", "refs"]
