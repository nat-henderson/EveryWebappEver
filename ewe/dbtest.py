from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)
    def __init__(self, name, fullname, password):
        self.name = name
        self.fullname = fullname
        self.password = password

engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

Base.metadata.create_all(engine) 
ed_user = User('ed', 'Ed Jones', 'edspassword')
session.add(ed_user)

#print jsonify_sql_obj(ed_user)
