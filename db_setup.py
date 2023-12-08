from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///bot_database.db', echo=True)
Base.metadata.create_all(engine)
