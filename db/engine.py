from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db.models import Base
from app.config import DB


def get_db() -> Session:
    engine = create_engine(DB)
    _Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return _Session()
