import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..models.schemas import AdvisoryRequest, AgentRecommendation, WeatherData
from ..data_preprocessing.weather_data import WeatherDataProcessor


class WeatherRiskAgent:
    """Weather Risk Agent for predicting extreme weather events and mitigation strategies"""
    
    def __init__(self):
        self.weather_processor = WeatherDataProcessor()
        self.risk_thresholds = {
            "drought": {
                "temperature_threshold": 35.0,
                "precipitation_threshold": 5.0,
                "consecutive_dry_days": 7
            },
            "flood": {
                "precipitation_threshold": 50.0,
                "consecutive_wet_days": 3
            },
            "heat_wave": {
                "temperature_threshold": 40.0,
                "consecutive_hot_days": 3
            },
            "cold_wave": {
                "temperature_threshold": 5.0,
                "consecutive_cold_days": 3
            },
            "cyclone": {
                "wind_speed_threshold": 50.0,
                "precipitation_threshold": 100.0
            }
        }
        
        self.mitigation_strategies = {
            "drought": [
                "Implement mulching to conserve soil moisture",
                "Use drought-resistant crop varieties",
                "Adjust irrigation schedule to early morning/evening",
                "Consider crop insurance for drought protection",
                "Store water in ponds/tanks for emergency use"
            ],
            "flood": [
                "Ensure proper drainage system in fields",
                "Elevate seed storage areas",
                "Prepare sandbags for field protection",
                "Monitor weather alerts regularly",
                "Have emergency crop protection measures ready"
            ],
            "heat_wave": [
                "Increase irrigation frequency during heat waves",
                "Use shade nets for sensitive crops",
                "Avoid field work during peak hours (10 AM - 4 PM)",
                "Apply foliar sprays to reduce heat stress",
                "Consider early harvesting if crops are mature"
            ],
            "cold_wave": [
                "Use row covers or plastic tunnels",
                "Apply organic mulch to retain soil heat",
                "Irrigate fields before cold nights",
                "Use windbreaks to reduce cold wind impact",
                "Consider crop insurance for frost damage"
            ],
            "cyclone": [
                "Harvest mature crops immediately",
                "Secure farm equipment and structures",
                "Store harvested produce in safe locations",
                "Monitor official cyclone warnings",
                "Prepare emergency contact list"
            ]
        }
    
    async def recommend(self, request: AdvisoryRequest) -> AgentRecommendation:
        """Generate weather risk recommendations"""
        # Get weather data if not provided
        weather_data = request.weather
        if not weather_data:
            weather_data = await self.weather_processor.get_weather_forecast(
                request.profile.location_lat,
                request.profile.location_lon,
                request.horizon_days
            )
        
        # Assess weather risks
        risk_assessment = self._assess_weather_risks(weather_data, request)
        
        # Generate mitigation strategies
        mitigation_tasks = self._generate_mitigation_tasks(risk_assessment, request)
        
        # Calculate confidence and priority
        confidence = self._calculate_confidence(weather_data, risk_assessment)
        priority = self._determine_priority(risk_assessment)
        
        return AgentRecommendation(
            agent="weather_risk",
            priority=priority,
            confidence_score=confidence,
            summary=f"Weather risk assessment and mitigation strategies for {request.profile.crop}",
            explanation=self._generate_explanation(risk_assessment, weather_data),
            data_sources=["NASA POWER API", "IMD Weather Forecast", "Historical Weather Database"],
            tasks=mitigation_tasks,
            risk_level=self._get_overall_risk_level(risk_assessment),
            estimated_impact="positive",
            cost_estimate=self._estimate_mitigation_costs(risk_assessment),
            details=risk_assessment
        )
    
    def _assess_weather_risks(self, weather_data: WeatherData, request: AdvisoryRequest) -> Dict[str, Any]:
        """Assess various weather risks"""
        risks = {}
        
        # Drought risk
        drought_risk = self._assess_drought_risk(weather_data)
        risks["drought"] = drought_risk
        
        # Flood risk
        flood_risk = self._assess_flood_risk(weather_data)
        risks["flood"] = flood_risk
        
        # Heat wave risk
        heat_risk = self._assess_heat_wave_risk(weather_data)
        risks["heat_wave"] = heat_risk
        
        # Cold wave risk
        cold_risk = self._assess_cold_wave_risk(weather_data)
        risks["cold_wave"] = cold_risk
        
        # Cyclone risk (simplified)
        cyclone_risk = self._assess_cyclone_risk(weather_data)
        risks["cyclone"] = cyclone_risk
        
        # Overall risk assessment
        risks["overall_risk_level"] = self._calculate_overall_risk(risks)
        risks["risk_score"] = self._calculate_risk_score(risks)
        
        return risks
    
    def _assess_drought_risk(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Assess drought risk"""
        thresholds = self.risk_thresholds["drought"]
        
        risk_factors = []
        risk_score = 0
        
        # Temperature factor
        if weather_data.temperature_c > thresholds["temperature_threshold"]:
            risk_factors.append("High temperature")
            risk_score += 0.3
        
        # Precipitation factor
        if weather_data.precipitation_mm < thresholds["precipitation_threshold"]:
            risk_factors.append("Low precipitation")
            risk_score += 0.4
        
        # Humidity factor
        if weather_data.humidity_pct < 40:
            risk_factors.append("Low humidity")
            risk_score += 0.2
        
        # Wind factor
        if weather_data.wind_speed_kmh > 20:
            risk_factors.append("High wind speed")
            risk_score += 0.1
        
        risk_level = "low"
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "probability": min(risk_score * 100, 95)
        }
    
    def _assess_flood_risk(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Assess flood risk"""
        thresholds = self.risk_thresholds["flood"]
        
        risk_factors = []
        risk_score = 0
        
        # Precipitation factor
        if weather_data.precipitation_mm > thresholds["precipitation_threshold"]:
            risk_factors.append("Heavy precipitation")
            risk_score += 0.6
        
        # Humidity factor
        if weather_data.humidity_pct > 80:
            risk_factors.append("High humidity")
            risk_score += 0.2
        
        # Wind factor (for storm surge)
        if weather_data.wind_speed_kmh > 30:
            risk_factors.append("Strong winds")
            risk_score += 0.2
        
        risk_level = "low"
        if risk_score > 0.6:
            risk_level = "high"
        elif risk_score > 0.3:
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "probability": min(risk_score * 100, 95)
        }
    
    def _assess_heat_wave_risk(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Assess heat wave risk"""
        thresholds = self.risk_thresholds["heat_wave"]
        
        risk_factors = []
        risk_score = 0
        
        # Temperature factor
        if weather_data.temperature_c > thresholds["temperature_threshold"]:
            risk_factors.append("Extreme temperature")
            risk_score += 0.7
        
        # Humidity factor
        if weather_data.humidity_pct > 70:
            risk_factors.append("High humidity")
            risk_score += 0.2
        
        # Solar radiation factor
        if weather_data.solar_radiation_mj > 25:
            risk_factors.append("High solar radiation")
            risk_score += 0.1
        
        risk_level = "low"
        if risk_score > 0.6:
            risk_level = "high"
        elif risk_score > 0.3:
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "probability": min(risk_score * 100, 95)
        }
    
    def _assess_cold_wave_risk(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Assess cold wave risk"""
        thresholds = self.risk_thresholds["cold_wave"]
        
        risk_factors = []
        risk_score = 0
        
        # Temperature factor
        if weather_data.temperature_c < thresholds["temperature_threshold"]:
            risk_factors.append("Low temperature")
            risk_score += 0.7
        
        # Wind factor
        if weather_data.wind_speed_kmh > 15:
            risk_factors.append("Cold winds")
            risk_score += 0.2
        
        # Humidity factor
        if weather_data.humidity_pct > 80:
            risk_factors.append("High humidity")
            risk_score += 0.1
        
        risk_level = "low"
        if risk_score > 0.6:
            risk_level = "high"
        elif risk_score > 0.3:
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "probability": min(risk_score * 100, 95)
        }
    
    def _assess_cyclone_risk(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Assess cyclone risk (simplified)"""
        thresholds = self.risk_thresholds["cyclone"]
        
        risk_factors = []
        risk_score = 0
        
        # Wind speed factor
        if weather_data.wind_speed_kmh > thresholds["wind_speed_threshold"]:
            risk_factors.append("High wind speed")
            risk_score += 0.6
        
        # Precipitation factor
        if weather_data.precipitation_mm > thresholds["precipitation_threshold"]:
            risk_factors.append("Heavy precipitation")
            risk_score += 0.4
        
        risk_level = "low"
        if risk_score > 0.5:
            risk_level = "high"
        elif risk_score > 0.2:
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "probability": min(risk_score * 100, 95)
        }
    
    def _calculate_overall_risk(self, risks: Dict[str, Any]) -> str:
        """Calculate overall risk level"""
        high_risks = sum(1 for risk_type in ["drought", "flood", "heat_wave", "cold_wave", "cyclone"] 
                        if risks[risk_type]["risk_level"] == "high")
        medium_risks = sum(1 for risk_type in ["drought", "flood", "heat_wave", "cold_wave", "cyclone"] 
                          if risks[risk_type]["risk_level"] == "medium")
        
        if high_risks > 0:
            return "high"
        elif medium_risks > 1:
            return "medium"
        else:
            return "low"
    
    def _calculate_risk_score(self, risks: Dict[str, Any]) -> float:
        """Calculate overall risk score"""
        total_score = 0
        for risk_type in ["drought", "flood", "heat_wave", "cold_wave", "cyclone"]:
            total_score += risks[risk_type]["risk_score"]
        return min(total_score, 1.0)
    
    def _generate_mitigation_tasks(self, risk_assessment: Dict[str, Any], request: AdvisoryRequest) -> List[str]:
        """Generate mitigation tasks based on risk assessment"""
        tasks = []
        
        # Add tasks for each high-risk weather event
        for risk_type in ["drought", "flood", "heat_wave", "cold_wave", "cyclone"]:
            if risk_assessment[risk_type]["risk_level"] in ["medium", "high"]:
                strategies = self.mitigation_strategies[risk_type]
                # Add top 2 strategies for each risk
                tasks.extend(strategies[:2])
        
        # Add general monitoring tasks
        tasks.append("Monitor weather alerts and forecasts daily")
        tasks.append("Keep emergency contact numbers handy")
        
        # Add crop-specific recommendations
        if request.profile.growth_stage in ["flowering", "grain_filling"]:
            tasks.append("Protect flowering crops from extreme weather")
        
        return tasks[:8]  # Limit to 8 tasks
    
    def _calculate_confidence(self, weather_data: WeatherData, risk_assessment: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        confidence = 0.8  # Base confidence
        
        # Higher confidence if we have comprehensive weather data
        if weather_data:
            confidence += 0.1
        
        # Higher confidence if risk levels are clear
        if risk_assessment["overall_risk_level"] != "low":
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _determine_priority(self, risk_assessment: Dict[str, Any]) -> int:
        """Determine priority based on risk level"""
        if risk_assessment["overall_risk_level"] == "high":
            return 10  # Highest priority
        elif risk_assessment["overall_risk_level"] == "medium":
            return 8
        else:
            return 6
    
    def _get_overall_risk_level(self, risk_assessment: Dict[str, Any]) -> str:
        """Get overall risk level"""
        return risk_assessment["overall_risk_level"]
    
    def _estimate_mitigation_costs(self, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate costs for mitigation measures"""
        base_cost = 1000  # INR per hectare
        
        # Scale cost based on risk level
        if risk_assessment["overall_risk_level"] == "high":
            cost_multiplier = 3.0
        elif risk_assessment["overall_risk_level"] == "medium":
            cost_multiplier = 1.5
        else:
            cost_multiplier = 1.0
        
        total_cost = base_cost * cost_multiplier
        
        return {
            "estimated_cost_inr": total_cost,
            "cost_unit": "INR per hectare",
            "cost_breakdown": {
                "protective_measures": total_cost * 0.6,
                "monitoring_systems": total_cost * 0.2,
                "insurance_premium": total_cost * 0.2
            }
        }
    
    def _generate_explanation(self, risk_assessment: Dict[str, Any], weather_data: WeatherData) -> str:
        """Generate human-readable explanation"""
        high_risks = [risk_type for risk_type in ["drought", "flood", "heat_wave", "cold_wave", "cyclone"] 
                     if risk_assessment[risk_type]["risk_level"] == "high"]
        
        if high_risks:
            risk_names = ", ".join(high_risks).replace("_", " ")
            return f"High risk of {risk_names} detected based on current weather conditions. " \
                   f"Temperature: {weather_data.temperature_c:.1f}°C, " \
                   f"Precipitation: {weather_data.precipitation_mm:.1f}mm, " \
                   f"Wind: {weather_data.wind_speed_kmh:.1f} km/h. " \
                   f"Immediate mitigation measures recommended."
        else:
            return f"Weather conditions are generally favorable. " \
                   f"Temperature: {weather_data.temperature_c:.1f}°C, " \
                   f"Precipitation: {weather_data.precipitation_mm:.1f}mm. " \
                   f"Continue monitoring for any changes."
