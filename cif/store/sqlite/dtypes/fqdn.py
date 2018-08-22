from . import IOCType
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class Fqdn(IOCType):

    def get_col_spec(self, **kw):
        return "FQDN"
