"""
CRUD operations for notes and tags in NoteEase.
Provides create, read, update, and delete operations for the database.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from .models import Note, Tag
from .schemas import NoteCreate, NoteUpdate, TagCreate


# ============================================================
# Tag CRUD Operations
# ============================================================

# PUBLIC_INTERFACE
def get_tag(db: Session, tag_id: int) -> Optional[Tag]:
    """
    Retrieve a single tag by its ID.

    Args:
        db: Database session
        tag_id: ID of the tag to retrieve

    Returns:
        Tag instance or None if not found
    """
    return db.query(Tag).filter(Tag.id == tag_id).first()


# PUBLIC_INTERFACE
def get_tag_by_name(db: Session, name: str) -> Optional[Tag]:
    """
    Retrieve a tag by its name.

    Args:
        db: Database session
        name: Name of the tag to retrieve

    Returns:
        Tag instance or None if not found
    """
    return db.query(Tag).filter(Tag.name == name).first()


# PUBLIC_INTERFACE
def get_tags(db: Session, skip: int = 0, limit: int = 100) -> List[Tag]:
    """
    Retrieve all tags with optional pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Tag instances
    """
    return db.query(Tag).offset(skip).limit(limit).all()


# PUBLIC_INTERFACE
def create_tag(db: Session, tag: TagCreate) -> Tag:
    """
    Create a new tag or return an existing one with the same name.

    Args:
        db: Database session
        tag: TagCreate schema with the tag data

    Returns:
        Created or existing Tag instance
    """
    existing = get_tag_by_name(db, tag.name)
    if existing:
        return existing

    db_tag = Tag(name=tag.name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


# PUBLIC_INTERFACE
def delete_tag(db: Session, tag_id: int) -> Optional[Tag]:
    """
    Delete a tag by its ID.

    Args:
        db: Database session
        tag_id: ID of the tag to delete

    Returns:
        Deleted Tag instance or None if not found
    """
    db_tag = get_tag(db, tag_id)
    if db_tag:
        db.delete(db_tag)
        db.commit()
    return db_tag


# ============================================================
# Note CRUD Operations
# ============================================================

# PUBLIC_INTERFACE
def get_note(db: Session, note_id: int) -> Optional[Note]:
    """
    Retrieve a single note by its ID.

    Args:
        db: Database session
        note_id: ID of the note to retrieve

    Returns:
        Note instance or None if not found
    """
    return db.query(Note).filter(Note.id == note_id).first()


# PUBLIC_INTERFACE
def get_notes(
    db: Session,
    query: Optional[str] = None,
    tag_ids: Optional[List[int]] = None,
    pinned_only: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20
) -> tuple:
    """
    Retrieve notes with optional filtering and pagination.

    Args:
        db: Database session
        query: Text to search in title and content
        tag_ids: List of tag IDs to filter by
        pinned_only: If True, only return pinned notes
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Tuple of (list of Note instances, total count)
    """
    filters = []

    # Text search filter
    if query:
        search_term = f'%{query}%'
        filters.append(or_(
            Note.title.ilike(search_term),
            Note.content.ilike(search_term)
        ))

    # Pinned filter
    if pinned_only is not None:
        filters.append(Note.is_pinned == pinned_only)

    db_query = db.query(Note)

    # Tag filter
    if tag_ids:
        for tag_id in tag_ids:
            db_query = db_query.filter(Note.tags.any(Tag.id == tag_id))

    if filters:
        db_query = db_query.filter(and_(*filters))

    # Order pinned notes first, then by update time
    db_query = db_query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())

    total = db_query.count()
    notes = db_query.offset(skip).limit(limit).all()

    return notes, total


# PUBLIC_INTERFACE
def create_note(db: Session, note: NoteCreate) -> Note:
    """
    Create a new note.

    Args:
        db: Database session
        note: NoteCreate schema with the note data

    Returns:
        Created Note instance
    """
    db_note = Note(
        title=note.title,
        content=note.content,
        is_pinned=note.is_pinned
    )

    # Associate tags if provided
    if note.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(note.tag_ids)).all()
        db_note.tags = tags

    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


# PUBLIC_INTERFACE
def update_note(db: Session, note_id: int, note_update: NoteUpdate) -> Optional[Note]:
    """
    Update an existing note.

    Args:
        db: Database session
        note_id: ID of the note to update
        note_update: NoteUpdate schema with fields to update

    Returns:
        Updated Note instance or None if not found
    """
    db_note = get_note(db, note_id)
    if not db_note:
        return None

    update_data = note_update.model_dump(exclude_unset=True)

    # Handle tag updates separately
    if 'tag_ids' in update_data:
        tag_ids = update_data.pop('tag_ids')
        if tag_ids is not None:
            tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            db_note.tags = tags
        else:
            db_note.tags = []

    # Update other fields
    for field, value in update_data.items():
        setattr(db_note, field, value)

    db.commit()
    db.refresh(db_note)
    return db_note


# PUBLIC_INTERFACE
def delete_note(db: Session, note_id: int) -> Optional[Note]:
    """
    Delete a note by its ID.

    Args:
        db: Database session
        note_id: ID of the note to delete

    Returns:
        Deleted Note instance or None if not found
    """
    db_note = get_note(db, note_id)
    if db_note:
        db.delete(db_note)
        db.commit()
    return db_note


# PUBLIC_INTERFACE
def toggle_pin_note(db: Session, note_id: int) -> Optional[Note]:
    """
    Toggle the pinned status of a note.

    Args:
        db: Database session
        note_id: ID of the note to toggle pin

    Returns:
        Updated Note instance or None if not found
    """
    db_note = get_note(db, note_id)
    if db_note:
        db_note.is_pinned = not db_note.is_pinned
        db.commit()
        db.refresh(db_note)
    return db_note
