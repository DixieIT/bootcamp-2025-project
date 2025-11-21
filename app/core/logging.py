import logging
import os
from app.services.db_service import log_to_db

class DatabaseHandler(logging.Handler):
    """Custom logging handler to write logs to SQLite database"""
    def emit(self, record):
        try:
            log_to_db(
                level=record.levelname,
                logger_name=record.name,
                message=self.format(record)
            )
        except Exception:
            # Don't let logging errors crash the app
            pass

def setup_logging():
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Create file handler (keep for backward compatibility)
    file_handler = logging.FileHandler("logs/app.log")
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    file_handler.setFormatter(logging.Formatter(fmt))

    # Create database handler (new!)
    db_handler = DatabaseHandler()
    db_handler.setFormatter(logging.Formatter(fmt))

    # Configure root logger with both handlers
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)  # Still write to file
    root.addHandler(db_handler)     # Also write to database