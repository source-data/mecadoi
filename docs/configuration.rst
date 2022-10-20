Configuration
=============

The application is configured through an env file.
It's location is ``.env`` by default but can be set through the ``ENV_FILE`` environment variable like so:

.. code-block:: bash

    ENV_FILE=.env.ci python3 -m src.cli.main [command] [subcommand]

.. The configuration for a specific peer review platform is defined in `config.py`. See details in `documentation/doc.md`.