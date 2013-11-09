import random
import string

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData, Table
from flask import Flask, request

from utilities import *

app = Flask(__name__)

appengine = create_engine('sqlite:////tmp/app.db', echo=True)
Session = sessionmaker(bind=appengine)
session = Session()

names_to_orm_classes = {}

Base = declarative_base(bind=appengine)

class NoSuchTableException(ValueError): pass

def get_or_create_orm_object(name, appengine = None, Base = None):
    if name not in names_to_orm_classes:
        meta = MetaData()
        meta.reflect(bind=appengine)
        if name not in meta.tables:
            raise NoSuchTableException("no %s in %s" % (name, meta.tables.keys()))
        table = meta.tables[name]
        def random_id():
            return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
        new_table_id = table.name + random_id()
        code_to_generate_this_table = """
class %s(Base):
    __table__ = Table(%r, Base.metadata, autoload=True)

""" % (new_table_id, table.name)
        all_vars = globals().update(locals())
        exec(code_to_generate_this_table) in all_vars
        names_to_orm_classes[name] = locals()[new_table_id]
    return names_to_orm_classes[name]

@app.route('/<tablename>/<int:id>', methods=['GET'])
def get_obj_from_table(tablename, id):
    table = get_or_create_orm_object(tablename, appengine, Base)
    obj = session.query(table).filter_by(id=id).first()
    if not obj:
        return "User does not exist.",400
    return jsonify_sql_obj(obj)

@app.route('/<tablename>/<int:id>', methods=['POST'])
def modify_obj(tablename,id):
    table = get_or_create_orm_object(tablename, appengine, Base)
    obj = session.query(table).filter_by(id=id).first()
    f = request.form
    if not obj:
        return "User does not exist.",400
    for key in f.keys():
        setattr(obj,key,f[key])
    session.add(obj)
    session.commit()
    ## note: if users submits invalid fields they'll 
    ## still be in the response 
    ## despite not having been added to the database
    return jsonify_sql_obj(obj)

if __name__ == '__main__':
    app.run()
