import numpy as np
from typing import Dict, Any, List
from ..models.schemas import AdvisoryRequest, AgentRecommendation, WeatherData
from ..data_preprocessing.weather_data import WeatherDataProcessor


class IrrigationAgent:
    """Enhanced Irrigation Agent with ML capabilities and weather integration"""
    
    def __init__(self):
        self.weather_processor = WeatherDataProcessor()
        self.ml_model = self._initialize_ml_model()
        self.crop_water_requirements = {
            "wheat": {"daily_mm": 4.5, "critical_stages": ["tillering", "flowering"]},
            "rice": {"daily_mm": 8.0, "critical_stages": ["vegetative", "flowering"]},
            "maize": {"daily_mm": 5.5, "critical_stages": ["vegetative", "tasseling"]},
            "cotton": {"daily_mm": 6.0, "critical_stages": ["flowering", "boll_formation"]},
            "sugarcane": {"daily_mm": 7.0, "critical_stages": ["vegetative", "grand_growth"]},
            "pulses": {"daily_mm": 3.5, "critical_stages": ["flowering", "pod_formation"]},
            "oilseeds": {"daily_mm": 4.0, "critical_stages": ["flowering", "seed_formation"]},
            "vegetables": {"daily_mm": 5.0, "critical_stages": ["vegetative", "flowering"]}
        }
    
    def _initialize_ml_model(self):
        """Initialize simple rule-based model for irrigation prediction"""
        # Placeholder for ML model - using rule-based approach for now
        return None
    
    async def recommend(self, request: AdvisoryRequest) -> AgentRecommendation:
        """Generate irrigation recommendations"""
        # Get weather data if not provided
        weather_data = request.weather
        if not weather_data:
            weather_data = await self.weather_processor.get_weather_forecast(
                request.profile.location_lat, 
                request.profile.location_lon,
                request.horizon_days
            )
        
        # Calculate irrigation needs
        irrigation_needs = self._calculate_irrigation_needs(request, weather_data)
        
        # Generate tasks and recommendations
        tasks = self._generate_irrigation_tasks(irrigation_needs, request)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(request, weather_data)
        
        # Determine priority
        priority = self._determine_priority(irrigation_needs, request)
        
        return AgentRecommendation(
            agent="irrigation",
            priority=priority,
            confidence_score=confidence,
            summary=f"Optimal irrigation schedule for {request.profile.crop} based on weather and soil conditions",
            explanation=self._generate_explanation(irrigation_needs, weather_data),
            data_sources=["NASA POWER API", "Soil Moisture Sensors", "Crop Water Requirements Database"],
            tasks=tasks,
            risk_level=self._assess_risk_level(irrigation_needs),
            estimated_impact="positive",
            cost_estimate=self._estimate_costs(irrigation_needs),
            details=irrigation_needs
        )
    
    def _calculate_irrigation_needs(self, request: AdvisoryRequest, weather_data: WeatherData) -> Dict[str, Any]:
        """Calculate irrigation requirements"""
        crop = request.profile.crop
        crop_data = self.crop_water_requirements.get(crop, {"daily_mm": 5.0, "critical_stages": []})
        
        # Base water requirement
        daily_requirement = crop_data["daily_mm"]
        
        # Adjust for growth stage
        stage_multiplier = self._get_stage_multiplier(request.profile.growth_stage, crop_data["critical_stages"])
        adjusted_requirement = daily_requirement * stage_multiplier
        
        # Adjust for weather conditions
        weather_adjustment = self._calculate_weather_adjustment(weather_data)
        final_requirement = adjusted_requirement * weather_adjustment
        
        # Calculate deficit
        soil_moisture = request.sensors.soil_moisture_pct if request.sensors else 20.0
        moisture_deficit = max(0, 30 - soil_moisture)  # Assume 30% is optimal
        
        return {
            "daily_requirement_mm": final_requirement,
            "moisture_deficit_pct": moisture_deficit,
            "irrigation_frequency_days": self._calculate_frequency(final_requirement, moisture_deficit),
            "irrigation_duration_minutes": self._calculate_duration(final_requirement, request.profile.farm_size_hectares),
            "water_efficiency_tips": self._get_efficiency_tips(request.profile.irrigation_type),
            "weather_impact": weather_adjustment,
            "stage_impact": stage_multiplier
        }
    
    def _get_stage_multiplier(self, growth_stage: str, critical_stages: List[str]) -> float:
        """Get water requirement multiplier based on growth stage"""
        if growth_stage in critical_stages:
            return 1.3  # 30% more water during critical stages
        elif growth_stage in ["sowing", "germination"]:
            return 0.8  # Less water during early stages
        elif growth_stage in ["maturity", "harvesting"]:
            return 0.6  # Reduced water during maturity
        else:
            return 1.0  # Normal water requirement
    
    def _calculate_weather_adjustment(self, weather_data: WeatherData) -> float:
        """Calculate weather-based adjustment factor"""
        # High temperature increases water requirement
        temp_factor = 1.0 + (weather_data.temperature_c - 25) * 0.02
        
        # High wind increases evaporation
        wind_factor = 1.0 + (weather_data.wind_speed_kmh - 10) * 0.01
        
        # Low humidity increases water requirement
        humidity_factor = 1.0 + (60 - weather_data.humidity_pct) * 0.005
        
        # Precipitation reduces irrigation need
        rain_factor = max(0.5, 1.0 - weather_data.precipitation_mm * 0.1)
        
        return temp_factor * wind_factor * humidity_factor * rain_factor
    
    def _calculate_frequency(self, daily_requirement: float, moisture_deficit: float) -> int:
        """Calculate irrigation frequency in days"""
        if moisture_deficit > 15:
            return 1  # Daily irrigation if severe deficit
        elif moisture_deficit > 10:
            return 2  # Every 2 days
        elif daily_requirement > 6:
            return 3  # Every 3 days for high water requirement
        else:
            return 4  # Every 4 days for normal conditions
    
    def _calculate_duration(self, daily_requirement: float, farm_size: float) -> int:
        """Calculate irrigation duration in minutes"""
        # Simplified calculation - in real implementation, consider irrigation system efficiency
        base_duration = daily_requirement * 10  # 10 minutes per mm
        size_factor = min(2.0, farm_size / 2.0)  # Scale with farm size
        return int(base_duration * size_factor)
    
    def _get_efficiency_tips(self, irrigation_type: str) -> List[str]:
        """Get water efficiency tips based on irrigation type"""
        tips = {
            "drip": [
                "Check for clogged emitters regularly",
                "Maintain proper pressure (1-2 bar)",
                "Use mulch to reduce evaporation"
            ],
            "sprinkler": [
                "Irrigate during early morning or evening",
                "Avoid irrigation during windy conditions",
                "Check for uniform water distribution"
            ],
            "flood": [
                "Level the field properly",
                "Use bunds to prevent water runoff",
                "Monitor water depth regularly"
            ],
            "rainfed": [
                "Implement soil moisture conservation",
                "Use drought-resistant crop varieties",
                "Practice crop rotation"
            ]
        }
        return tips.get(irrigation_type, ["Monitor soil moisture regularly", "Avoid over-irrigation"])
    
    def _generate_irrigation_tasks(self, irrigation_needs: Dict[str, Any], request: AdvisoryRequest) -> List[str]:
        """Generate specific irrigation tasks"""
        tasks = []
        
        if irrigation_needs["moisture_deficit_pct"] > 10:
            tasks.append(f"Irrigate immediately - soil moisture deficit is {irrigation_needs['moisture_deficit_pct']:.1f}%")
        
        tasks.append(f"Schedule irrigation every {irrigation_needs['irrigation_frequency_days']} days")
        tasks.append(f"Apply {irrigation_needs['daily_requirement_mm']:.1f} mm of water per day")
        
        if irrigation_needs["irrigation_duration_minutes"] > 0:
            tasks.append(f"Run irrigation system for {irrigation_needs['irrigation_duration_minutes']} minutes per session")
        
        # Add efficiency tips
        for tip in irrigation_needs["water_efficiency_tips"][:2]:  # Limit to 2 tips
            tasks.append(tip)
        
        return tasks
    
    def _calculate_confidence(self, request: AdvisoryRequest, weather_data: WeatherData) -> float:
        """Calculate confidence score for recommendations"""
        confidence = 0.8  # Base confidence
        
        # Increase confidence if we have sensor data
        if request.sensors and request.sensors.soil_moisture_pct is not None:
            confidence += 0.1
        
        # Increase confidence if we have weather data
        if weather_data:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _determine_priority(self, irrigation_needs: Dict[str, Any], request: AdvisoryRequest) -> int:
        """Determine priority level for irrigation recommendations"""
        if irrigation_needs["moisture_deficit_pct"] > 15:
            return 9  # Critical - immediate action needed
        elif irrigation_needs["moisture_deficit_pct"] > 10:
            return 8  # High priority
        elif request.profile.growth_stage in ["flowering", "tillering"]:
            return 7  # Important during critical stages
        else:
            return 6  # Normal priority
    
    def _assess_risk_level(self, irrigation_needs: Dict[str, Any]) -> str:
        """Assess risk level for irrigation"""
        if irrigation_needs["moisture_deficit_pct"] > 15:
            return "high"
        elif irrigation_needs["moisture_deficit_pct"] > 10:
            return "medium"
        else:
            return "low"
    
    def _estimate_costs(self, irrigation_needs: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate irrigation costs"""
        # Simplified cost estimation
        water_cost_per_mm = 50  # INR per mm per hectare
        daily_cost = irrigation_needs["daily_requirement_mm"] * water_cost_per_mm
        
        return {
            "daily_cost_inr": daily_cost,
            "weekly_cost_inr": daily_cost * 7,
            "monthly_cost_inr": daily_cost * 30,
            "cost_unit": "INR per hectare"
        }
    
    def _generate_explanation(self, irrigation_needs: Dict[str, Any], weather_data: WeatherData) -> str:
        """Generate human-readable explanation"""
        return (
            f"Based on current weather conditions (temperature: {weather_data.temperature_c:.1f}°C, "
            f"humidity: {weather_data.humidity_pct:.1f}%, precipitation: {weather_data.precipitation_mm:.1f}mm) "
            f"and soil moisture deficit of {irrigation_needs['moisture_deficit_pct']:.1f}%, "
            f"the crop requires {irrigation_needs['daily_requirement_mm']:.1f}mm of water daily. "
            f"Weather conditions are affecting water requirement by a factor of {irrigation_needs['weather_impact']:.2f}."
        )


