import argparse
import json

from configmodels import Base, DBTable, DBReference, configengine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import MetaData, Column, Table
from sqlalchemy.types import *

column_type_dict = {
    'int' : Integer,
    'str' : String(255),
    'string' : String(255),
    'bool' : Boolean,
    'date' : Date,
    'datetime' : DateTime,
    'float' : Float,
    'time' : Time}

def get_config_file_metadata(configfile, engine):
    config = json.load(configfile)
    metadata = MetaData(bind=engine)
    Session = sessionmaker(bind=configengine)
    def create_column(column_dict, curr_table):
        colname = column_dict['name']
        if column_dict['type'] == 'ForeignKey':
            coltype = ForeignKey(column_dict['table'])
            if 'backref' in column_dict:
                to_table_id = curr_table.id
                from_table = column_dict['table'].split('.')[0]
                fkey_to_attribute = column_dict['table'].split('.')[1]
                fkey_name = colname
                from_name = column_dict['backref']
                ref = DBReference(from_table = from_table, from_name = from_name,
                        to_table_id = to_table_id, fkey_name = fkey_name,
                        fkey_to_attribute = fkey_to_attribute)
                session = Session()
                session.add(ref)
                session.commit()
        else:
            coltype = column_type_dict[column_dict['type']]
        return Column(colname, coltype)

    for table in config:
        curr_table = DBTable(name = table['tablename'],
                database_table = table.get('dbname') or table['tablename'],
                is_user = table.get('is_user', False))
        if table.get('is_user'):
            if not any(column['name'] == 'username' for column in table['columns']):
                table['columns'].append[{'name':'username', 'type':'str'}]
            if not any(column['name'] == 'password' for column in table['columns']):
                table['columns'].append[{'name':'password', 'type':'str'}]
        session = Session()
        session.add(curr_table)
        session.commit()
        Table(table['tablename'], metadata,
                Column('id', Integer, primary_key=True),
                *[create_column(column, curr_table) for column in table['columns']])

    return metadata

if __name__ == '__main__':
    Base.metadata.drop_all()
    Base.metadata.create_all()
    parser = argparse.ArgumentParser(description='Create the database specified from the config.')
    parser.add_argument('SQLAlchemyURI', type=str, help="the uri for the database.  ex 'sqllite:///:memory:'")
    parser.add_argument('ConfigFile', type=str, help="the filename to read the config from")
    parser.add_argument('--update', action="store_true", help="If set, updates schema instead of overwriting.  Usually this means issuing ALTER TABLE commands instead of DROP TABLE / CREATE TABLE, but that might be different depending on your backend.")
    options = parser.parse_args()
    engine = create_engine(options.SQLAlchemyURI)
    metadata = get_config_file_metadata(open(options.ConfigFile), engine)
    metadata.bind = engine
    if not options.update:
        metadata.drop_all()
    metadata.create_all()
