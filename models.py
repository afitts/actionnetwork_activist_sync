### models.py ###

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger

Base = declarative_base()

class Member(Base):
    __tablename__ = 'member'
    id = Column(BigInteger, primary_key=True)
    given_name = Column(String)
    family_name = Column(String)
    email_address = Column(String)
    phone_number = Column(String)
    address = Column(String)

    def __repr__(self):
        return "<Member(given_name='{}', family_name='{}', email_address={}, phone_number={}, address={})>" \
            .format(self.given_name, self.family_name, self.email_address, self.phone_number, self.address)

class Member_Attribute(Base):
    __tablename__ = 'member_attribute'
    id = Column(BigInteger, primary_key=True)
    attribute = Column(String)
    value = Column(String)