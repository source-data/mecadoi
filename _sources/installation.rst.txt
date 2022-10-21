Installation
============

Requirements
------------

- ``python3`` >= 3.9
- ``pip``

For creating DOIs with Crossref:

- A Crossref `membership`_ and `account credentials`_.

Everything except creating DOIs also works without a Crossref membership and credentials.

.. _membership: https://www.crossref.org/documentation/member-setup/
.. _account credentials: https://www.crossref.org/documentation/member-setup/account-credentials/

Installing from source
------------------------

Clone this repository, create a virtual env (optional), and install the dependencies:

.. code-block:: bash

    git clone https://github.com/source-data/mecadoi.git && cd mecadoi
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements/base.txt

The application is configured with an ``.env`` file. The repository contains an example:

.. code-block:: bash

    cp .env.example .env

You're now ready to use the CLI, e.g. to get basic info about a MECA archive:

.. code-block:: bash

    python3 -m src meca info demo-meca.zip

Which should output something like this:

.. code-block:: text

    authors: Doe, Jane, Doe, John
    doi: 10.12345/multiple-revision-rounds.1234567890
    journal: Review Commons - TEST
    preprint_doi: 10.1101/multiple-revision-rounds.123.456.7890
    review_process: 2 revision rounds, 4 reviews, 1 author reply
    title: An article with multiple revision rounds.