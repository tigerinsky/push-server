#coding:utf-8
from sqlalchemy import Column, String, Integer
import sqlalchemy.exc

from db import Base, Session
from util.log import logger

class UserPush(Base):
    __tablename__ = 'ci_user_push'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(Integer)
    xg_device_token = Column(String(255))
    device_type = Column(Integer)
    tags = Column(String(255))

    def __init__(self):
        self.uid = 0
        self.xg_device_token = ''
        self.device_type = 0
        self.tags = ''

    @classmethod
    def get_device_info(cls, uid):
        '''
        @return list
        '''
        r = Session.query(cls.xg_device_token, cls.device_type).filter(cls.uid == uid).all()
        return r

    @classmethod
    def get_device_list(cls, uid_list):
        r = Session.query(cls.xg_device_token, cls.device_type).filter(cls.uid.in_(uid_list)).all()
        return r

    @classmethod
    def get_device_type(cls, xg_device_token):
        r = Session.query(cls.device_type).filter(cls.xg_device_token == xg_device_token).first()

        if not r:
            return None

        return r.device_type
    @classmethod
    def update_tags(cls, xg_device_token, tags):
        try:
            r = Session.query(cls).filter(cls.xg_device_token == xg_device_token).first()
            r.tags = tags
            Session.add(r)
            Session.commit()
        except sqlalchemy.exc.IntegrityError, e:
            logger.warning('msg[update tags error] table[%s] e[%s]' % (__tablename__, e))
            Session.rollback()
