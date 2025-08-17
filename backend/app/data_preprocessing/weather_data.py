import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from ..models.schemas import WeatherData


class WeatherDataProcessor:
    """Processes weather data from multiple sources including NASA POWER API"""
    
    def __init__(self):
        self.nasa_power_base_url = "https://power.larc.nasa.gov/api/temporal/daily/regional"
        self.openweather_api_key = None  # Set via environment variable
        
    async def get_nasa_power_data(self, lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch weather data from NASA POWER API"""
        try:
            params = {
                "parameters": "T2M,RH2M,WS2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
                "community": "RE",
                "longitude": lon,
                "latitude": lat,
                "start": start_date,
                "end": end_date,
                "format": "JSON"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.nasa_power_base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
            return self._process_nasa_power_response(data)
        except Exception as e:
            print(f"Error fetching NASA POWER data: {e}")
            return self._get_fallback_weather_data()
    
    def _process_nasa_power_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process NASA POWER API response"""
        if "properties" not in data or "parameter" not in data["properties"]:
            return self._get_fallback_weather_data()
            
        params = data["properties"]["parameter"]
        dates = list(params["T2M"].keys())
        
        # Get latest data
        latest_date = max(dates)
        
        return {
            "temperature_c": params["T2M"][latest_date] - 273.15,  # Convert K to C
            "humidity_pct": params["RH2M"][latest_date],
            "wind_speed_kmh": params["WS2M"][latest_date] * 3.6,  # Convert m/s to km/h
            "precipitation_mm": params["PRECTOTCORR"][latest_date],
            "solar_radiation_mj": params["ALLSKY_SFC_SW_DWN"][latest_date] / 1000000,  # Convert W/m² to MJ/m²
            "forecast_days": 7,
            "data_source": "NASA POWER API",
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_fallback_weather_data(self) -> Dict[str, Any]:
        """Fallback weather data when API fails"""
        return {
            "temperature_c": 25.0,
            "humidity_pct": 60.0,
            "wind_speed_kmh": 10.0,
            "precipitation_mm": 0.0,
            "solar_radiation_mj": 20.0,
            "forecast_days": 7,
            "data_source": "Fallback",
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_weather_forecast(self, lat: float, lon: float, days: int = 7) -> WeatherData:
        """Get weather forecast for the specified location"""
        end_date = datetime.now() + timedelta(days=days)
        start_date = datetime.now()
        
        weather_dict = await self.get_nasa_power_data(
            lat, lon,
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d")
        )
        
        return WeatherData(**weather_dict)
    
    def calculate_weather_risk(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Calculate weather-related risks"""
        risks = {
            "drought_risk": "low",
            "flood_risk": "low",
            "heat_stress_risk": "low",
            "cold_stress_risk": "low"
        }
        
        # Drought risk assessment
        if weather_data.precipitation_mm < 5 and weather_data.temperature_c > 30:
            risks["drought_risk"] = "high"
        elif weather_data.precipitation_mm < 10:
            risks["drought_risk"] = "medium"
            
        # Heat stress risk
        if weather_data.temperature_c > 35:
            risks["heat_stress_risk"] = "high"
        elif weather_data.temperature_c > 30:
            risks["heat_stress_risk"] = "medium"
            
        # Cold stress risk
        if weather_data.temperature_c < 5:
            risks["cold_stress_risk"] = "high"
        elif weather_data.temperature_c < 10:
            risks["cold_stress_risk"] = "medium"
            
        return risks
