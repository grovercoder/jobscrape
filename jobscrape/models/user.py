from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String
from jobscrape.models import Base

class User(UserMixin, Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    password = Column(String)
    stripe_id = Column(String)
    checkout_session_id = Column(String)
    subscription_tier = Column(String)
    subscription_status = Column(String)
    date_paid = Column(String)
    last_active_timestamp = Column(Integer)

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = generate_password_hash(password, method='pbkdf2:sha256')  # Ensure correct hashing method

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    @classmethod
    def create(cls, email, username, password):
        # Create a new user instance
        new_user = cls(email=email, username=username, password=password)
        return new_user