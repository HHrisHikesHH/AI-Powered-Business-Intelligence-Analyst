"""
Database Adapter Abstraction Layer.
Supports multiple database types (PostgreSQL, MySQL, SQLite, etc.)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, inspect
from loguru import logger
from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MSSQL = "mssql"
    ORACLE = "oracle"


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""
    
    def __init__(self, connection_string: str, **kwargs):
        self.connection_string = connection_string
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
    
    @abstractmethod
    def get_engine(self) -> AsyncEngine:
        """Create and return async database engine."""
        pass
    
    @abstractmethod
    def get_session_factory(self) -> async_sessionmaker:
        """Create and return async session factory."""
        pass
    
    @abstractmethod
    async def get_tables(self, session: AsyncSession, schema: str = "public") -> List[str]:
        """Get list of all tables in the database."""
        pass
    
    @abstractmethod
    async def get_columns(self, session: AsyncSession, table_name: str, schema: str = "public") -> List[Dict]:
        """Get columns for a table."""
        pass
    
    @abstractmethod
    async def get_relationships(self, session: AsyncSession, schema: str = "public") -> List[Dict]:
        """Get foreign key relationships."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test database connection."""
        pass
    
    @abstractmethod
    def get_database_type(self) -> DatabaseType:
        """Get the database type."""
        pass


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""
    
    def get_engine(self) -> AsyncEngine:
        """Create PostgreSQL async engine."""
        if self.engine is None:
            self.engine = create_async_engine(
                self.connection_string,
                echo=False,
                future=True,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
        return self.engine
    
    def get_session_factory(self) -> async_sessionmaker:
        """Create PostgreSQL async session factory."""
        if self.session_factory is None:
            engine = self.get_engine()
            self.session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self.session_factory
    
    async def get_tables(self, session: AsyncSession, schema: str = "public") -> List[str]:
        """Get list of all tables in PostgreSQL."""
        result = await session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """), {"schema": schema})
        
        rows = result.fetchall()
        return [row[0] for row in rows]
    
    async def get_columns(self, session: AsyncSession, table_name: str, schema: str = "public") -> List[Dict]:
        """Get columns for a PostgreSQL table."""
        result = await session.execute(text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table_name
            ORDER BY ordinal_position
        """), {"schema": schema, "table_name": table_name})
        
        rows = result.fetchall()
        return [
            {
                "name": row[0],
                "data_type": row[1],
                "is_nullable": row[2],
                "default": row[3]
            }
            for row in rows
        ]
    
    async def get_relationships(self, session: AsyncSession, schema: str = "public") -> List[Dict]:
        """Get foreign key relationships in PostgreSQL."""
        result = await session.execute(text("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = :schema
        """), {"schema": schema})
        
        rows = result.fetchall()
        return [
            {
                "table": row[0],
                "column": row[1],
                "foreign_table": row[2],
                "foreign_column": row[3]
            }
            for row in rows
        ]
    
    async def test_connection(self) -> bool:
        """Test PostgreSQL connection."""
        try:
            engine = self.get_engine()
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False
    
    def get_database_type(self) -> DatabaseType:
        """Get database type."""
        return DatabaseType.POSTGRESQL


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter."""
    
    def get_engine(self) -> AsyncEngine:
        """Create MySQL async engine."""
        if self.engine is None:
            self.engine = create_async_engine(
                self.connection_string,
                echo=False,
                future=True,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
        return self.engine
    
    def get_session_factory(self) -> async_sessionmaker:
        """Create MySQL async session factory."""
        if self.session_factory is None:
            engine = self.get_engine()
            self.session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self.session_factory
    
    async def get_tables(self, session: AsyncSession, schema: str = None) -> List[str]:
        """Get list of all tables in MySQL."""
        if schema is None:
            # MySQL uses database name instead of schema
            result = await session.execute(text("SHOW TABLES"))
        else:
            result = await session.execute(text(f"SHOW TABLES FROM `{schema}`"))
        
        rows = result.fetchall()
        # MySQL returns tuples, get first element
        return [row[0] for row in rows]
    
    async def get_columns(self, session: AsyncSession, table_name: str, schema: str = None) -> List[Dict]:
        """Get columns for a MySQL table."""
        if schema:
            query = text(f"DESCRIBE `{schema}`.`{table_name}`")
        else:
            query = text(f"DESCRIBE `{table_name}`")
        
        result = await session.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "name": row[0],
                "data_type": row[1],
                "is_nullable": "YES" if row[2] == "YES" else "NO",
                "default": row[4] if len(row) > 4 else None
            }
            for row in rows
        ]
    
    async def get_relationships(self, session: AsyncSession, schema: str = None) -> List[Dict]:
        """Get foreign key relationships in MySQL."""
        if schema:
            query = text("""
                SELECT
                    TABLE_NAME,
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = :schema
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            result = await session.execute(query, {"schema": schema})
        else:
            query = text("""
                SELECT
                    TABLE_NAME,
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            result = await session.execute(query)
        
        rows = result.fetchall()
        return [
            {
                "table": row[0],
                "column": row[1],
                "foreign_table": row[2],
                "foreign_column": row[3]
            }
            for row in rows
        ]
    
    async def test_connection(self) -> bool:
        """Test MySQL connection."""
        try:
            engine = self.get_engine()
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            return False
    
    def get_database_type(self) -> DatabaseType:
        """Get database type."""
        return DatabaseType.MYSQL


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter."""
    
    def get_engine(self) -> AsyncEngine:
        """Create SQLite async engine."""
        if self.engine is None:
            self.engine = create_async_engine(
                self.connection_string,
                echo=False,
                future=True,
                pool_pre_ping=True,
                connect_args={"check_same_thread": False} if "sqlite" in self.connection_string else {},
            )
        return self.engine
    
    def get_session_factory(self) -> async_sessionmaker:
        """Create SQLite async session factory."""
        if self.session_factory is None:
            engine = self.get_engine()
            self.session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self.session_factory
    
    async def get_tables(self, session: AsyncSession, schema: str = None) -> List[str]:
        """Get list of all tables in SQLite."""
        result = await session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """))
        
        rows = result.fetchall()
        return [row[0] for row in rows]
    
    async def get_columns(self, session: AsyncSession, table_name: str, schema: str = None) -> List[Dict]:
        """Get columns for a SQLite table."""
        result = await session.execute(text(f"PRAGMA table_info(`{table_name}`)"))
        rows = result.fetchall()
        
        return [
            {
                "name": row[1],
                "data_type": row[2],
                "is_nullable": "YES" if row[3] == 0 else "NO",
                "default": row[4]
            }
            for row in rows
        ]
    
    async def get_relationships(self, session: AsyncSession, schema: str = None) -> List[Dict]:
        """Get foreign key relationships in SQLite."""
        # SQLite stores FK info in sqlite_master, need to parse CREATE TABLE statements
        # For simplicity, we'll query pragma_foreign_key_list
        result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        
        relationships = []
        for table in tables:
            try:
                result = await session.execute(text(f"PRAGMA foreign_key_list(`{table}`)"))
                rows = result.fetchall()
                for row in rows:
                    relationships.append({
                        "table": table,
                        "column": row[3],  # from column
                        "foreign_table": row[2],  # to table
                        "foreign_column": row[4]  # to column
                    })
            except:
                continue
        
        return relationships
    
    async def test_connection(self) -> bool:
        """Test SQLite connection."""
        try:
            engine = self.get_engine()
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"SQLite connection test failed: {e}")
            return False
    
    def get_database_type(self) -> DatabaseType:
        """Get database type."""
        return DatabaseType.SQLITE


def create_database_adapter(
    db_type: str,
    connection_string: str,
    **kwargs
) -> DatabaseAdapter:
    """
    Factory function to create appropriate database adapter.
    
    Args:
        db_type: Database type (postgresql, mysql, sqlite, etc.)
        connection_string: Database connection string
        **kwargs: Additional adapter-specific parameters
    
    Returns:
        DatabaseAdapter instance
    """
    db_type_lower = db_type.lower()
    
    if db_type_lower in ["postgresql", "postgres"]:
        return PostgreSQLAdapter(connection_string, **kwargs)
    elif db_type_lower in ["mysql", "mariadb"]:
        # Ensure MySQL connection string uses aiomysql driver
        if not connection_string.startswith("mysql+aiomysql://"):
            connection_string = connection_string.replace("mysql://", "mysql+aiomysql://", 1)
        return MySQLAdapter(connection_string, **kwargs)
    elif db_type_lower == "sqlite":
        # Ensure SQLite connection string uses aiosqlite driver
        if not connection_string.startswith("sqlite+aiosqlite://"):
            connection_string = connection_string.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return SQLiteAdapter(connection_string, **kwargs)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

