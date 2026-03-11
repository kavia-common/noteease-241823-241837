"""
Database models for the NoteEase application.
Defines SQLAlchemy ORM models for Notes and Tags.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Association table for many-to-many relationship between notes and tags
note_tags = Table(
    'note_tags',
    Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Note(Base):
    """ORM model representing a Note."""

    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, default='Untitled')
    content = Column(Text, nullable=True, default='')
    is_pinned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    # Many-to-many relationship with tags
    tags = relationship('Tag', secondary=note_tags, back_populates='notes',
                        lazy='selectin')


class Tag(Base):
    """ORM model representing a Tag."""

    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Many-to-many relationship with notes
    notes = relationship('Note', secondary=note_tags, back_populates='tags',
                         lazy='selectin')
