from database import Base,engine
from sqlalchemy import Column,Integer,String,Boolean,Float,Date

class Transaction(Base):
    __tablename__='transaction'#creats table with this name 'transaction'

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    category = Column(String)
    description = Column(String)
    is_income = Column(Boolean)
    date = Column(String)

class Goal(Base):
    __tablename__ = 'goals'
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    goal = Column(String, nullable=False)
    description = Column(String, nullable=False)
    