"""Database Configuration"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging
from app.config import settings
from app.logging_config import log_with_context

# Database logger
db_logger = logging.getLogger("app.database")

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    future=True,
)

# Add database event listeners for logging
@event.listens_for(Engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log database connection"""
    log_with_context(
        db_logger,
        logging.INFO,
        "DB_CONNECTION_SUCCESS",
        database=settings.database_url.split("/")[-1].split("?")[0]
    )

@event.listens_for(Engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection pool checkout"""
    pass

@event.listens_for(Engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection pool checkin"""
    pass

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            log_with_context(
                db_logger,
                logging.ERROR,
                "DB_QUERY_FAILED",
                error_message=str(e),
                exc_info=True
            )
            raise
        finally:
            await session.close()
