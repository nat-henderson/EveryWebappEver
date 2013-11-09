import random
import string
import argparse
import StringIO
import json

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine,String,Integer
from sqlalchemy.schema import MetaData, Table, Column
from flask import Flask, request, render_template
from flask.ext.security import login_required

from utilities import *
from configmodels import configengine, DBReference
from config import get_config_file_metadata

app = Flask(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create the database specified from the config.')
    parser.add_argument('--uri', default='sqlite:////tmp/app.db', type=str, help="the uri for the database.  ex 'sqllite:///:memory:'")
    options = parser.parse_args()

appengine = create_engine(options.uri, echo=True)
Session = sessionmaker(bind=appengine)
session = Session()

ConfigSession = sessionmaker(bind=configengine)
configsession = ConfigSession()

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

@app.route('/<tablename>/lookup/<attrname>/<value>', methods=['GET'])
def get_obj_list_by_attr(tablename, attrname, value):
    table = get_or_create_orm_object(tablename, appengine, Base)
    if not hasattr(table,attrname):
        return "This table does not have a column of that name.",412
    attr = getattr(table,attrname)
    obj_list=session.query(table).filter(attr==value).all() 
    print obj_list
    return jsonify_sql_obj(obj_list)

@app.route('/<tablename>/<int:id>', methods=['GET'])
def get_obj_from_table(tablename, id):
    table = get_or_create_orm_object(tablename, appengine, Base)
    obj = session.query(table).filter_by(id=id).first()
    if not obj:
        return "Object does not exist.",400
    return jsonify_sql_obj(obj)

@app.route('/<tablename>/<int:id>/<attrname>', methods=['GET'])
def get_obj_attr(tablename,id,attrname):
    session = Session() #I wish we didn't need this
    table = get_or_create_orm_object(tablename, appengine, Base)
    obj = session.query(table).filter_by(id=id).first()
    if not obj:
        return "Object does not exist", 400
    if hasattr(obj, attrname):
        ret = getattr(obj,attrname)
        return json.dumps({attrname:ret})
    c_session = ConfigSession()
    dbref = c_session.query(DBReference).filter_by(from_name = attrname, from_table = tablename).first()
    if not dbref:
        return "Attribute does not exist", 400
    table_to_search = dbref.to_table.database_table
    table_obj = get_or_create_orm_object(table_to_search, appengine, Base)
    session = Session()
    linked_objs = session.query(table_obj).filter_by(**{dbref.fkey_name: getattr(obj, dbref.fkey_to_attribute)}).all()
    return jsonify_sql_obj(linked_objs)


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

@app.route('/createtable/<tablename>', methods = ['POST'])
def create_table(tablename):
    try:
        # this will raise exception if DNE
        get_or_create_orm_object(tablename)
        return "Table already exists", 412
    except Exception as e:
        print e
        pass
    columns = request.form.to_dict()
    json_dict = {"tablename" : tablename, "columns" : []}
    def make_fake_column(colname, coltype):
        if coltype.startswith("ForeignKey"):
            return {"name":colname, "type":"ForeignKey", "table":coltype[len("ForeignKey_"):], "backref":tablename}
        else:
            return {"name":colname, "type":coltype}

    for colname, coltype in columns.items():
        json_dict["columns"].append(make_fake_column(colname, coltype))

    new_table_metadata = get_config_file_metadata(StringIO.StringIO(json.dumps([json_dict])), appengine)
    new_table_metadata.create_all()
    return "Table created."

if __name__ == '__main__':
   app.run(debug=True)
