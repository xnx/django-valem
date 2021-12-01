import os
from setuptools import setup, find_packages

long_description = """
django-valem is a Python package for managing chemical reactions, collisional
processes, etc.

See https://github.com/xnx/django-valem for more information.
"""

# Read in dependencies list from requirements.txt
thelibFolder = os.path.dirname(os.path.realpath(__file__))
requirementPath = thelibFolder + '/requirements.txt'
install_requires = []
if os.path.isfile(requirementPath):
    with open(requirementPath) as f:
        install_requires = f.read().splitlines()

setup(
    name = 'django-valem',
    version = '0.0.1',
    author = 'Christian Hill, Martin Hanicinec, Dipti',
    author_email = 'xn.hill@gmail.com',
    description = 'A package for managing chemical reactions and species',
    long_description=long_description,
    long_description_content_type="text/markdown",
    #include_package_data=True,
    url = 'https://github.com/xnx/django-valem',
    packages = find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires='>=3.6',
)
