from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum

class IdolStatus(enum.Enum):
    ACTIVE = "active"
    HIATUS = "hiatus"
    WORLD_TOUR = "world_tour"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True) # Telegram ID
    username = Column(String)
    points = Column(Integer, default=1000)
    fandom_id = Column(Integer, ForeignKey("fandoms.id"), nullable=True)
    wins = Column(Integer, default=0)
    last_maintenance_check = Column(DateTime, default=datetime.datetime.utcnow)
    
    idols = relationship("UserIdol", back_populates="owner")
    fandom = relationship("Fandom", back_populates="members")

class Fandom(Base):
    __tablename__ = "fandoms"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    total_points = Column(Integer, default=0)
    
    members = relationship("User", back_populates="fandom")

class IdolTemplate(Base):
    """Global library of idols"""
    __tablename__ = "idol_templates"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    group_name = Column(String)
    rarity = Column(String) # C, B, A, S, SS
    base_vocal = Column(Integer)
    base_dance = Column(Integer)
    base_rap = Column(Integer)
    image_url = Column(String, nullable=True)

class UserIdol(Base):
    """Specific idol instance owned by a user"""
    __tablename__ = "user_idols"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    template_id = Column(Integer, ForeignKey("idol_templates.id"))
    
    vocal = Column(Integer)
    dance = Column(Integer)
    rap = Column(Integer)
    morale = Column(Integer, default=100)
    energy = Column(Integer, default=100)
    
    status = Column(Enum(IdolStatus), default=IdolStatus.ACTIVE)
    contract_expiry = Column(DateTime)
    last_interaction = Column(DateTime, default=datetime.datetime.utcnow)
    
    owner = relationship("User", back_populates="idols")
    template = relationship("IdolTemplate")

class Photocard(Base):
    __tablename__ = "photocards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    idol_name = Column(String)
    multiplier = Column(Float, default=1.05) # 5% bonus

class GlobalEvent(Base):
    __tablename__ = "global_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String)
    points = Column(Integer)
    is_taken = Column(Boolean, default=False)
    taken_by_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
