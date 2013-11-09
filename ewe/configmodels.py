from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

engine = create_engine('sqlite:////tmp/config.db', echo=True)

Base = declarative_base(bind=engine)

class DBTable(Base):
    pass
