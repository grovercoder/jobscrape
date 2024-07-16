import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'QM8kg%sSQhKHv#KJnFZMHZe5PBxUf!#HrG5h^Sm7L'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///home/shawn/Projects/research/jobscrape/jobs.db'
