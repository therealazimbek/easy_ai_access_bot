from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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


# Enable echo for more information
engine = create_engine("sqlite:///bot_database.db", echo=True)

try:
    # Create tables
    Base.metadata.create_all(engine)
    print("Tables created successfully")
except Exception as e:
    print(f"Error creating tables: {e}")

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()


# Function to insert user information
def insert_user(user_id, username, first_name, last_name):
    user = User(
        user_id=user_id, username=username, first_name=first_name, last_name=last_name
    )
    session.merge(user)
    session.commit()


# Function to update request counts
def update_request_count(user_id, service_name):
    request = (
        session.query(Request)
        .filter_by(user_id=user_id, service_name=service_name)
        .first()
    )
    if request:
        request.request_count += 1
    else:
        request = Request(user_id=user_id, service_name=service_name, request_count=1)
        session.merge(request)
    session.commit()


# Example usage:
insert_user(123, "user123", "John", "Doe")
update_request_count(123, "openai")
update_request_count(123, "google_vision")
