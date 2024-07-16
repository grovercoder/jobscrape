from sqlalchemy import Column, Integer, String, Text, ForeignKey
from jobscrape.models import Base

class Resume(Base):
    __tablename__ = 'resumes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,  ForeignKey('users.id'))
    title = Column(String)
    content = Column(Text)

    @classmethod
    def for_user(cls, session, user):
        resume = session.query(cls).filter(user_id = user.id).first()
        if resume:
            return resume
        
        return None
    