from . import IOCType
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Url(IOCType):

    def get_col_spec(self, **kw):
        return 'URL'
