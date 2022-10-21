Project Background
==================

Reviews produced during the scholarly peer review process at Review Commons are published to the web (currently to the `hypothes.is`_ platform).
As they represent scholarly work, Review Commons wants them to receive a DOI like other such works.
This is currently not supported by the publishing platform used by Review Commons.
Upon completion of the peer review process, however, this publishing platform allows exporting the data associated with a peer-reviewed article to a configurable FTP server in the MECA format.

.. _hypothes.is: https://web.hypothes.is/

The MECA format
---------------

The `Manuscript Exchange Common Approach`_ format is a standard for transferral of manuscripts and related information between publishers.
A single MECA archive is .zip-compressed file with metadata and review data in XML files and manuscripts, revisions, etc. in .docx or .pdf files.

Specifically, each MECA must contain a file named ``manifest.xml`` that lists every file in the archive.
It also must have a file, commonly called ``article.xml``, with metadata about the manuscript or article packaged in the MECA.
Finally, MECAs can contain information about the review process of the packaged article in an optional file usually called ``reviews.xml``.

.. _Manuscript Exchange Common Approach: https://www.niso.org/standards-committees/meca

The DOI system
--------------

The digital object identifier [DOI®] system provides an infrastructure for persistent unique identification of objects of any type.
DOI is an acronym for "digital object identifier", meaning a "digital identifier of an object" rather than an "identifier of a digital object".
The DOI system is designed to work over the Internet.
A DOI name is permanently assigned to an object to provide a resolvable persistent network link to current information about that object, including where the object, or information about it, can be found on the Internet.
While information about an object can change over time, its DOI name will not change.

For example, the DOI name "10.1000/182" is assigned to the latest version of the DOI handbook, from which the preceding paragraph is taken.
It can be accessed like so: https://doi.org/10.1000/182
DOIs are created through registration agencies such as `Crossref`_.

.. _Crossref: https://www.crossref.org/
