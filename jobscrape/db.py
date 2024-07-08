from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError

import requests
from bs4 import BeautifulSoup

Base = declarative_base()

class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True)
    keyword = Column(String, unique=True)

    @classmethod
    def add(cls, session, keyword):
        existing_keyword = session.query(cls).filter_by(keyword=keyword).first()
        if existing_keyword:
            return existing_keyword
        new_keyword = cls(keyword=keyword)
        session.add(new_keyword)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        return new_keyword

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

class Resume(Base):
    __tablename__ = 'resumes'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)

    
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
    

class ResumeKeyword(Base):
    __tablename__ ='resumekeywords'
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer, ForeignKey('resumes.id'), primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), primary_key=True)
    

# Define relationships
Keyword.jobs = relationship('JobKeyword', back_populates='keyword')
Job.keywords = relationship('JobKeyword', back_populates='job')
JobKeyword.job = relationship('Job', back_populates='keywords')
JobKeyword.keyword = relationship('Keyword', back_populates='jobs')

class DB:
    def __init__(self, dbpath="jobs.db"):
        self.dbpath = dbpath
        self.engine = None

        self.setup_db()

    def setup_db(self):
        if not self.dbpath:
            raise ValueError("No database path provided")
        
        self.engine = create_engine(f"sqlite:///{self.dbpath}")
        Base.metadata.create_all(self.engine, checkfirst=True)
    
    def get_session(self):
        if self.engine:
            Session = sessionmaker(bind=self.engine)
            return Session()
    
        return None
    
    # def add_job(self, job):
    #     session = self.get_session()

    #     if not self.job_exists(job):
    #         try:
    #             session.add(job)
    #             session.commit()
    #             job_id = job.id
    #         except IntegrityError:
    #             session.rollback()
    #             print(f"Job with URL {job.url} already exists. Skipping...")
    #             job_id = -1
    #         finally:
    #             session.close()
    #         return job_id
    #     else:
    #         print(f'Job already in DB: {job.source} : {job.title}')
    

    # def job_url_exists(self, url):
    #     session = self.get_session()
    #     try:
    #         exists = session.query(Job).filter_by(url=url).first() is not None
    #     finally:
    #         session.close()
    #     return exists
    
    # def job_exists(self, job):
    #     session = self.get_session()
    #     try:
    #         # Check for job with matching source and title
    #         existing_job = session.query(Job).filter_by(source=job.source, title=job.title).first()
    #         if existing_job:
    #             return True
    #         # Check for job with matching remote_id
    #         if job.remote_id:
    #             existing_job = session.query(Job).filter_by(source=job.source, remote_id=job.remote_id).first()
    #             if existing_job:
    #                 return True
    #         return False
    #     finally:
    #         session.close()

    # def job_keyword_exists(self, job_id, keyword):
    #     session = self.get_session()
    #     existing = session.query(JobKeyword).filter_by(job=job_id, keyword=keyword).first() is not None
    #     session.close()

    #     if existing:
    #         return True
        
    #     return False

    # def add_job_keyword(self, job_id, keyword):
    #     if not self.job_keyword_exists(job_id, keyword):
    #         session = self.get_session()
    #         jk = JobKeyword()
    #         jk.job = job_id
    #         jk.keyword = keyword
    #         session.add(jk)
    #         session.commit()
    #         session.close()

