Configuration
=============

The application is configured through an env file. Its location is, by default, ``.env`` in the
working directory. If no such file exists, the parent folders of the working directory are searched.
The env file location can be changed by setting the environment variable ``ENV_FILE``, like so:

.. code-block:: bash

    ENV_FILE=.env.example python3 -m src [command] [subcommand]

The project contains the sample env file ``.env.example`` with valid settings for all configuration
settings.

General settings
~~~~~~~~~~~~~~~~

CROSSREF_DEPOSITION_URL
-----------------------

The URL of the Crossref XML deposition system.

Should be either https://doi.crossref.org/servlet/deposit for the production system or
https://test.crossref.org/servlet/deposit for the test sandbox, but check `Crossref's documentation`_
to make sure.

Required when creating DOIs with Crossref. Can be left empty otherwise.

.. _Crossref's documentation: https://www.crossref.org/documentation/register-maintain-records/direct-deposit-xml/https-post/

CROSSREF_USERNAME
-----------------

The username of your Crossref account credentials.

Required when creating DOIs with Crossref. Can be left empty otherwise.

CROSSREF_PASSWORD
-----------------

The password of your Crossref account credentials.

Required when creating DOIs with Crossref. Can be left empty otherwise.

DB_URL
------

The URL to access the MECADOI database.

It must be in a form understood by SQLAlchemy's ``create_engine``. Quoting from its documentation:

"The string form of the URL is dialect[+driver]://user:password@host/dbname[?key=value..], where
dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name of a DBAPI,
such as psycopg2, pyodbc, cx_oracle, etc."

LOG_FILE
--------

Where to write the log to. Must be a file path.

Not required. The application logs to stdout if empty.

LOG_LEVEL
---------

The log level to use.

Not required. Defaults to ``INFO``.

Deposition metadata
~~~~~~~~~~~~~~~~~~~

These settings are used for generating the metadata sent to Crossref to create DOIs.
They are are required when creating deposition files and can be left empty otherwise.

All values are going into fields of the `Crossref metadata schema`_ for DOI deposition.
Each description below has an `XPath`_ location path to the field that the setting value will be
inserted into.

Some of these settings are templates (those with the suffix ``_TEMPLATE``). They will be used to
build the value to go into their field by substituting $-prefixed placeholders with actual values.
As an example, a template like ``This is a $placeholder`` will produce a value of ``This is a test``
if the placeholder is replaced by the word "test". For more details on the syntax, see the documentation
for `Python template strings`_.

.. _Crossref metadata schema: https://data.crossref.org/reports/help/schema_doc/5.3.1/index.html
.. _XPath: https://en.wikipedia.org/wiki/XPath
.. _Python template strings: https://docs.python.org/3/library/string.html#template-strings

DEPOSITOR_NAME
--------------

Name of the organization registering the DOIs.

`doi_batch/head/depositor/depositor_name`_

DEPOSITOR_EMAIL
---------------

Email address to which batch success and/or error messages are sent.

`doi_batch/head/depositor/email_address`_

REGISTRANT_NAME
---------------

The organization responsible for the information being registered.

`doi_batch/head/registrant`_

INSTITUTION_NAME
----------------

The full name of institution or organization associated with a peer review or author reply.

`doi_batch/body/peer_review/institution/institution_name`_

REVIEW_RESOURCE_URL_TEMPLATE
----------------------------

The URI associated with a peer review's DOI will be constructed from this template.

For each review in a MECA archive, this template will be used to construct the URI under which the
review is published.
The template must contain these parameters:

- ``$article_id``: the DOI of the article under review.
- ``$revision``: the revision identifier that this review belongs to.
- ``$running_number``: the running number of this review.

`doi_batch/body/peer_review/doi_data/resource`_

REVIEW_TITLE_TEMPLATE
---------------------

The title of the review being registered will be constructed from this template.

For each review in a MECA archive, this template will be used to construct the title of the review.
The template must contain these parameters:

- ``$article_title``: the title of the article under review.
- ``$review_number``: the running number of this review.

`doi_batch/body/peer_review/titles/title`_

AUTHOR_REPLY_RESOURCE_URL_TEMPLATE
----------------------------------

The URI associated with an author reply's DOI will be constructed from this template.

For each author reply in a MECA archive, this template will be used to construct the URI under
which the author reply is published.
The template must contain these parameters:

- ``$article_id``: the DOI of the article under review.
- ``$revision``: the revision identifier that this author reply belongs to.

`doi_batch/body/peer_review/doi_data/resource`_

AUTHOR_REPLY_TITLE_TEMPLATE
---------------------------

The title of the author reply being registered will be constructed from this template.

For each author reply in a MECA archive, this template will be used to construct title of the
author reply.
The template must contain these parameters:

- ``$article_title``: the title of the article under review.

`doi_batch/body/peer_review/titles/title`_

DOI_TEMPLATE
------------

The DOI under which reviews and author replies are published will be constructed from this template.

For each review and author reply in a MECA archive, this template will be used to construct the DOI
under which they are published.
The template must contain these parameters:

- ``$year``: the current year, e.g. ``2022``.
- ``$random``: a random strinc of numbers.

`doi_batch/body/peer_review/doi_data/doi`_

.. _doi_batch/head/depositor/depositor_name: https://data.crossref.org/reports/help/schema_doc/5.3.1/common5_3_1_xsd.html#depositor_name
.. _doi_batch/head/depositor/email_address: https://data.crossref.org/reports/help/schema_doc/5.3.1/common5_3_1_xsd.html#email_address
.. _doi_batch/head/registrant: https://data.crossref.org/reports/help/schema_doc/5.3.1/common5_3_1_xsd.html#registrant
.. _doi_batch/body/peer_review/institution/institution_name: https://data.crossref.org/reports/help/schema_doc/5.3.1/common5_3_1_xsd.html#institution_name
.. _doi_batch/body/peer_review/doi_data/resource: https://data.crossref.org/reports/help/schema_doc/5.3.1/common5_3_1_xsd.html#resource
.. _doi_batch/body/peer_review/titles/title: https://data.crossref.org/reports/help/schema_doc/5.3.1/common5_3_1_xsd.html#title
.. _doi_batch/body/peer_review/doi_data/doi: https://data.crossref.org/reports/help/schema_doc/5.3.1/common5_3_1_xsd.html#doi