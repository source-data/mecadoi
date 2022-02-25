# The classes in this package are generated with xsdata from a sample MECA archive: https://pypi.org/project/xsdata/
# The command used to generate the classes is `xsdata MECA.zip --package src.meca.xml`. A few classes then will have to
# be moved to a common file to break circular dependencies between article.py and review_group.py.

from .article import Article
from .manifest import Manifest
from .review_group import ReviewGroup
from .transfer import Transfer
