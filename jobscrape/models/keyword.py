from jobscrape.models import Base
from sqlalchemy import Column, Integer, String

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