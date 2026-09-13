from sqlalchemy import Column,Integer,String,DateTime
from sqlalchemy import func
from app.db.session import Base

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True,index=True)
    full_name = Column(String)
    hashed_password=Column(String(100),nullable=False)
    email=Column(String(50),unique=True,index=True,nullable=False)
    tenant_id=Column(String(10),nullable=False)
    is_active=Column(Integer,default=1)
    created_at=Column(DateTime,server_default=func.now())