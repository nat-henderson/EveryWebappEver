import random
import string
import argparse

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData, Table
from flask import Flask, request

from utilities import *

app = Flask(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create the database specified from the config.')
    parser.add_argument('--uri', default='sqlite:////tmp/app.db', type=str, help="the uri for the database.  ex 'sqllite:///:memory:'")
    options = parser.parse_args()

appengine = create_engine(options.uri, echo=True)
Session = sessionmaker(bind=appengine)
session = Session()

names_to_orm_classes = {}

Base = declarative_base(bind=appengine)

class NoSuchTableException(ValueError): pass

def get_or_create_orm_object(name, appengine = appengine, Base = Base):
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
        new_table = locals()[new_table_id]
        names_to_orm_classes[name] = new_table

    return names_to_orm_classes[name]

@app.route('/<tablename>/<int:id>', methods=['GET'])
def get_obj_from_table(tablename, id):
    table = get_or_create_orm_object(tablename, appengine, Base)
    obj = session.query(table).filter_by(id=id).first()
    if not obj:
        return "Object does not exist.",400
    return jsonify_sql_obj(obj)

@app.route('/<tablename>/<int:id>', methods=['POST'])
def modify_obj(tablename,id):
    table = get_or_create_orm_object(tablename, appengine, Base)
    obj = session.query(table).filter_by(id=id).first()
    f = request.form
    if not obj:
        return "Object does not exist.",400
    for key in f.keys():
        setattr(obj,key,f[key])
    session.add(obj)
    session.commit()
    ## note: if user submits invalid fields
    ## they'll still be in the response
    ## despite not having been added to the database
    return jsonify_sql_obj(obj)

@app.route('/<tablename>',methods=['POST'])
def create_obj(tablename):
    orm_obj = get_or_create_orm_object(tablename, appengine, Base)
    obj_args = request.form.to_dict()
    obj = orm_obj(**obj_args)
    session.add(obj)
    session.commit()
    return jsonify_sql_obj(obj)

@app.route('/<tablename>/<int:id>', methods=['DELETE'])
def delete_obj(tablename,id):
    table = get_or_create_orm_object(tablename, appengine, Base)
    obj = session.query(table).filter_by(id=id).first()
    if not obj:
        return "Object does not exist.",400
    session.delete(obj)
    session.commit()
    return "Object deleted.",204

if __name__ == '__main__':
   app.run(debug = True)
