"""
NoteEase FastAPI Backend Application.

This module provides REST API endpoints for managing notes including:
- CRUD operations for notes and tags
- Search and filtering
- Pinning notes as favorites
- Tag management
"""
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import get_db, init_db
from .schemas import (
    NoteCreate, NoteUpdate, NoteResponse, NoteListResponse,
    TagCreate, TagResponse
)
from . import crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: startup and shutdown events."""
    # Startup: initialize database
    init_db()
    yield
    # Shutdown: nothing to clean up


# Application metadata
app = FastAPI(
    title='NoteEase API',
    description=(
        'A clean, minimal REST API for managing notes with tagging, '
        'pinning, search, and autosave support.'
    ),
    version='1.0.0',
    lifespan=lifespan,
    openapi_tags=[
        {'name': 'notes', 'description': 'Operations for creating and managing notes'},
        {'name': 'tags', 'description': 'Operations for creating and managing tags'},
        {'name': 'health', 'description': 'Health check endpoints'},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ============================================================
# Health Check
# ============================================================

@app.get('/', tags=['health'], summary='Health Check', operation_id='health_check')
def health_check():
    """
    Check if the API is running and healthy.

    Returns:
        JSON with status message
    """
    return {'message': 'Healthy', 'service': 'NoteEase API', 'version': '1.0.0'}


# ============================================================
# Notes Endpoints
# ============================================================

@app.get(
    '/notes',
    response_model=NoteListResponse,
    tags=['notes'],
    summary='List Notes',
    description='Retrieve a paginated list of notes with optional filtering by text search, tags, or pinned status.',
    operation_id='list_notes'
)
def list_notes(
    query: Optional[str] = Query(None, description='Search text to match in title or content'),
    tag_ids: Optional[List[int]] = Query(None, description='Filter notes by tag IDs'),
    pinned_only: Optional[bool] = Query(None, description='Return only pinned notes'),
    page: int = Query(1, ge=1, description='Page number'),
    page_size: int = Query(20, ge=1, le=100, description='Number of notes per page'),
    db: Session = Depends(get_db)
):
    """
    List all notes with optional filtering.

    - **query**: Search text to match in title or content (case-insensitive)
    - **tag_ids**: Filter by one or more tag IDs
    - **pinned_only**: When true, only return pinned notes
    - **page**: Page number (1-indexed)
    - **page_size**: Number of notes per page (max 100)

    Returns a paginated list of notes sorted with pinned notes first,
    then by last updated time (most recent first).
    """
    skip = (page - 1) * page_size
    notes, total = crud.get_notes(
        db,
        query=query,
        tag_ids=tag_ids,
        pinned_only=pinned_only,
        skip=skip,
        limit=page_size
    )
    return NoteListResponse(
        notes=notes,
        total=total,
        page=page,
        page_size=page_size
    )


@app.post(
    '/notes',
    response_model=NoteResponse,
    status_code=201,
    tags=['notes'],
    summary='Create Note',
    description='Create a new note with optional title, content, and tags.',
    operation_id='create_note'
)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    """
    Create a new note.

    - **title**: Note title (default: 'Untitled')
    - **content**: Note content body
    - **is_pinned**: Whether the note should be pinned (default: false)
    - **tag_ids**: List of existing tag IDs to associate

    Returns the created note with all fields populated.
    """
    return crud.create_note(db, note)


@app.get(
    '/notes/{note_id}',
    response_model=NoteResponse,
    tags=['notes'],
    summary='Get Note',
    description='Retrieve a single note by its ID.',
    operation_id='get_note'
)
def get_note(note_id: int, db: Session = Depends(get_db)):
    """
    Get a note by ID.

    - **note_id**: The unique identifier of the note

    Returns the note if found, 404 if not found.
    """
    db_note = crud.get_note(db, note_id)
    if not db_note:
        raise HTTPException(status_code=404, detail=f'Note {note_id} not found')
    return db_note


@app.put(
    '/notes/{note_id}',
    response_model=NoteResponse,
    tags=['notes'],
    summary='Update Note',
    description='Update an existing note. Only provided fields will be updated.',
    operation_id='update_note'
)
def update_note(note_id: int, note: NoteUpdate, db: Session = Depends(get_db)):
    """
    Update a note by ID.

    - **note_id**: The unique identifier of the note
    - **title**: New title (optional)
    - **content**: New content (optional)
    - **is_pinned**: New pinned status (optional)
    - **tag_ids**: New list of tag IDs (optional, replaces existing tags)

    Returns the updated note, 404 if not found.
    """
    db_note = crud.update_note(db, note_id, note)
    if not db_note:
        raise HTTPException(status_code=404, detail=f'Note {note_id} not found')
    return db_note


@app.delete(
    '/notes/{note_id}',
    tags=['notes'],
    summary='Delete Note',
    description='Permanently delete a note by its ID.',
    operation_id='delete_note'
)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """
    Delete a note by ID.

    - **note_id**: The unique identifier of the note

    Returns success message, 404 if not found.
    """
    db_note = crud.delete_note(db, note_id)
    if not db_note:
        raise HTTPException(status_code=404, detail=f'Note {note_id} not found')
    return {'message': f'Note {note_id} deleted successfully'}


@app.patch(
    '/notes/{note_id}/pin',
    response_model=NoteResponse,
    tags=['notes'],
    summary='Toggle Pin Note',
    description='Toggle the pinned status of a note.',
    operation_id='toggle_pin_note'
)
def toggle_pin_note(note_id: int, db: Session = Depends(get_db)):
    """
    Toggle pin/unpin status of a note.

    - **note_id**: The unique identifier of the note

    Returns the updated note with toggled pin status, 404 if not found.
    """
    db_note = crud.toggle_pin_note(db, note_id)
    if not db_note:
        raise HTTPException(status_code=404, detail=f'Note {note_id} not found')
    return db_note


# ============================================================
# Tags Endpoints
# ============================================================

@app.get(
    '/tags',
    response_model=List[TagResponse],
    tags=['tags'],
    summary='List Tags',
    description='Retrieve all available tags.',
    operation_id='list_tags'
)
def list_tags(db: Session = Depends(get_db)):
    """
    Get all tags.

    Returns a list of all tags ordered by creation time.
    """
    return crud.get_tags(db)


@app.post(
    '/tags',
    response_model=TagResponse,
    status_code=201,
    tags=['tags'],
    summary='Create Tag',
    description='Create a new tag. If a tag with the same name exists, returns that tag.',
    operation_id='create_tag'
)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """
    Create a new tag.

    - **name**: Name of the tag (must be unique)

    Returns the created tag or the existing tag with the same name.
    """
    return crud.create_tag(db, tag)


@app.delete(
    '/tags/{tag_id}',
    tags=['tags'],
    summary='Delete Tag',
    description='Delete a tag by its ID. The tag will be removed from all associated notes.',
    operation_id='delete_tag'
)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    Delete a tag by ID.

    - **tag_id**: The unique identifier of the tag

    The tag will be disassociated from all notes before deletion.
    Returns success message, 404 if not found.
    """
    db_tag = crud.delete_tag(db, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail=f'Tag {tag_id} not found')
    return {'message': f'Tag {tag_id} deleted successfully'}
