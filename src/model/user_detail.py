#coding:utf-8
from sqlalchemy import Column, String, Integer
import sqlalchemy.exc

from db import Base, Session
from util.log import logger

class UserDetail(Base):
    __tablename__ = 'ci_user_detail'

    uid = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String(255))
    school = Column(String(255))
    ukind_verify = Column(Integer)

    def __init__(self):
        self.uid = 0
        self.xg_device_token = ''
        self.device_type = 0
        self.tags = ''

    @classmethod
    def get_user(cls, uid):
        '''
        @return list
        '''
        r = Session.query(cls).filter(cls.uid == uid).first()
