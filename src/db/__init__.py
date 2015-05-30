#coding:utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from config import HOST
from config import PORT
from config import PASSPORT
from config import USER
from config import DBNAME

connect_url = 'mysql+mysqldb://%s:%s@%s:%s/%s?charset=utf8' % (USER, PASSPORT, HOST, PORT, DBNAME)
engine = create_engine(connect_url, pool_size=250, max_overflow=0, pool_recycle=3600)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
Base = declarative_base()

__all__ = ['Base', 'Session']
