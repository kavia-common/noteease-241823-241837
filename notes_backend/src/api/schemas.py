"""
Pydantic schemas for request and response validation.
Defines the data shapes for the NoteEase API.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base schema for Tag."""

    name: str = Field(..., description='The name of the tag', min_length=1, max_length=100)


class TagCreate(TagBase):
    """Schema for creating a new Tag."""
    pass


class TagResponse(TagBase):
    """Schema for returning a Tag in responses."""

    id: int = Field(..., description='Unique identifier of the tag')
    created_at: datetime = Field(..., description='Timestamp when the tag was created')

    model_config = {'from_attributes': True}


class NoteBase(BaseModel):
    """Base schema for Note."""

    title: str = Field(default='Untitled', description='Title of the note', max_length=255)
    content: Optional[str] = Field(default='', description='Content of the note')
    is_pinned: bool = Field(default=False, description='Whether the note is pinned')


class NoteCreate(NoteBase):
    """Schema for creating a new Note."""

    tag_ids: Optional[List[int]] = Field(
        default=[],
        description='List of tag IDs to associate with this note'
    )


class NoteUpdate(BaseModel):
    """Schema for updating an existing Note. All fields are optional."""

    title: Optional[str] = Field(None, description='Title of the note', max_length=255)
    content: Optional[str] = Field(None, description='Content of the note')
    is_pinned: Optional[bool] = Field(None, description='Whether the note is pinned')
    tag_ids: Optional[List[int]] = Field(None, description='List of tag IDs to associate')


class NoteResponse(NoteBase):
    """Schema for returning a Note in responses."""

    id: int = Field(..., description='Unique identifier of the note')
    tags: List[TagResponse] = Field(default=[], description='Tags associated with this note')
    created_at: datetime = Field(..., description='Timestamp when the note was created')
    updated_at: datetime = Field(..., description='Timestamp when the note was last updated')

    model_config = {'from_attributes': True}


class NoteListResponse(BaseModel):
    """Schema for returning a paginated list of notes."""

    notes: List[NoteResponse] = Field(..., description='List of notes')
    total: int = Field(..., description='Total number of notes matching the query')
    page: int = Field(..., description='Current page number')
    page_size: int = Field(..., description='Number of notes per page')


class SearchQuery(BaseModel):
    """Schema for note search parameters."""

    query: Optional[str] = Field(None, description='Text to search in title and content')
    tag_ids: Optional[List[int]] = Field(None, description='Filter by tag IDs')
    pinned_only: Optional[bool] = Field(None, description='Filter pinned notes only')
    page: int = Field(default=1, ge=1, description='Page number')
    page_size: int = Field(default=20, ge=1, le=100, description='Notes per page')
