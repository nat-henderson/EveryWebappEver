from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

configengine = create_engine('sqlite:////tmp/config.db', echo=True)

Base = declarative_base(bind=configengine)

class DBTable(Base):
    name = Column(String(255))
    database_table = Column(String(255))
