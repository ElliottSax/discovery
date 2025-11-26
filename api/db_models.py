"""
SQLAlchemy ORM models for database tables
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text,
    Boolean, ForeignKey, Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.database import Base


class Politician(Base):
    """Politician table"""
    __tablename__ = "politicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    chamber = Column(String(50), nullable=False)  # senate, house
    state = Column(String(2), nullable=False)
    party = Column(String(50))  # republican, democrat, independent
    district = Column(String(10))  # For house members

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    trades = relationship("Trade", back_populates="politician")

    # Indexes
    __table_args__ = (
        Index('idx_politician_chamber_state', 'chamber', 'state'),
        Index('idx_politician_party', 'party'),
    )


class Trade(Base):
    """Trade/transaction table"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey('politicians.id'), nullable=False)

    # Transaction details
    disclosure_date = Column(DateTime, nullable=False)
    transaction_date = Column(DateTime, nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    asset_name = Column(String(500))
    transaction_type = Column(String(20), nullable=False)  # purchase, sale, exchange

    # Amount information
    amount_range = Column(String(50))  # e.g., "$1,001 - $15,000"
    amount_min = Column(Float)
    amount_max = Column(Float)

    # Market data
    price_at_transaction = Column(Float)
    current_price = Column(Float)
    return_pct = Column(Float)

    # Classification
    sector = Column(String(100), index=True)
    industry = Column(String(200))

    # Additional data
    extra_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    politician = relationship("Politician", back_populates="trades")

    # Indexes
    __table_args__ = (
        Index('idx_trade_date_ticker', 'transaction_date', 'ticker'),
        Index('idx_trade_politician_date', 'politician_id', 'transaction_date'),
        Index('idx_trade_sector', 'sector'),
    )


class Stock(Base):
    """Stock/asset information"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(500))

    # Classification
    sector = Column(String(100), index=True)
    industry = Column(String(200))
    exchange = Column(String(50))

    # Current data
    current_price = Column(Float)
    market_cap = Column(Float)
    pe_ratio = Column(Float)
    volume = Column(Float)

    # Timestamps
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_stock_sector_industry', 'sector', 'industry'),
    )


class PriceHistory(Base):
    """Historical price data"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False)

    # OHLCV data
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(Float)

    # Adjusted prices
    adj_close = Column(Float)

    created_at = Column(DateTime, server_default=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uq_ticker_date'),
        Index('idx_price_ticker_date', 'ticker', 'date'),
    )


class Pattern(Base):
    """Detected trading patterns"""
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String(200), nullable=False)
    pattern_type = Column(String(100), nullable=False, index=True)  # cluster, timing, sector_rotation, etc.

    # Pattern details
    description = Column(Text)
    politicians_involved = Column(JSON)  # List of politician names
    stocks_involved = Column(JSON)  # List of tickers

    # Metrics
    confidence = Column(Float)
    significance = Column(String(20))  # low, medium, high

    # Time range
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Analysis metadata
    detection_method = Column(String(100))  # fourier, hmm, dtw, etc.
    analysis_data = Column(JSON)

    # Timestamps
    detected_at = Column(DateTime, server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_pattern_type_confidence', 'pattern_type', 'confidence'),
        Index('idx_pattern_dates', 'start_date', 'end_date'),
    )


class Alert(Base):
    """System alerts"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)

    # Severity
    severity = Column(String(20), nullable=False, index=True)  # info, warning, critical

    # Status
    status = Column(String(20), default='active')  # active, acknowledged, resolved
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)

    # Data
    extra_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # Indexes
    __table_args__ = (
        Index('idx_alert_type_severity', 'alert_type', 'severity'),
        Index('idx_alert_status_created', 'status', 'created_at'),
    )


class AnalysisRun(Base):
    """Analysis execution tracking"""
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(100), nullable=False, index=True)

    # Status
    status = Column(String(20), nullable=False)  # running, completed, failed

    # Timing
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    # Results
    records_processed = Column(Integer, default=0)
    patterns_detected = Column(Integer, default=0)
    errors = Column(Integer, default=0)

    # Data
    results = Column(JSON)
    error_message = Column(Text)
    config = Column(JSON)

    # MLFlow tracking
    mlflow_run_id = Column(String(100))
    mlflow_experiment_id = Column(String(100))

    # Indexes
    __table_args__ = (
        Index('idx_analysis_type_status', 'analysis_type', 'status'),
        Index('idx_analysis_started', 'started_at'),
    )


class User(Base):
    """User accounts for API access"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # API access
    api_key = Column(String(255), unique=True)
    rate_limit_tier = Column(String(20), default='standard')  # standard, premium, enterprise

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")


class Subscription(Base):
    """Alert subscriptions"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Notification settings
    email = Column(String(255))
    webhook_url = Column(String(500))

    # Alert preferences
    alert_types = Column(JSON)  # List of alert types to receive
    frequency = Column(String(20), default='daily')  # realtime, daily, weekly

    # Filters
    politicians_filter = Column(JSON)  # Optional list of politicians to watch
    stocks_filter = Column(JSON)  # Optional list of stocks to watch
    min_severity = Column(String(20), default='info')

    # Status
    active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    # Indexes
    __table_args__ = (
        Index('idx_subscription_user_active', 'user_id', 'active'),
    )
