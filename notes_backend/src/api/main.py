from typing import Dict, List
from fastapi import FastAPI, HTTPException, Path, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# Configure FastAPI app with metadata and tags for OpenAPI
openapi_tags = [
    {
        "name": "Health",
        "description": "Service health and metadata endpoints."
    },
    {
        "name": "Notes",
        "description": "CRUD operations for managing notes."
    },
]

app = FastAPI(
    title="Notes Backend API",
    description="A simple Notes API providing CRUD operations for a notes application.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# CORS: Allow local Next.js frontend (port 3000) and any other origins if needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Pydantic Models (Schemas)
# ----------------------------

class NoteBase(BaseModel):
    """Base schema for note fields."""
    title: str = Field(..., description="The title of the note", min_length=1)
    content: str = Field(..., description="The content/body of the note", min_length=1)


class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    pass


class NoteUpdate(BaseModel):
    """Schema for updating an existing note (partial update not supported; use full replace)."""
    title: str = Field(..., description="The updated title of the note", min_length=1)
    content: str = Field(..., description="The updated content/body of the note", min_length=1)


class Note(NoteBase):
    """Schema representing a full note record."""
    id: str = Field(..., description="Unique identifier (UUID string) of the note")
    created_at: datetime = Field(..., description="Timestamp when the note was created")
    updated_at: datetime = Field(..., description="Timestamp when the note was last updated")


# ----------------------------
# In-memory storage (simple persistence placeholder)
# ----------------------------
# In a production app, replace with a database. This is intentionally simple for now.
NOTES_DB: Dict[str, Note] = {}


def _now() -> datetime:
    """Utility to get current UTC timestamp without timezone for simplicity."""
    return datetime.utcnow()


# ----------------------------
# Routes
# ----------------------------

@app.get("/", tags=["Health"], summary="Health Check", description="Simple health check endpoint.")
def health_check():
    """Return a simple health response to verify the service is up."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/notes",
    response_model=List[Note],
    tags=["Notes"],
    summary="List notes",
    description="Retrieve all notes in reverse chronological order (most recently updated first).",
)
def list_notes() -> List[Note]:
    """Return a list of all notes."""
    # Sort by updated_at desc for convenience in UI
    return sorted(NOTES_DB.values(), key=lambda n: n.updated_at, reverse=True)


# PUBLIC_INTERFACE
@app.post(
    "/notes",
    response_model=Note,
    status_code=status.HTTP_201_CREATED,
    tags=["Notes"],
    summary="Create note",
    description="Create a new note with a title and content.",
)
def create_note(payload: NoteCreate) -> Note:
    """Create a new note and return it."""
    note_id = str(uuid.uuid4())
    ts = _now()
    note = Note(id=note_id, title=payload.title, content=payload.content, created_at=ts, updated_at=ts)
    NOTES_DB[note_id] = note
    return note


# PUBLIC_INTERFACE
@app.get(
    "/notes/{note_id}",
    response_model=Note,
    tags=["Notes"],
    summary="Get note by id",
    description="Fetch a single note by its unique identifier.",
)
def get_note(
    note_id: str = Path(..., description="The UUID string of the note to retrieve")
) -> Note:
    """Return the note with the given id or 404 if not found."""
    note = NOTES_DB.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


# PUBLIC_INTERFACE
@app.put(
    "/notes/{note_id}",
    response_model=Note,
    tags=["Notes"],
    summary="Update note by id",
    description="Replace an existing note's title and content.",
)
def update_note(
    payload: NoteUpdate,
    note_id: str = Path(..., description="The UUID string of the note to update"),
) -> Note:
    """Update the title and content of an existing note, or 404 if not found."""
    existing = NOTES_DB.get(note_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")
    updated = Note(
        id=existing.id,
        title=payload.title,
        content=payload.content,
        created_at=existing.created_at,
        updated_at=_now(),
    )
    NOTES_DB[note_id] = updated
    return updated


# PUBLIC_INTERFACE
@app.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Notes"],
    summary="Delete note by id",
    description="Delete a note by its unique identifier.",
)
def delete_note(
    note_id: str = Path(..., description="The UUID string of the note to delete"),
) -> None:
    """Delete a note or return 404 if not found."""
    existing = NOTES_DB.get(note_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")
    del NOTES_DB[note_id]
    return None
