from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum


class SoilType(str, Enum):
    LOAM = "loam"
    CLAY = "clay"
    SANDY = "sandy"
    SILT = "silt"
    CLAY_LOAM = "clay_loam"
    SANDY_LOAM = "sandy_loam"


class CropType(str, Enum):
    WHEAT = "wheat"
    RICE = "rice"
    MAIZE = "maize"
    COTTON = "cotton"
    SUGARCANE = "sugarcane"
    PULSES = "pulses"
    OILSEEDS = "oilseeds"
    VEGETABLES = "vegetables"


class GrowthStage(str, Enum):
    SOWING = "sowing"
    GERMINATION = "germination"
    VEGETATIVE = "vegetative"
    TILLERING = "tillering"
    BOOTING = "booting"
    FLOWERING = "flowering"
    GRAIN_FILLING = "grain_filling"
    MATURITY = "maturity"
    HARVESTING = "harvesting"


class WeatherData(BaseModel):
    temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    precipitation_mm: float
    solar_radiation_mj: float
    forecast_days: int = 7


class MarketData(BaseModel):
    crop_name: str
    current_price_per_kg: float
    price_trend: str  # "rising", "falling", "stable"
    demand_level: str  # "high", "medium", "low"
    supply_level: str  # "high", "medium", "low"
    market_location: str


class SoilHealthData(BaseModel):
    ph_level: Optional[float] = None
    nitrogen_kg_ha: Optional[float] = None
    phosphorus_kg_ha: Optional[float] = None
    potassium_kg_ha: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    soil_moisture_pct: Optional[float] = None
    soil_temperature_c: Optional[float] = None


class FarmerProfile(BaseModel):
    farmer_id: str = Field(..., description="Unique identifier for the farmer")
    name: Optional[str] = None
    location_lat: float
    location_lon: float
    district: Optional[str] = None
    state: Optional[str] = None
    farm_size_hectares: Optional[float] = None
    crop: CropType = Field(..., description="Primary crop")
    growth_stage: Optional[GrowthStage] = None
    soil_type: Optional[SoilType] = None
    irrigation_type: Optional[str] = None  # "drip", "sprinkler", "flood", "rainfed"
    farming_practice: Optional[str] = None  # "organic", "conventional", "mixed"


class SensorData(BaseModel):
    soil_moisture_pct: Optional[float] = Field(None, description="Current volumetric water content percentage")
    soil_temperature_c: Optional[float] = None
    air_temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    last_rain_mm_24h: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    solar_radiation_mj: Optional[float] = None


class AdvisoryRequest(BaseModel):
    profile: FarmerProfile
    sensors: Optional[SensorData] = None
    weather: Optional[WeatherData] = None
    market: Optional[MarketData] = None
    soil_health: Optional[SoilHealthData] = None
    horizon_days: int = Field(7, ge=1, le=30)
    language: str = Field("en", description="Preferred language for recommendations")


class AgentRecommendation(BaseModel):
    agent: str
    priority: int = Field(5, ge=1, le=10)
    confidence_score: float = Field(0.8, ge=0.0, le=1.0)
    summary: str
    explanation: str
    data_sources: List[str] = []
    details: Dict[str, Any] = {}
    tasks: List[str] = []
    risk_level: Optional[str] = None  # "low", "medium", "high", "critical"
    estimated_impact: Optional[str] = None  # "positive", "negative", "neutral"
    cost_estimate: Optional[Dict[str, Any]] = None


class AdvisoryResponse(BaseModel):
    farmer_id: str
    crop: str
    horizon_days: int
    generated_at: datetime = Field(default_factory=datetime.now)
    recommendations: List[AgentRecommendation]
    unified_plan: List[str]
    risk_assessment: Dict[str, Any] = {}
    weather_summary: Optional[Dict[str, Any]] = None
    market_summary: Optional[Dict[str, Any]] = None
    soil_summary: Optional[Dict[str, Any]] = None
    confidence_overall: float = Field(0.8, ge=0.0, le=1.0)
    response_time_ms: Optional[float] = None


class DataSource(BaseModel):
    name: str
    type: str  # "weather", "market", "soil", "pest", "policy"
    url: Optional[str] = None
    last_updated: Optional[datetime] = None
    reliability_score: float = Field(0.8, ge=0.0, le=1.0)


class SystemHealth(BaseModel):
    status: str
    agents_online: int
    total_agents: int
    data_sources: List[DataSource]
    response_time_ms: float
    uptime_percentage: float



# ===== Authentication & OTP Schemas =====
class SendOtpRequest(BaseModel):
    """Request to send an OTP to a phone number."""
    phone: str = Field(..., description="Phone number in local or E.164 format")
    name: Optional[str] = Field(None, description="Name to associate with this phone, if new user")


class SendOtpResponse(BaseModel):
    """Response for OTP send request."""
    success: bool
    message: str
    expires_at: Optional[datetime] = None
    dev_code: Optional[str] = None  # Provided only in dev for testing


class VerifyOtpRequest(BaseModel):
    """Request to verify an OTP for a phone number."""
    phone: str
    otp: str


class VerifyOtpResponse(BaseModel):
    """Response for OTP verification containing farmer profile binding."""
    success: bool
    message: str
    farmer_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
