from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FarmerProfile(BaseModel):
    farmer_id: str = Field(..., description="Unique identifier for the farmer")
    location_lat: float
    location_lon: float
    farm_size_hectares: Optional[float] = None
    crop: str = Field(..., description="Primary crop, e.g., wheat, rice")
    growth_stage: Optional[str] = Field(
        None, description="Crop growth stage, e.g., sowing, tillering, flowering"
    )
    soil_type: Optional[str] = None


class SensorData(BaseModel):
    soil_moisture_pct: Optional[float] = Field(
        None, description="Current volumetric water content percentage"
    )
    soil_temperature_c: Optional[float] = None
    last_rain_mm_24h: Optional[float] = None


class AdvisoryRequest(BaseModel):
    profile: FarmerProfile
    sensors: Optional[SensorData] = None
    horizon_days: int = Field(7, ge=1, le=14)


class AgentRecommendation(BaseModel):
    agent: str
    priority: int = Field(5, ge=1, le=10)
    summary: str
    details: Dict[str, Any] = {}
    tasks: List[str] = []


class AdvisoryResponse(BaseModel):
    farmer_id: str
    crop: str
    horizon_days: int
    recommendations: List[AgentRecommendation]
    unified_plan: List[str]


