import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..models.schemas import AdvisoryRequest, AgentRecommendation, WeatherData, SoilHealthData
from ..data_preprocessing.weather_data import WeatherDataProcessor
from ..data_preprocessing.market_data import MarketDataProcessor


class SeedCropAgent:
    """Seed and Crop Selection Agent using retrieval model for optimal variety recommendations"""
    
    def __init__(self):
        self.weather_processor = WeatherDataProcessor()
        self.market_processor = MarketDataProcessor()
        
        # Crop variety database
        self.crop_varieties = {
            "wheat": {
                "HD-2967": {"yield": "high", "disease_resistance": ["rust"], "drought_tolerance": "medium"},
                "PBW-343": {"yield": "medium", "disease_resistance": ["rust"], "drought_tolerance": "high"},
                "DBW-17": {"yield": "high", "disease_resistance": ["rust", "smut"], "drought_tolerance": "medium"}
            },
            "rice": {
                "Pusa-44": {"yield": "high", "disease_resistance": ["blast"], "drought_tolerance": "low"},
                "PR-114": {"yield": "medium", "disease_resistance": ["blast"], "drought_tolerance": "medium"},
                "HKR-47": {"yield": "high", "disease_resistance": ["blast", "bacterial_blight"], "drought_tolerance": "medium"}
            }
        }
    
    async def recommend(self, request: AdvisoryRequest) -> AgentRecommendation:
        """Generate seed and crop selection recommendations"""
        # Get weather data if not provided
        weather_data = request.weather
        if not weather_data:
            weather_data = await self.weather_processor.get_weather_forecast(
                request.profile.location_lat,
                request.profile.location_lon,
                request.horizon_days
            )
        
        # Analyze conditions
        conditions = self._analyze_conditions(request, weather_data)
        
        # Get variety recommendations
        variety_recommendations = self._get_variety_recommendations(request, conditions)
        
        # Generate tasks
        tasks = self._generate_selection_tasks(variety_recommendations, request)
        
        return AgentRecommendation(
            agent="seed_crop",
            priority=7,
            confidence_score=0.8,
            summary=f"Optimal seed variety selection for {request.profile.crop}",
            explanation=self._generate_explanation(variety_recommendations, conditions),
            data_sources=["Crop Variety Database", "Soil Health Card", "Weather Forecast"],
            tasks=tasks,
            risk_level="low",
            estimated_impact="positive",
            cost_estimate={"estimated_cost_inr": 2000, "cost_unit": "INR per hectare"},
            details={"variety_recommendations": variety_recommendations, "conditions": conditions}
        )
    
    def _analyze_conditions(self, request: AdvisoryRequest, weather_data: WeatherData) -> Dict[str, Any]:
        """Analyze current conditions for crop selection"""
        return {
            "soil_suitability": self._assess_soil_suitability(request),
            "climate_suitability": self._assess_climate_suitability(weather_data),
            "overall_suitability": 0.8
        }
    
    def _assess_soil_suitability(self, request: AdvisoryRequest) -> Dict[str, Any]:
        """Assess soil suitability"""
        soil_type = request.profile.soil_type
        suitability_score = 0.7
        
        if soil_type in ["loam", "clay_loam"]:
            suitability_score += 0.2
        
        return {"score": suitability_score, "soil_type": soil_type}
    
    def _assess_climate_suitability(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Assess climate suitability"""
        suitability_score = 0.7
        
        if 20 <= weather_data.temperature_c <= 30:
            suitability_score += 0.2
        
        return {"score": suitability_score, "temperature": weather_data.temperature_c}
    
    def _get_variety_recommendations(self, request: AdvisoryRequest, conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get variety recommendations"""
        crop = request.profile.crop
        varieties = self.crop_varieties.get(crop, {})
        
        recommendations = []
        for variety_name, variety_data in varieties.items():
            score = 0.7  # Base score
            if variety_data["yield"] == "high":
                score += 0.2
            if variety_data["drought_tolerance"] == "high":
                score += 0.1
            
            recommendations.append({
                "variety_name": variety_name,
                "score": score,
                "characteristics": variety_data
            })
        
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:2]
    
    def _generate_selection_tasks(self, variety_recommendations: List[Dict[str, Any]], request: AdvisoryRequest) -> List[str]:
        """Generate tasks for seed selection"""
        tasks = []
        
        if variety_recommendations:
            best_variety = variety_recommendations[0]
            tasks.append(f"Select {best_variety['variety_name']} variety for {request.profile.crop}")
            tasks.append("Purchase certified seeds from authorized dealers")
            tasks.append("Check seed germination rate before sowing")
        
        return tasks
    
    def _generate_explanation(self, variety_recommendations: List[Dict[str, Any]], conditions: Dict[str, Any]) -> str:
        """Generate explanation"""
        if not variety_recommendations:
            return "No suitable varieties found."
        
        best_variety = variety_recommendations[0]
        return f"Recommended: {best_variety['variety_name']} with {best_variety['score']*100:.1f}% suitability score."
