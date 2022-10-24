Development
===========

Run ``pip install -r requirements/dev.txt`` to install all development dependencies.

Continuous Integration is run with a Github Actions workflow that is defined in ``.github/workflows/unit-tests.yml``.
This workflow lints and tests the application.

Linting
-------

Checking the code style, formatting, and types is performed with `flake8`_, `black`_, and `mypy`_, respectively.

``scripts/lint.sh`` runs the three tools in succession.
Run ``black ./mecadoi ./tests`` to auto-format all code. 

Configuration for flake8 and mypy is in the ``.flake8`` and ``mypy.ini`` files.

.. _flake8: https://flake8.pycqa.org/
.. _black: https://black.readthedocs.io/
.. _mypy: https://mypy.readthedocs.io/

Testing
-------

Tests are located in the ``tests`` folder, test data (including the contents of some sample MECA archives) in ``tests/resources``.

To run all tests:

.. code-block:: bash

    python3 -m unittest

Documentation
-------------

Documentation source files are located in the ``docs`` folder.
The documentation is built with `sphinx`_.

First, install all dependencies to build the documentation:

.. code-block:: bash

    pip install -r requirements/docs.txt

``docs`` contains a Makefile to build or clean the documentation:

.. code-block:: bash

    cd docs
    make clean
    make html

The HTML build output is located in ``docs/_build/html``.

.. _sphinx: https://www.sphinx-doc.org/

Crossref sandbox
----------------

If you want to test the full workflow of the application including DOI creation and you have a membership, CrossRef provides a `sandbox environment`_.
This environment requires a different set of credentials than the usual account credentials.

The sandbox also does not seem to be kept in sync with the production environment, there seems to be no way to query its contents, and when creating DOIs for reviews and replies these must be linked to an existing DOI.

Therefore, before being able to create DOIs for peer reviews, you need create a DOI for an article.
Then, use that DOI as the preprint DOI in the test MECA and run the MECADOI workflow.
Only then will creating DOIs for all reviews and replies in the test MECA work.

.. _sandbox environment: https://test.crossref.org/