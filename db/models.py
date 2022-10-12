from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, ARRAY, Boolean
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=True)
    username = Column(String, nullable=True)

    def __repr__(self):
        return f'{self.id} {self.first_name} {self.username}'


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)


class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cost = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    comment = Column(String, nullable=True)
    date = Column(TIMESTAMP, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    user = relationship("User", backref="expenses")
    category = relationship("Category", backref="expenses")


class Income(Base):
    __tablename__ = 'income'

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    date = Column(TIMESTAMP, nullable=False, primary_key=True)
    name = Column(String, nullable=True)
    value = Column(Integer)

    user = relationship("User", backref="user_summary")


class UserCategory(Base):
    __tablename__ = 'user_category'

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False, primary_key=True)
    costs = Column(ARRAY(String), nullable=True)
    status = Column(String, default='monthly')
    budget = Column(Integer, default=0)
    is_auto = Column(Boolean, default=False)

    user = relationship("User", backref="user_category")
    category = relationship("Category", backref="user_category")
