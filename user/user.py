from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)


class Request(Base):
    __tablename__ = "requests"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    service_name = Column(String, primary_key=True)
    request_count = Column(Integer)
