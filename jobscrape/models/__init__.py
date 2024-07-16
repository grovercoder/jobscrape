from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
# from sqlalchemy.exc import IntegrityError

Base = declarative_base()

from .keyword import Keyword
from .job import Job
from .jobkeyword import JobKeyword
from .resume import Resume
from .resumekeyword import ResumeKeyword
from .user import User
from .site import Site
from .user import User

Keyword.jobs = relationship('JobKeyword', back_populates='keyword')
Job.keywords = relationship('JobKeyword', back_populates='job')
JobKeyword.job = relationship('Job', back_populates='keywords')
JobKeyword.keyword = relationship('Keyword', back_populates='jobs')
# User.resumes = relationship('Resume', back_populates="user", uselist=True)