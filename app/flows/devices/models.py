from app.db_utils import safe_commit
from sqlalchemy import Column, Integer, String
from app.database import Base

class Device(Base):
    __tablename__ = "devices_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    ip = Column(String)
    category = Column(String)
