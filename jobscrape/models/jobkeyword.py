from sqlalchemy import Column, Integer, ForeignKey
from jobscrape.models import Base

class JobKeyword(Base):
    __tablename__ = 'jobkeywords'
    job_id = Column(Integer, ForeignKey('jobs.id'), primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), primary_key=True)

    @classmethod
    def add(cls, session, **kwargs):

        jobkeyword = cls(**kwargs)  
        existing_record = session.query(JobKeyword).filter_by(job_id=jobkeyword.job_id, keyword_id=jobkeyword.keyword_id).first()
        if existing_record:
            return existing_record
        
        session.add(jobkeyword)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    