from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from jobscrape.models import Base, Keyword, Job, JobKeyword, Resume, ResumeKeyword


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
    
    def purge_old_jobs(self, olderthan=7):
        session = self.get_session()

        # remove jobs older than seven days
        limit = int((datetime.utcnow() - timedelta(days=olderthan)).timestamp() * 1000)
        try:
            # Delete from jobkeywords where job_id is in jobs to be deleted
            session.query(JobKeyword).filter(
                JobKeyword.job_id.in_(
                    session.query(Job.id).filter(Job.collected < limit)
                )
            ).delete(synchronize_session='fetch')

            # Delete from jobs where collected date is less than limit
            session.query(Job).filter(Job.collected < limit).delete(synchronize_session='fetch')

            # Commit the transaction
            session.commit()

        except Exception as e:
            # Rollback in case of any exception
            session.rollback()
            print(f"Error occurred: {e}")
    