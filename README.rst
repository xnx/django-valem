****************************
Introduction to Django-Valem
****************************


Django-Valem is a collection of Django apps defining data models for parsing,
validation, manipulation and interpretation of chemical reactions, formulas, and
quantum states.
The ``django-valem`` apps package is based around PyValem_.



Installation:
=============
The ``django-valem`` apps can be installed either from PyPI_ using pip

.. code-block:: bash

    python3 -m pip install django-valem


or from the source by running from the project source directory

.. code-block:: bash

    python3 -m pip install .


Configuration:
==============
The ``django-valem`` apps can be added to any Django project by adding the following
apps into the ``INSTALLED_APPS`` list in the ``settings.py`` of the project:

.. code-block:: python

    INSTALLED_APPS = [
        ...

        "rp",  # App handling species and their states
        "rxn",  # App handling chemical reactions between species (rp.RP instances)
        "ds",  # App handling datasets attached to rxn.Reaction instances
        "refs",  # App handling references for ds.ReactionDataSet subclasses instances
    ]


For Developers:
===============
It goes without saying that any development should be done in a clean virtual
environment.
After cloning or forking the project from its GitHub_ page, ``django-valem`` might be
installed into the virtual environment in editable mode with

.. code-block:: bash

    pip install -e .[dev]

The ``[dev]`` extra installs (apart from the package dependencies) also several
development-related packages, such as ``black``, ``ipython``, or ``django`` itself.
The tests can then be executed by running (from the project root directory)

.. code-block:: bash

    python runtests.py

The project does not have ``requirements.txt`` by design, all the package dependencies
are rather handled by ``setup.py``.
The package needs to be installed to run the tests, which grants the testing process
another layer of usefulness.

The project code is formatted by ``black``.
Always make sure to format your code before submitting a pull request, by running
``black`` on all your python files, or ``black .`` from the project source directory.

If the ``rp.models.py``, or ``rxn.models.py`` are changed, the ``makemigrations.py``
script needs to be run to make migrations for the apps, before the apps are pushed to
master, or published to PyPI.


.. _GitHub: https://github.com/xnx/django-valem
.. _PyPI: https://pypi.org/project/django-valem
.. _PyValem: https://github.com/xnx/pyvalem
