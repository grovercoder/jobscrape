from jobscrape.models import Base
from sqlalchemy import Column, Integer, String, Text, Boolean

class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=True)
    code = Column(String)
    name = Column(String)
    postings_url = Column(String)

    # indicate if the url is an RSS feed and should use XML parsing instead of HTML parsing
    rss = Column(Boolean, default=False)

    # User ID that added the site
    authored_by = Column(Integer)

    # Some administrative timestamps
    added_date = Column(Integer)
    last_scanned = Column(Integer)

    # ################
    # Paging
    # ################
    # The regular expression to find the page indicator in the URL
    # Do not set a value if the site does not use paging
    page_pattern = Column(String)
    # which regex group is the page number
    page_group = Column(Integer, default=2)
    # indicate how paging is done - usually "page" or "offset"
    page_type = Column(String)

    # ################
    # CSS Selectors
    # ################
    # On the job listing page

    # The HTML element that wraps the list of posting links
    selector_jobs_container = Column(String)
    # How to find the specific links within the container
    selector_job_links = Column(String)

    # On the job detail page
    selector_job_title = Column(String)
    selector_job_id = Column(String)
    selector_location = Column(String)
    selector_job_description = Column(Text)

    @classmethod
    def get_by_code(cls, session, requested_code):
        return session.query(cls).filter(cls.code.ilike(requested_code)).first()

    @classmethod
    def postings_url_exists(cls, session, target):
        return session.query(cls).filter_by(cls.postings_url.ilike(target)).first() is not None

    @classmethod
    def code_exists(cls, session, target):
        return session.query(cls).filter_by(cls.postings_url.ilike(target)).first() is not None

    @classmethod
    def add(cls, session, **kwargs):
        site = cls(**kwargs)

        existing = session.query(Site).filter_by(code=site.code).first()
        if existing:
            return existing
        
        existing = session.query(Site).filter_by(postings_url=site.postings_url).first()
        if existing:
            return existing
        
        session.add(site)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        
        return site

    @classmethod
    def list_all(cls, session):
        return session.query(cls).all()
    
    @classmethod
    def list_enabled(cls, session):
        return session.query(cls).filter(cls.enabled==True).all()