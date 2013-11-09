import argparse

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData, Column, Table
from sqlalchemy.types import *

def get_config_file_base(filename):
    config = json.load(filename)
    metadata = MetaData()
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
        else:
            coltype = type_dict[column_dict['type']]
        return Column(colname, coltype)

    for table in config:
        Table(table['tablename'], metadata,
                Column('id', Integer, primary_key=True,
                *[create_column(column) for column in table['columns']]),
                extend_existing = True)

    return metadata

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create the database specified from the config.')
    parser.add_argument('SQLAlchemyURI', type=str, help="the uri for the database.  ex 'sqllite:///:memory:'")
    parser.add_argument('ConfigFile', type=str, help="the filename to read the config from")
    parser.add_argument('--update', action="store_true", help="If set, updates schema instead of overwriting.")
    parser.parse_args()
    metadata = get_config_file_metadata(parser.ConfigFile)
    engine = create_engine(parser.SQLAlchemyURI)
    metadata.bind = engine
    if not parser.update:
        metadata.drop_all()
    metadata.create_all()
