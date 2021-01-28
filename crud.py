from config import DATABASE_URI
from models import Base, Member, Member_Attribute
from contextlib import contextmanager
from actionnetwork_activist_sync.full_member_api_pull import full_member_pull
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy_utils import database_exists, create_database
import pandas as pd


engine = create_engine(DATABASE_URI,paramstyle="format") #paramstyle is so column names with parentheses don't crash

Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def recreate_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    recreate_database()
    # add_data()
    db = scoped_session(sessionmaker(bind=engine))
    #db.execute("CREATE TABLE member();")
    #db.execute("CREATE TABLE member_attribute();")
    df = full_member_pull() #pd.read_csv('/Users/afitts/DSA/ActionNetwork_full_member_DC_export_2020-12-05',header=0)  
    mem_dict = df[['given_name','family_name','email_address','phone_number','address']]#.to_dict()
    mem_attr_dict = df.drop(['given_name','family_name','email_address','phone_number','address'],axis=1)\
        .stack().reset_index().rename(columns={'level_0' : 'id', 'level_1' : 'attribute', 0 : 'value'})#.to_dict()
    mem_dict.to_sql('member', engine,if_exists='replace')
    mem_attr_dict.to_sql('member_attribute', engine,if_exists='replace')
    db.commit()
    #member = Member(**mem_dict)
    #member_attr = Member_Attribute(**mem_attr_dict)
    #with session_scope() as s:
    #    s.add(member)
        #s.add(member_attr)
