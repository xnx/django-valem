import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner
from coverage import Coverage

if __name__ == "__main__":
    cov = Coverage()
    cov.erase()
    cov.start()

    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)

    failures = test_runner.run_tests(["tests"])

    cov.stop()
    cov.save()
    covered = cov.report()
    cov.html_report()

    sys.exit(bool(failures))
