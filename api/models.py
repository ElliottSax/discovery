"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class Trade(BaseModel):
    """Trade data model"""
    politician_name: str
    chamber: str
    state: Optional[str] = None
    party: Optional[str] = None
    disclosure_date: datetime
    transaction_date: datetime
    ticker: str
    asset_name: str
    transaction_type: str
    amount_range: str
    amount_min: float
    amount_max: float
    price_at_transaction: Optional[float] = None
    current_price: Optional[float] = None
    return_pct: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    
class Politician(BaseModel):
    """Politician model"""
    name: str
    chamber: str
    state: str
    party: str
    trade_count: int = 0
    last_trade_date: Optional[datetime] = None
    total_volume: Optional[float] = None
    performance: Optional[Dict] = None
    
class Analysis(BaseModel):
    """Analysis result model"""
    analysis_type: str
    timestamp: datetime
    data: Dict
    confidence: float = Field(ge=0, le=1)
    description: Optional[str] = None
    
class Alert(BaseModel):
    """Alert model"""
    id: int
    alert_type: str
    title: str
    message: str
    severity: str = Field(pattern="^(info|warning|critical)$")
    timestamp: datetime
    metadata: Optional[Dict] = None
    
class Pattern(BaseModel):
    """Trading pattern model"""
    pattern_name: str
    description: str
    politicians_involved: List[str]
    stocks_involved: List[str]
    time_period: str
    significance: str = Field(pattern="^(low|medium|high)$")
    confidence: float = Field(ge=0, le=1)
    
class Performance(BaseModel):
    """Performance metrics model"""
    politician_name: Optional[str] = None
    ticker: Optional[str] = None
    period: str
    total_return: float
    annualized_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    win_rate: Optional[float] = None
    average_holding_period: Optional[int] = None
    benchmark_comparison: Optional[Dict] = None
    
class MarketData(BaseModel):
    """Market data model"""
    ticker: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    timestamp: datetime
    
class Subscription(BaseModel):
    """Alert subscription model"""
    user_id: str
    email: Optional[str] = None
    webhook_url: Optional[str] = None
    alert_types: List[str]
    frequency: str = Field(pattern="^(realtime|daily|weekly)$", default="daily")
    active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
class PipelineStatus(BaseModel):
    """Pipeline status model"""
    status: str = Field(pattern="^(running|completed|failed|idle)$")
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    records_processed: int = 0
    errors: int = 0
    duration_seconds: Optional[float] = None
    stages: Optional[Dict] = None