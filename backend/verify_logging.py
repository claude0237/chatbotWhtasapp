"""Script to verify logging configuration is working correctly"""
import logging
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.logging_config import setup_logging, log_with_context, log_security, log_whatsapp, log_bot

# Setup logging
setup_logging()

# Test different log levels and categories
print("Testing logging configuration...")

# Test app logger
app_logger = logging.getLogger("app")
app_logger.info("Test INFO message from app logger")
app_logger.warning("Test WARNING message from app logger")
app_logger.error("Test ERROR message from app logger")

# Test security logger
security_logger = logging.getLogger("app.security")
log_security(
    security_logger,
    logging.INFO,
    "TEST_AUTH_LOGIN",
    user_id="test-user-123",
    email="test@example.com",
    company_id="test-company-456",
    role="ADMIN"
)

# Test WhatsApp logger
whatsapp_logger = logging.getLogger("app.whatsapp")
log_whatsapp(
    whatsapp_logger,
    logging.INFO,
    "TEST_WHATSAPP_SEND",
    company_id="test-company-456",
    phone_number="+1234567890",
    message_id="test-msg-789",
    status_code=200
)

# Test bot logger
bot_logger = logging.getLogger("app.bot")
log_bot(
    bot_logger,
    logging.INFO,
    "TEST_BOT_PROCESSING",
    company_id="test-company-456",
    phone_number="+1234567890",
    bot_type="NATIVE",
    reply_length=42
)

# Test database logger
db_logger = logging.getLogger("app.database")
log_with_context(
    db_logger,
    logging.INFO,
    "TEST_DB_CONNECTION",
    database="test_db"
)

# Test cache logger
cache_logger = logging.getLogger("app.cache")
log_with_context(
    cache_logger,
    logging.INFO,
    "TEST_REDIS_GET",
    key="test:key:123"
)

# Test jobs logger
jobs_logger = logging.getLogger("app.jobs")
log_with_context(
    jobs_logger,
    logging.INFO,
    "TEST_CELERY_JOB",
    phone_number="+1234567890",
    company_id="test-company-456"
)

# Test upload logger
upload_logger = logging.getLogger("app.upload")
log_with_context(
    upload_logger,
    logging.INFO,
    "TEST_FILE_UPLOAD",
    user_id="test-user-123",
    company_id="test-company-456",
    filename="test.jpg",
    file_size=1024
)

print("\nLogging test complete! Check the logs directory:")
print("- logs/app.log")
print("- logs/security.log")
print("- logs/whatsapp.log")
print("- logs/bot.log")
print("- logs/error.log")
print("- logs/performance.log")
