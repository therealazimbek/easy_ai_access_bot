from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from user.user import User, Request


class UserRepository:
    def __init__(self):
        self.Base = declarative_base()
        self.engine = create_engine("sqlite:///bot_database.db", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def insert_user(self, user_id, username, first_name, last_name):
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.merge(user)
        self.session.commit()

    def update_request_count(self, user_id, service_name):
        request = (
            self.session.query(Request)
            .filter_by(user_id=user_id, service_name=service_name)
            .first()
        )
        if request:
            request.request_count += 1
        else:
            request = Request(
                user_id=user_id, service_name=service_name, request_count=1
            )
            self.session.merge(request)
        self.session.commit()

    def get_service_counts(self, user_id):
        result = (
            self.session.query(Request.service_name, Request.request_count)
            .filter_by(user_id=user_id)
            .all()
        )
        service_counts = {service: count for service, count in result}

        return service_counts

    def user_exists(self, user_id):
        user = self.session.query(User).filter_by(user_id=user_id).first()
        return user is not None
