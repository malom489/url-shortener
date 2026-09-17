from sqlalchemy import Column ,Integer,String,BigInteger,DateTime,ForeignKey,Index
from sqlalchemy.sql import func 
from app.db.session import Base


class Link(Base):
    __tablename__ = "links"   
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(String(50),index=True,nullable=False)
    short_code=Column(String(10),index=True,nullable=False,unique=True)
    original_url=Column(String(255),nullable=False)
    created_by=Column(Integer,ForeignKey("users.id"),nullable=False)
    click_count=Column(BigInteger,default=0)
    created_at=Column(DateTime(timezone=True),server_default=func.now())
    
    __table_args__ = (
        Index("ix_links_tenant_code", "tenant_id", "short_code"),
    )