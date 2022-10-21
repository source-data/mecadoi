MECADOI
=======

MECADOI is a Python library and command-line interface to create DOIs for peer reviews and author replies contained in a MECA archive.
MECA is a `standardized format`_ for the transferral of a manuscript, its metadata, and optionally peer review data between publishers.

The command-line interface (CLI) provides an easy way to read MECA archives, extract their contents and metadata, store the required data in a local database, and create a DOI for each peer review and, when available, authors' reply, using the `CrossRef deposition API`_.

The Python library enables more fine-grained control over the workflow executed by the CLI.

The project also contains the setup for a simple workflow pipeline to automatically ingest MECA archives from a file server, create DOIs for any peer reviews and authors' replies within them, archive the results to an AWS S3 bucket, and export a summary of all created DOIs.

MECADOI was built by `EMBO Press`_ for use by the `Review Commons`_ platform.

.. _standardized format: https://www.niso.org/publications/rp-30-2020-meca
.. _CrossRef deposition API: https://www.crossref.org/documentation/member-setup/direct-deposit-xml/
.. _EMBO Press: https://www.embopress.org/
.. _Review Commons: https://www.reviewcommons.org/

Links
-----

- Documentation: https://source-data.github.io/mecadoi/
- Source code: https://github.com/source-data/mecadoi/
