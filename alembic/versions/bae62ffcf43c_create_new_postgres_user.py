"""create_new_postgres_user

Revision ID: bae62ffcf43c
Revises: ceb61c324258
Create Date: 2025-04-22 08:14:19.402833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os


# revision identifiers, used by Alembic.
revision: str = 'bae62ffcf43c'
down_revision: Union[str, None] = 'ceb61c324258'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Get database name from environment variable or use default
    database_name = os.environ.get("PG_DATABASE", "postgres")
    
    # Create a new user with password
    # Using a placeholder password - in production, use a secure method to generate/store passwords
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'rdsuser') THEN
            CREATE USER rdsuser;
        END IF;
    END
    $$;
    """)
    
    # Grant permissions to the user
    op.execute(f"""
    GRANT rds_iam TO rdsuser;
    GRANT ALL PRIVILEGES on ALL TABLES IN SCHEMA public TO rdsuser;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Get database name from environment variable or use default
    database_name = os.environ.get("PG_DATABASE", "postgres")
    
    # Revoke permissions
    op.execute(f"""
    REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM rdsuser;
    """)
    
    # Drop the user
    op.execute("""
    DROP USER IF EXISTS rdsuser;
    """)
