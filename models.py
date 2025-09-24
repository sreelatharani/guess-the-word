from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import db

class User(db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Word(db.Model):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True)
    value = Column(String(5), unique=True, nullable=False)  # uppercase 5-letter

class Game(db.Model):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished = Column(Boolean, default=False)
    won = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)

    user = relationship("User")
    word = relationship("Word")
    guesses = relationship("Guess", cascade="all, delete-orphan")

class Guess(db.Model):
    __tablename__ = "guesses"
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    guess_text = Column(String(5), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    correct_positions = Column(String)  # e.g. "GOGXX"
