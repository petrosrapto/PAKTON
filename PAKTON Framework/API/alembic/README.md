# Alembic Database Migration Guide

This guide explains how to use Alembic for database schema migrations in the PAKTON API.

## What is Alembic?

Alembic is a database migration tool for SQLAlchemy. It allows you to:
- Track database schema changes over time
- Apply schema changes in a controlled, versioned manner
- Rollback changes if needed
- Maintain consistency across development, staging, and production environments

## Directory Structure

```
alembic/
├── env.py              # Migration environment configuration
├── script.py.mako      # Template for generating new migrations
└── versions/           # Migration scripts
    └── 001_initial.py  # First migration (creates users and conversations tables)
```

## Configuration Files

### `alembic.ini` (in API root directory)
Main configuration file containing:
- Database connection URL
- Migration scripts location
- Logging configuration

### `env.py`
Python environment setup that:
- Imports your SQLAlchemy models
- Configures the migration context
- Handles online/offline migration modes

### `script.py.mako`
Template used when generating new migration files

## How Alembic Works

### 1. **Tracking Schema State**

Alembic maintains a special table in your database called `alembic_version` that tracks which migrations have been applied.

```sql
SELECT * FROM alembic_version;
-- Returns the current migration revision ID
```

### 2. **Migration Chain**

Migrations are linked in a chain:
```
None -> 001_initial -> 002_next_migration -> 003_another_migration
```

Each migration knows:
- Its own revision ID
- The previous revision it builds upon
- How to upgrade (apply changes)
- How to downgrade (revert changes)

### 3. **Auto-generation**

Alembic can detect differences between:
- Your SQLAlchemy models (Python code)
- Your actual database schema

And generate migration scripts automatically!

## Basic Commands

### Check Current Version

```bash
cd "/Users/petrosrapto/Desktop/PAKTON/PAKTON/PAKTON Framework/API"
alembic current
```

**Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
001_initial (head)
```

### View Migration History

```bash
alembic history --verbose
```

**Output:**
```
001_initial (head)
    Initial migration - create users and conversations tables
    Path: /path/to/alembic/versions/001_initial.py
    
<base> -> 001_initial (head), Initial migration - create users and conversations tables
```

### Apply All Pending Migrations (Upgrade)

```bash
alembic upgrade head
```

**What happens:**
1. Alembic checks current version in `alembic_version` table
2. Finds all migrations between current and `head` (latest)
3. Runs each migration's `upgrade()` function in order
4. Updates `alembic_version` table

**Output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial, Initial migration
```

### Rollback Last Migration (Downgrade)

```bash
alembic downgrade -1
```

Rolls back one migration by running its `downgrade()` function.

### Rollback to Specific Version

```bash
alembic downgrade 001_initial
```

### Rollback All Migrations

```bash
alembic downgrade base
```

## Creating New Migrations

### Method 1: Auto-generate (Recommended)

Alembic detects changes between models and database:

```bash
# 1. Make changes to your models (e.g., add new field to User model)
# Edit database/models/user.py

# 2. Generate migration
alembic revision --autogenerate -m "Add phone_number to User model"
```

**What happens:**
1. Alembic compares your SQLAlchemy models with the actual database
2. Detects differences (new columns, tables, indexes, etc.)
3. Generates a new migration file in `alembic/versions/`
4. The file contains `upgrade()` and `downgrade()` functions

**Generated file example:**
```python
# alembic/versions/002_add_phone_number.py

def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'phone_number')
```

### Method 2: Empty Migration (Manual)

For complex changes or data migrations:

```bash
alembic revision -m "Migrate user data format"
```

Then manually write the `upgrade()` and `downgrade()` functions.

### Method 3: Using the Helper Script

We've provided a helper script:

```bash
./migrate.sh create
# Enter description when prompted
```

## Migration Workflow

### Development Environment

```bash
# 1. Pull latest code
git pull

# 2. Check if there are new migrations
alembic history

# 3. Apply migrations
alembic upgrade head

# 4. Make model changes
# Edit files in database/models/

# 5. Generate migration
alembic revision --autogenerate -m "Description of changes"

# 6. Review the generated migration file
# Check alembic/versions/00X_*.py

# 7. Test the migration
alembic upgrade head

# 8. Test rollback
alembic downgrade -1

# 9. Re-apply
alembic upgrade head

# 10. Commit migration file
git add alembic/versions/00X_*.py
git commit -m "Add migration: description"
```

### Production/Docker Environment

```bash
# 1. Rebuild containers with new code
docker-compose down
docker-compose up -d --build

# 2. Run migrations inside the container
docker exec -it multiagentframework_service alembic upgrade head

# Or use the helper script
docker exec -it multiagentframework_service ./migrate.sh upgrade
```

## Common Operations

### Add a New Table

1. Create new model in `database/models/new_model.py`:
```python
from sqlalchemy import Column, String, Integer
from ..config import Base

class NewModel(Base):
    __tablename__ = "new_table"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
```

2. Export in `database/models/__init__.py`:
```python
from .new_model import NewModel
__all__ = [..., "NewModel"]
```

3. Generate migration:
```bash
alembic revision --autogenerate -m "Add new_table"
```

4. Apply migration:
```bash
alembic upgrade head
```

### Add a Column to Existing Table

1. Edit the model (e.g., `database/models/user.py`):
```python
class User(Base):
    # ... existing columns ...
    new_field = Column(String(100), nullable=True)  # Add this
```

2. Generate migration:
```bash
alembic revision --autogenerate -m "Add new_field to users"
```

3. Apply:
```bash
alembic upgrade head
```

### Rename a Column

**Important:** Auto-generate will see this as DROP + ADD. Manual migration needed:

```bash
alembic revision -m "Rename user email to email_address"
```

Edit the generated file:
```python
def upgrade() -> None:
    op.alter_column('users', 'email', new_column_name='email_address')

def downgrade() -> None:
    op.alter_column('users', 'email_address', new_column_name='email')
```

### Data Migration

For migrating data (not just schema):

```bash
alembic revision -m "Migrate old data format"
```

Edit migration:
```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Get database connection
    connection = op.get_bind()
    
    # Update data
    connection.execute(
        sa.text("UPDATE users SET status = 'active' WHERE status IS NULL")
    )

def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE users SET status = NULL WHERE status = 'active'")
    )
```

## Best Practices

### ✅ DO

1. **Always review auto-generated migrations** before applying
2. **Test migrations locally** before deploying
3. **Test rollback** (downgrade) to ensure it works
4. **Use descriptive migration names** (e.g., "add_user_preferences_table")
5. **Keep migrations small and focused** (one logical change per migration)
6. **Commit migrations to version control** immediately
7. **Make columns nullable first** when adding to existing tables
8. **Use transactions** (migrations are transactional by default)

### ❌ DON'T

1. **Don't edit applied migrations** (create a new one instead)
2. **Don't delete migrations** that have been applied in production
3. **Don't assume auto-generate is perfect** (always review)
4. **Don't mix schema and data changes** in complex ways
5. **Don't skip testing rollback** functionality
6. **Don't commit untested migrations**

## Troubleshooting

### "Can't locate revision identified by '...'"

**Problem:** Migration file is missing or revision IDs are out of sync.

**Solution:**
```bash
# Check what revision the database thinks it's at
alembic current

# Check available migrations
alembic history

# If database is ahead, you might need to:
alembic stamp head  # Force mark database as current
```

### "Target database is not up to date"

**Problem:** Database has migrations applied that aren't in your code.

**Solution:**
```bash
# Pull latest code
git pull

# Check history
alembic history

# Apply missing migrations
alembic upgrade head
```

### Migration fails with error

**Solution:**
```bash
# Check what went wrong
alembic current

# If partial migration, rollback to last good state
alembic downgrade <last_good_revision>

# Fix the migration file
# Re-apply
alembic upgrade head
```

### "Table already exists"

**Problem:** Migration tries to create a table that exists.

**Solution:**
```bash
# Option 1: Mark the migration as applied without running it
alembic stamp head

# Option 2: Drop the table (⚠️ DANGER - data loss!)
# Option 3: Edit migration to check if table exists first
```

### Reset everything (⚠️ Development only!)

```bash
# 1. Drop all tables
alembic downgrade base

# 2. Re-apply all migrations
alembic upgrade head

# Or, nuclear option:
# Drop database and recreate
docker-compose down -v
docker-compose up -d
alembic upgrade head
```

## Environment Variables

Alembic uses these environment variables:

```bash
# Database connection
DATABASE_URL=postgresql://user:password@host:port/database
```

Set in:
- `.env` file (local development)
- `docker-compose.yml` (Docker)
- Environment (production)

## Integration with Helper Script

We provide `migrate.sh` for common operations:

```bash
# Initialize database (first time)
./migrate.sh init

# Apply pending migrations
./migrate.sh upgrade

# Rollback last migration
./migrate.sh downgrade

# Check current version
./migrate.sh current

# View history
./migrate.sh history

# Create new migration
./migrate.sh create
```

## Advanced: Branching and Merging

When multiple developers create migrations:

```bash
# Developer A creates migration: 003_add_feature_a
# Developer B creates migration: 003_add_feature_b (same number!)

# After merging branches, create merge migration:
alembic merge -m "Merge feature branches" 003_add_feature_a 003_add_feature_b

# This creates a new migration that depends on both
```

## Offline Migrations

For generating SQL without database connection:

```bash
alembic upgrade head --sql > migration.sql
```

Then run `migration.sql` manually on the database.

## Summary

**Key Concepts:**
- Migrations are version-controlled schema changes
- Each migration has upgrade (apply) and downgrade (rollback) functions
- Alembic tracks which migrations are applied
- Always test migrations before production deployment

**Common Commands:**
```bash
alembic current                          # Check version
alembic history                          # View all migrations
alembic upgrade head                     # Apply all pending
alembic downgrade -1                     # Rollback one
alembic revision --autogenerate -m "msg" # Generate migration
```

**Workflow:**
1. Change models → 2. Generate migration → 3. Review → 4. Test → 5. Apply → 6. Commit

For more information: https://alembic.sqlalchemy.org/
