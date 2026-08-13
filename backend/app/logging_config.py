"""Logging Configuration for WhatsApp SaaS Platform"""
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Get log directory from environment or use default
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_data["context"] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add standard record fields
        if hasattr(record, 'pathname'):
            log_data["file"] = record.pathname
        if hasattr(record, 'lineno'):
            log_data["line"] = record.lineno
        if hasattr(record, 'funcName'):
            log_data["function"] = record.funcName
        
        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Custom text formatter for readable logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().isoformat() + "Z"
        level = record.levelname
        logger = record.name
        message = record.getMessage()
        
        # Add context if available
        context_str = ""
        if hasattr(record, 'context'):
            context_str = " " + " ".join([f"{k}={v}" for k, v in record.context.items()])
        
        return f"{timestamp} {level} {logger} {message}{context_str}"


def setup_logging(log_level: str = "WARNING"):
    """Setup logging configuration for the application"""
    
    # Get log level from environment
    level = getattr(logging, os.getenv("LOG_LEVEL", log_level).upper(), logging.WARNING)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Common formatter
    json_formatter = JSONFormatter()
    text_formatter = TextFormatter()
    
    # 1. App log (general application logs)
    app_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    app_handler.setLevel(logging.WARNING)
    app_handler.setFormatter(json_formatter)
    root_logger.addHandler(app_handler)
    
    # 2. Error log (errors only)
    error_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "error.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    # 3. Security log (security and audit)
    security_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "security.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(json_formatter)
    security_logger = logging.getLogger("security")
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False
    
    # 4. Performance log
    performance_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "performance.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    performance_handler.setLevel(logging.WARNING)
    performance_handler.setFormatter(json_formatter)
    performance_logger = logging.getLogger("performance")
    performance_logger.addHandler(performance_handler)
    performance_logger.setLevel(logging.WARNING)
    performance_logger.propagate = False
    
    # 5. WhatsApp log
    whatsapp_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "whatsapp.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    whatsapp_handler.setLevel(logging.WARNING)
    whatsapp_handler.setFormatter(json_formatter)
    whatsapp_logger = logging.getLogger("whatsapp")
    whatsapp_logger.addHandler(whatsapp_handler)
    whatsapp_logger.setLevel(logging.WARNING)
    whatsapp_logger.propagate = False
    
    # 6. Bot log
    bot_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "bot.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    bot_handler.setLevel(logging.WARNING)
    bot_handler.setFormatter(json_formatter)
    bot_logger = logging.getLogger("bot")
    bot_logger.addHandler(bot_handler)
    bot_logger.setLevel(logging.WARNING)
    bot_logger.propagate = False
    
    # Console handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(text_formatter)
    root_logger.addHandler(console_handler)
    
    # Module-specific loggers configuration
    configure_module_loggers(level)
    
    return root_logger


def configure_module_loggers(level: int):
    """Configure log levels for specific modules"""
    
    # Auth module
    auth_logger = logging.getLogger("app.auth")
    auth_logger.setLevel(logging.INFO)
    
    # WhatsApp module
    whatsapp_logger = logging.getLogger("app.whatsapp")
    whatsapp_logger.setLevel(logging.INFO)
    
    # Bot module
    bot_logger = logging.getLogger("app.bot")
    bot_logger.setLevel(logging.INFO)
    
    # ML module
    ml_logger = logging.getLogger("app.ml")
    ml_logger.setLevel(logging.INFO)
    
    # Database module
    db_logger = logging.getLogger("app.database")
    db_logger.setLevel(logging.WARNING)
    
    # Cache module
    cache_logger = logging.getLogger("app.cache")
    cache_logger.setLevel(logging.WARNING)
    
    # Jobs module
    jobs_logger = logging.getLogger("app.jobs")
    jobs_logger.setLevel(logging.INFO)
    
    # Audit module
    audit_logger = logging.getLogger("app.audit")
    audit_logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    """Log a message with additional context"""
    extra = {'context': context} if context else {}
    logger.log(level, message, extra=extra)


# Convenience functions for specific log types
def log_security(logger: logging.Logger, level: int, message: str, **context):
    """Log security event"""
    security_logger = logging.getLogger("security")
    log_with_context(security_logger, level, message, **context)


def log_performance(logger: logging.Logger, level: int, message: str, **context):
    """Log performance metric"""
    performance_logger = logging.getLogger("performance")
    log_with_context(performance_logger, level, message, **context)


def log_whatsapp(logger: logging.Logger, level: int, message: str, **context):
    """Log WhatsApp event"""
    whatsapp_logger = logging.getLogger("whatsapp")
    log_with_context(whatsapp_logger, level, message, **context)


def log_bot(logger: logging.Logger, level: int, message: str, **context):
    """Log bot event"""
    bot_logger = logging.getLogger("bot")
    log_with_context(bot_logger, level, message, **context)
