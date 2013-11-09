from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

configengine = create_engine('sqlite:////tmp/config.db', echo=True)

Base = declarative_base(bind=configengine)

class DBTable(Base):
    __tablename__ = 'dbtables'

    id = Column(Integer, primary_key = True)
    name = Column(String(255))
    database_table = Column(String(255))
    references = relationship("DBReference", backref = "to_table")
    is_user = Column(Boolean)

class DBReference(Base):
    __tablename__ = 'dbbackrefs'

    id = Column(Integer, primary_key = True)
    from_table = Column(String(255))
    from_name = Column(String(255))
    to_table_id = Column(Integer, ForeignKey('dbtables.id'))
    fkey_name = Column(String(255))
    fkey_to_attribute = Column(String(255))

class Permissions(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key = True)
    userid = Column(Integer)
    tableid = Column(Integer, ForeignKey('dbtables.id'))
    objectid = Column(Integer)

class Admins(Vase):
    __tablename__ = 'admins'

    userid = Column(Integer, primary_key = True)
