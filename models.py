from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, BigInteger
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
    id = Column(BigInteger, primary_key=True) # Telegram ID
    username = Column(String)
    points = Column(Integer, default=1000)
    wins = Column(Integer, default=0)
    last_maintenance_check = Column(DateTime, default=datetime.datetime.utcnow)
    
    idols = relationship("UserIdol", back_populates="owner")

class IdolTemplate(Base):
    """Global library of idols available in gacha"""
    __tablename__ = "idol_templates"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    group_name = Column(String)
    rarity = Column(String) # C, B, A, S, SS
    base_vocal = Column(Integer)
    base_dance = Column(Integer)
    base_rap = Column(Integer)

class UserIdol(Base):
    """Specific idol instance owned by a user"""
    __tablename__ = "user_idols"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    template_id = Column(Integer, ForeignKey("idol_templates.id"))
    
    vocal = Column(Integer)
    dance = Column(Integer)
    rap = Column(Integer)
    morale = Column(Integer, default=100)
    energy = Column(Integer, default=100)
    
    status = Column(Enum(IdolStatus), default=IdolStatus.ACTIVE)
    busy_until = Column(DateTime, nullable=True)
    contract_expiry = Column(DateTime)
    
    # Marketplace
    for_sale = Column(Boolean, default=False)
    sale_price = Column(Integer, default=0)
    
    owner = relationship("User", back_populates="idols")
    template = relationship("IdolTemplate")

class GlobalEvent(Base):
    __tablename__ = "global_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String) # NSFW_SPONSOR, CHARITY
    description = Column(String, default="")
    points = Column(Integer)
    is_taken = Column(Boolean, default=False)
    taken_by_user_id = Column(BigInteger, nullable=True)
    chat_id = Column(BigInteger, nullable=True) # Group where it was posted
    message_id = Column(Integer, nullable=True) # Message ID to edit later
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BotGroup(Base):
    """Tracks groups where the bot is active"""
    __tablename__ = "bot_groups"
    chat_id = Column(BigInteger, primary_key=True)
    title = Column(String, default="")
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
