"""
Logging configuration for the analysis system.

Provides centralized logging configuration with security filters
to prevent sensitive data leakage in logs.
"""

import logging
import re
from typing import List, Optional


class SensitiveDataFilter(logging.Filter):
    """
    Filter to redact sensitive information from log messages.
    
    This filter prevents accidental logging of sensitive data like:
    - Politician names (replaced with ID hashes)
    - Database credentials
    - API keys and tokens
    - Trade amounts and specific financial data
    """
    
    def __init__(self, patterns: Optional[List[str]] = None):
        """
        Initialize the filter with patterns to redact.
        
        Args:
            patterns: Optional list of regex patterns to redact
        """
        super().__init__()
        
        # Default patterns for sensitive data
        self.patterns = patterns or [
            # Database credentials
            r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            r'postgres://[^@]+@',
            
            # API keys and tokens
            r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            
            # Financial amounts (redact specific values)
            r'\$[\d,]+\.?\d*',
            r'amount["\']?\s*[:=]\s*[\d,]+\.?\d*',
            
            # Email addresses
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            
            # Social Security Numbers
            r'\b\d{3}-\d{2}-\d{4}\b',
            
            # Credit card numbers
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]
        
        # Names to anonymize (loaded from config or database)
        self.sensitive_names: set = set()
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records to redact sensitive information.
        
        Args:
            record: The log record to filter
            
        Returns:
            True (always pass the record, just redact content)
        """
        # Redact message
        if hasattr(record, 'msg'):
            record.msg = self._redact_message(str(record.msg))
        
        # Redact args if present
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._redact_message(str(arg)) if isinstance(arg, (str, int, float)) 
                else arg for arg in record.args
            )
        
        return True
    
    def _redact_message(self, message: str) -> str:
        """
        Redact sensitive information from a message.
        
        Args:
            message: The message to redact
            
        Returns:
            Redacted message
        """
        redacted = message
        
        # Apply regex patterns
        for pattern in self.compiled_patterns:
            redacted = pattern.sub('[REDACTED]', redacted)
        
        # Redact known sensitive names
        for name in self.sensitive_names:
            if name in redacted:
                # Replace with hash for consistency
                name_hash = str(hash(name))[:8]
                redacted = redacted.replace(name, f'[ID_{name_hash}]')
        
        return redacted
    
    def add_sensitive_name(self, name: str):
        """Add a name to the list of sensitive names to redact."""
        self.sensitive_names.add(name)
    
    def add_sensitive_names(self, names: List[str]):
        """Add multiple names to the list of sensitive names to redact."""
        self.sensitive_names.update(names)


def configure_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_sensitive_filter: bool = True,
    sensitive_names: Optional[List[str]] = None
):
    """
    Configure logging for the application with security filters.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        enable_sensitive_filter: Whether to enable sensitive data filtering
        sensitive_names: Optional list of sensitive names to redact
    
    Example:
        >>> configure_logging(
        ...     level="INFO",
        ...     log_file="app.log",
        ...     sensitive_names=["Nancy Pelosi", "Mitch McConnell"]
        ... )
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Add sensitive data filter
    if enable_sensitive_filter:
        sensitive_filter = SensitiveDataFilter()
        
        if sensitive_names:
            sensitive_filter.add_sensitive_names(sensitive_names)
        
        console_handler.addFilter(sensitive_filter)
        if log_file:
            file_handler.addFilter(sensitive_filter)
    
    root_logger.addHandler(console_handler)
    
    # Suppress noisy libraries
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logging.info("Logging configured with security filters")


# Development vs Production configurations
def configure_development_logging():
    """Configure logging for development environment."""
    configure_logging(
        level="DEBUG",
        log_file="debug.log",
        enable_sensitive_filter=True  # Still filter in dev
    )


def configure_production_logging():
    """Configure logging for production environment."""
    configure_logging(
        level="WARNING",  # Less verbose in production
        log_file="production.log",
        enable_sensitive_filter=True
    )


# Example usage
if __name__ == "__main__":
    # Test the sensitive data filter
    configure_logging(level="DEBUG")
    
    logger = logging.getLogger(__name__)
    
    # These should be redacted
    logger.info("Database password: supersecret123")
    logger.info("API key: sk-1234567890abcdef")
    logger.info("Trade amount: $50000")
    logger.info("Email: john.doe@example.com")
    
    # Add politician names to redact
    filter = SensitiveDataFilter()
    filter.add_sensitive_names(["Nancy Pelosi", "Mitch McConnell"])
    
    logger.info("Nancy Pelosi made a trade")
    logger.info("Analyzing Mitch McConnell's portfolio")