import argparse
import json

from configmodels import Base, DBTable, DBReference, configengine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import MetaData, Column, Table
from sqlalchemy.types import *

def get_config_file_metadata(filename, curr_table):
    config = json.load(open(filename))
    metadata = MetaData()
    Session = sessionmaker(bind=configengine)
    def create_column(column_dict):
        type_dict = {
                'int' : Integer,
                'str' : String(255),
                'string' : String(255),
                'bool' : Boolean,
                'date' : Date,
                'datetime' : DateTime,
                'float' : Float,
                'time' : Time}

        colname = column_dict['name']
        if column_dict['type'] == 'ForeignKey':
            coltype = ForeignKey(column_dict['table'])
            if 'backref' in column_dict:
                to_table = column_dict['table'].split('.')[0]
                to_field = column_dict['table'].split('.')[1]
                from_table_id = curr_table.id
                from_field = column_dict['backref']
                ref = DBReference(to_table, to_field, from_field, from_table_id)
                session = Session()
                session.add(ref)
                session.commit()
        else:
            coltype = type_dict[column_dict['type']]
        return Column(colname, coltype)

    for table in config:
        curr_table = DBTable(table['tablename'], table.get('dbname') or table['tablename'])
        session = Session()
        session.add(curr_table)
        session.commit()
        Table(table['tablename'], metadata,
                Column('id', Integer, primary_key=True),
                *[create_column(column, curr_table) for column in table['columns']],
                extend_existing = True)

    return metadata

if __name__ == '__main__':
    Base.metadata.create_all()
    parser = argparse.ArgumentParser(description='Create the database specified from the config.')
    parser.add_argument('SQLAlchemyURI', type=str, help="the uri for the database.  ex 'sqllite:///:memory:'")
    parser.add_argument('ConfigFile', type=str, help="the filename to read the config from")
    parser.add_argument('--update', action="store_true", help="If set, updates schema instead of overwriting.  Usually this means issuing ALTER TABLE commands instead of DROP TABLE / CREATE TABLE, but that might be different depending on your backend.")
    options = parser.parse_args()
    metadata = get_config_file_metadata(options.ConfigFile)
    engine = create_engine(options.SQLAlchemyURI)
    metadata.bind = engine
    if not options.update:
        metadata.drop_all()
    metadata.create_all()
