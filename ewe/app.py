from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from flask import Flask

app = Flask(__name__)

appengine = create_engine('sqlite:////tmp/app.db', echo=True)

names_to_orm_classes = {}

Base = declarative_base(bind=engine)

class NoSuchTableException(ValueError): pass

def get_or_create_orm_object(name):
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
        exec(code_to_generate_this_table)
        names_to_orm_classes[name] = locals()[new_table_id]
    return names_to_orm_classes[name]

if __name__ == '__main__':
    app.run()
