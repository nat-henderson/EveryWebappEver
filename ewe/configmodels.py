from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

configengine = create_engine('sqlite:////tmp/config.db', echo=True)

Base = declarative_base(bind=configengine)

class DBTable(Base):
    __tablename__ = 'dbtables'

    id = Column(Integer, primary_key = True)
    name = Column(String(255))
    database_table = Column(String(255))
    references = relationship("DBReference", backref = "from_table")

class DBReference(Base):
    __tablename__ = 'dbbackrefs'

    id = Column(Integer, primary_key = True)
    to_table = Column(String(255))
    to_field = Column(String(255))
    from_field = Column(String(255))
    from_table_id = Column(Integer, ForeignKey('dbtables.id'))
