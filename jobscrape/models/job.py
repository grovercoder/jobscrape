
from sqlalchemy import Column, Integer, String, Text
from jobscrape.models import Base
from jobscrape.models.keyword import Keyword
from jobscrape.models.jobkeyword import JobKeyword

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    collected = Column(Integer)
    source = Column(String)
    title = Column(String)
    url = Column(String, unique=True)
    description = Column(Text)
    location = Column(String)
    remote_id = Column(String)

    @classmethod
    def add(cls, session, **kwargs):
        job = cls(**kwargs)

        existing_job = session.query(Job).filter_by(url=job.url).first()
        if existing_job:
            return existing_job

        existing_job = session.query(Job).filter_by(source=job.source, title=job.title).first()
        if existing_job:
            return existing_job

        if job.remote_id:
            existing_job = session.query(Job).filter_by(source=job.source, remote_id=job.remote_id).first()
            if existing_job:
                return existing_job

        session.add(job)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        return job

    @classmethod
    def job_url_exists(cls, session, target):
        return session.query(cls).filter_by(url=target).first() is not None

    @classmethod
    def get_jobs_with_keywords(cls, session, keyword_list):
        # Find keyword IDs for the given keyword list
        keyword_ids = session.query(Keyword.id).filter(Keyword.keyword.in_(keyword_list)).all()
        keyword_ids = [k[0] for k in keyword_ids]  # Extract IDs from the result

        # Query to find jobs that have any of the given keywords
        jobs = session.query(Job).join(JobKeyword).filter(JobKeyword.keyword_id.in_(keyword_ids)).all()

        return jobs
