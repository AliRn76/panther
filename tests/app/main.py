import sys
from panther import Panther

URLs = 'urls.url_routing'

app = Panther(__name__, configs=sys.modules[__name__])
