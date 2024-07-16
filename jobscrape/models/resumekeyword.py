from sqlalchemy import Column, Integer, ForeignKey
from jobscrape.models import Base

class ResumeKeyword(Base):
    __tablename__ ='resumekeywords'
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'), primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), primary_key=True)
    