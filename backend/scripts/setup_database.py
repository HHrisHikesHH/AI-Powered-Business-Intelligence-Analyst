#!/usr/bin/env python3
"""
Database setup script for AI-Powered Business Intelligence Analyst.
Creates the database if it doesn't exist, then initializes tables and optionally seeds data.
"""
import asyncio
import asyncpg
import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.core.config import settings


async def database_exists(conn, db_name: str) -> bool:
    """Check if a database exists."""
    result = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", db_name
    )
    return result is not None


async def create_database():
    """Create the database if it doesn't exist."""
    # Connect to default postgres database to create our database
    admin_conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database="postgres"  # Connect to default database
    )
    
    try:
        # Check if database exists
        exists = await database_exists(admin_conn, settings.POSTGRES_DB)
        
        if exists:
            logger.info(f"Database '{settings.POSTGRES_DB}' already exists")
        else:
            logger.info(f"Creating database '{settings.POSTGRES_DB}'...")
            # Terminate existing connections to the database if any
            await admin_conn.execute(
                f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{settings.POSTGRES_DB}' AND pid <> pg_backend_pid()
                """
            )
            # Create the database
            await admin_conn.execute(
                f'CREATE DATABASE "{settings.POSTGRES_DB}"'
            )
            logger.info(f"Database '{settings.POSTGRES_DB}' created successfully")
    finally:
        await admin_conn.close()


def split_sql_statements(sql_content: str) -> list[str]:
    """
    Split SQL content into statements, handling dollar-quoted strings.
    This is a simple parser that handles most common cases.
    """
    statements = []
    current_statement = []
    in_dollar_quote = False
    dollar_tag = None
    i = 0
    
    while i < len(sql_content):
        char = sql_content[i]
        
        # Check for dollar-quoted strings (e.g., $$, $tag$, $tag$content$tag$)
        if not in_dollar_quote and char == '$':
            # Look ahead to find the dollar tag
            j = i + 1
            tag_start = i
            while j < len(sql_content) and sql_content[j] != '$':
                j += 1
            if j < len(sql_content):
                dollar_tag = sql_content[tag_start:j+1]
                in_dollar_quote = True
                current_statement.append(sql_content[i:j+1])
                i = j + 1
                continue
        
        # Check for end of dollar quote
        if in_dollar_quote and char == '$' and dollar_tag:
            # Check if this is the closing tag
            if sql_content[i:i+len(dollar_tag)] == dollar_tag:
                current_statement.append(dollar_tag)
                i += len(dollar_tag)
                in_dollar_quote = False
                dollar_tag = None
                continue
        
        current_statement.append(char)
        
        # If we're not in a dollar quote and we hit a semicolon, it's a statement separator
        if not in_dollar_quote and char == ';':
            statement = ''.join(current_statement).strip()
            if statement:
                statements.append(statement)
            current_statement = []
        
        i += 1
    
    # Add any remaining statement
    if current_statement:
        statement = ''.join(current_statement).strip()
        if statement:
            statements.append(statement)
    
    return statements


async def execute_sql_file(conn, sql_file_path: Path):
    """Execute a SQL file."""
    logger.info(f"Executing SQL file: {sql_file_path}")
    
    if not sql_file_path.exists():
        logger.error(f"SQL file not found: {sql_file_path}")
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")
    
    sql_content = sql_file_path.read_text()
    
    # Split into statements handling dollar-quoted strings
    statements = split_sql_statements(sql_content)
    
    for statement in statements:
        if statement:
            try:
                await conn.execute(statement)
            except Exception as e:
                # Some statements might fail (like IF NOT EXISTS when already exists)
                # Log but don't fail the whole process
                error_msg = str(e).lower()
                if any(phrase in error_msg for phrase in [
                    "already exists", "duplicate", "does not exist"
                ]):
                    logger.debug(f"Statement skipped: {statement[:50]}...")
                else:
                    logger.warning(f"Error executing statement: {e}")
                    logger.debug(f"Statement: {statement[:200]}...")


async def setup_database(seed: bool = False):
    """Main function to set up the database."""
    try:
        # Step 1: Create database if it doesn't exist
        await create_database()
        
        # Step 2: Connect to our database
        logger.info(f"Connecting to database '{settings.POSTGRES_DB}'...")
        conn = await asyncpg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        
        try:
            # Step 3: Run init.sql to create tables
            backend_dir = Path(__file__).parent.parent
            init_sql = backend_dir / "database" / "init.sql"
            await execute_sql_file(conn, init_sql)
            logger.info("Database schema initialized successfully")
            
            # Step 4: Optionally seed data
            if seed:
                seed_sql = backend_dir / "database" / "seed_data.sql"
                await execute_sql_file(conn, seed_sql)
                logger.info("Database seeded with sample data")
            
        finally:
            await conn.close()
        
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to set up database: {e}")
        raise


async def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up the database")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Also seed the database with sample data"
    )
    args = parser.parse_args()
    
    logger.info("Starting database setup...")
    logger.info(f"PostgreSQL Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"Database: {settings.POSTGRES_DB}")
    logger.info(f"User: {settings.POSTGRES_USER}")
    
    await setup_database(seed=args.seed)


if __name__ == "__main__":
    asyncio.run(main())

