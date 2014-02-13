from sqlalchemy import (
    Column,
    Integer,
    Text,
    Table,
    ForeignKey,
)

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
)
from pyramid.security import (
    Allow,
    Everyone,
)

from zope.sqlalchemy import ZopeTransactionExtension
from slugify import slugify
from passlib.hash import sha256_crypt

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class RootFactory(object):
    __acl__ = [(Allow, Everyone, 'view'),
               (Allow, 'admins', 'edit')]

    def __init__(self, request):
        pass


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    slug = Column(Text)
    body = Column(Text)

    def __init__(self, title, body):
        self.title = title
        self.slug = slugify(self.title)
        self.body = body


association_table = Table('association', Base.metadata,
                          Column('users_id', Integer, ForeignKey('users.id')),
                          Column('groups_id', Integer, ForeignKey('groups.id'))
                          )


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(Text, unique=True, nullable=False)
    password = Column(Text, nullable=False)
    email = Column(Text)
    group = relationship("Group", secondary=association_table, backref="parents")

    def __init__(self, username, password, email):
        self.username = username
        self.password = sha256_crypt.encrypt(password)
        self.email = email


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    description = Column(Text)

    def __init__(self, name):
        self.name = name