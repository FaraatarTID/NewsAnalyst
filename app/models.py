from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class IntelligenceCategory(str, Enum):
    """Categories of market intelligence."""
    INDUSTRY_NEWS = "industry_news"
    REGULATORY_CHANGE = "regulatory_change"
    COMPETITOR_ACTIVITY = "competitor_activity"
    MARKET_TREND = "market_trend"
    FUNDING_ANNOUNCEMENT = "funding_announcement"
    TECHNOLOGY_BREAKTHROUGH = "technology_breakthrough"
    PARTNERSHIP = "partnership"
    OTHER = "other"

class NewsArticle(BaseModel):
    """Represents a single news article."""
    title: str
    link: str
    published: str
    source: str = "Unknown"
    content: Optional[str] = None  # Full content if available
    snippet: Optional[str] = None  # Short excerpt

class Company(BaseModel):
    """Represents a company in the watchlist."""
    name: str
    sector: str = "Recycling/Waste Management"
    location: Optional[str] = None
    description: Optional[str] = None
    funding_stage: Optional[str] = None
    last_funding_amount: Optional[float] = None
    last_funding_date: Optional[datetime] = None
    website: Optional[str] = None
    key_people: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class MarketIntelligence(BaseModel):
    """Represents a market intelligence item."""
    title: str
    category: IntelligenceCategory
    summary: str
    impact_analysis: Optional[str] = None
    opportunities_risks: Optional[str] = None
    key_players: List[str] = Field(default_factory=list)
    geographic_region: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    importance_score: int = Field(5, ge=1, le=10)  # 1-10 scale
    source_link: str
    source_name: str
    published_date: str
    collected_at: datetime = Field(default_factory=datetime.now)

class AnalysisResult(BaseModel):
    """Represents the result of AI analysis."""
    title: str
    category: Optional[IntelligenceCategory] = None
    summary: str
    impact_analysis: Optional[str] = ""
    opportunities_risks: Optional[str] = ""
    key_players: Optional[str] = ""
    geographic_region: Optional[str] = ""
    importance_score: Optional[int] = 5
    importance: str = ""  # Legacy field for compatibility
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    original_link: str
    full_formatted_text: Optional[str] = None  # Complete formatted output from AI

class RegulatoryChange(BaseModel):
    """Represents a regulatory or policy change."""
    title: str
    country: str
    summary: str
    effective_date: Optional[datetime] = None
    compliance_deadline: Optional[datetime] = None
    impact_level: str = "Medium"  # Low, Medium, High, Critical
    source_link: str
    tags: List[str] = Field(default_factory=list)

class Stats(BaseModel):
    """Execution statistics."""
    total_articles: int = 0
    processed: int = 0
    failed: int = 0
    by_category: dict = Field(default_factory=dict)
    high_priority_count: int = 0  # Items with importance >= 7
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    errors: List[dict] = Field(default_factory=list)
