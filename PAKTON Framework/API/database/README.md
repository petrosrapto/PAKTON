# Database Package

This package contains all database-related code for the PAKTON API, including models, repositories, and configuration.

## Structure

```
database/
├── __init__.py              # Package exports
├── config.py                # SQLAlchemy configuration and session management
├── models/                  # Database models (ORM)
│   ├── __init__.py
│   ├── user.py             # User model
│   └── conversation.py     # Conversation model
└── repositories/            # Data access layer
    ├── __init__.py
    ├── user_repository.py          # User CRUD operations
    └── conversation_repository.py  # Conversation CRUD operations
```

## Usage

### Importing

```python
# Import everything you need from the database package
from database import (
    # Configuration
    Base, engine, SessionLocal, get_db, get_db_session, init_db,
    # Models
    User, Conversation,
    # Repositories
    UserRepository, ConversationRepository
)
```

### Using in FastAPI Endpoints

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db, ConversationRepository

@app.get("/conversations")
async def get_conversations(db: Session = Depends(get_db)):
    conversations = ConversationRepository.get_by_user_email(db, "user@example.com")
    return conversations
```

### Using with Context Manager

```python
from database import get_db_session, User

with get_db_session() as db:
    users = db.query(User).all()
    # Session is automatically committed and closed
```

## Models

### User

Stores user information with email as primary key.

**Fields:**
- `email` (PK) - User's email address
- `created_at` - Timestamp
- `updated_at` - Timestamp
- `conversations` - Relationship to Conversation model

### Conversation

Tracks user conversations with thread IDs.

**Fields:**
- `thread_id` (PK) - Unique conversation identifier
- `user_email` (FK) - References User.email
- `title` - Optional conversation title
- `last_message` - Preview of last message
- `created_at` - Timestamp
- `updated_at` - Timestamp
- `user` - Relationship to User model

**Methods:**
- `to_dict()` - Convert to dictionary for API responses

## Repositories

### UserRepository

**Methods:**
- `get_or_create(db, email)` - Get existing user or create new
- `get_by_email(db, email)` - Get user by email

### ConversationRepository

**Methods:**
- `create(db, thread_id, user_email, title, last_message)` - Create conversation
- `get_by_thread_id(db, thread_id)` - Get specific conversation
- `get_by_user_email(db, user_email, limit, offset)` - Get user's conversations
- `update(db, thread_id, title, last_message)` - Update conversation
- `get_or_create(db, thread_id, user_email, title, last_message)` - Get or create
- `delete(db, thread_id)` - Delete conversation
- `count_by_user(db, user_email)` - Count user's conversations

## Configuration

The database URL is configured via environment variable:

```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

Default: `postgresql://archivist_user:archivist_password@localhost:5432/archivist_db`

## Database Initialization

```python
from database import init_db

# Create all tables (development only - use Alembic in production)
init_db()
```

## Best Practices

1. **Always use repositories** - Don't query models directly in endpoints
2. **Use dependency injection** - Use `Depends(get_db)` in FastAPI
3. **Handle transactions** - Repositories handle commit/rollback
4. **Type hints** - All functions have proper type annotations
5. **Error handling** - Repositories log errors and handle exceptions
