import httpx
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..models.schemas import MarketData


class MarketDataProcessor:
    """Processes market data from AGMARKNET and other sources"""
    
    def __init__(self):
        self.agmarknet_base_url = "https://agmarknet.gov.in/api/v1"
        self.fallback_market_data = {
            "wheat": {"price": 22.5, "trend": "stable", "demand": "medium", "supply": "high"},
            "rice": {"price": 28.0, "trend": "rising", "demand": "high", "supply": "medium"},
            "maize": {"price": 18.5, "trend": "falling", "demand": "low", "supply": "high"},
            "cotton": {"price": 65.0, "trend": "stable", "demand": "medium", "supply": "medium"},
            "sugarcane": {"price": 3.2, "trend": "rising", "demand": "high", "supply": "low"},
            "pulses": {"price": 85.0, "trend": "stable", "demand": "high", "supply": "medium"},
            "oilseeds": {"price": 45.0, "trend": "rising", "demand": "medium", "supply": "low"},
            "vegetables": {"price": 35.0, "trend": "stable", "demand": "high", "supply": "medium"}
        }
    
    async def get_agmarknet_data(self, crop_name: str, state: str = "All India") -> Dict[str, Any]:
        """Fetch market data from AGMARKNET API"""
        try:
            # AGMARKNET API endpoint for price data
            params = {
                "commodity": crop_name,
                "state": state,
                "format": "json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.agmarknet_base_url}/price", params=params)
                response.raise_for_status()
                data = response.json()
                
            return self._process_agmarknet_response(data, crop_name)
        except Exception as e:
            print(f"Error fetching AGMARKNET data: {e}")
            return self._get_fallback_market_data(crop_name)
    
    def _process_agmarknet_response(self, data: Dict[str, Any], crop_name: str) -> Dict[str, Any]:
        """Process AGMARKNET API response"""
        try:
            if "records" in data and len(data["records"]) > 0:
                # Get the latest price data
                latest_record = data["records"][0]
                
                # Calculate price trend based on historical data
                price_trend = self._calculate_price_trend(data["records"])
                
                return {
                    "crop_name": crop_name,
                    "current_price_per_kg": float(latest_record.get("modal_price", 0)),
                    "price_trend": price_trend,
                    "demand_level": self._estimate_demand_level(latest_record),
                    "supply_level": self._estimate_supply_level(latest_record),
                    "market_location": latest_record.get("market", "Unknown"),
                    "data_source": "AGMARKNET",
                    "last_updated": datetime.now().isoformat()
                }
            else:
                return self._get_fallback_market_data(crop_name)
        except Exception as e:
            print(f"Error processing AGMARKNET response: {e}")
            return self._get_fallback_market_data(crop_name)
    
    def _calculate_price_trend(self, records: List[Dict[str, Any]]) -> str:
        """Calculate price trend from historical data"""
        if len(records) < 2:
            return "stable"
        
        try:
            current_price = float(records[0].get("modal_price", 0))
            previous_price = float(records[1].get("modal_price", 0))
            
            if current_price > previous_price * 1.05:
                return "rising"
            elif current_price < previous_price * 0.95:
                return "falling"
            else:
                return "stable"
        except:
            return "stable"
    
    def _estimate_demand_level(self, record: Dict[str, Any]) -> str:
        """Estimate demand level based on market indicators"""
        # This is a simplified estimation - in real implementation,
        # you would use more sophisticated indicators
        arrivals = record.get("arrivals", 0)
        if isinstance(arrivals, str):
            try:
                arrivals = float(arrivals)
            except:
                arrivals = 0
        
        if arrivals < 100:
            return "high"
        elif arrivals < 500:
            return "medium"
        else:
            return "low"
    
    def _estimate_supply_level(self, record: Dict[str, Any]) -> str:
        """Estimate supply level based on market indicators"""
        arrivals = record.get("arrivals", 0)
        if isinstance(arrivals, str):
            try:
                arrivals = float(arrivals)
            except:
                arrivals = 0
        
        if arrivals > 1000:
            return "high"
        elif arrivals > 500:
            return "medium"
        else:
            return "low"
    
    def _get_fallback_market_data(self, crop_name: str) -> Dict[str, Any]:
        """Get fallback market data when API fails"""
        fallback = self.fallback_market_data.get(crop_name.lower(), 
                                                {"price": 25.0, "trend": "stable", "demand": "medium", "supply": "medium"})
        
        return {
            "crop_name": crop_name,
            "current_price_per_kg": fallback["price"],
            "price_trend": fallback["trend"],
            "demand_level": fallback["demand"],
            "supply_level": fallback["supply"],
            "market_location": "National Average",
            "data_source": "Fallback",
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_market_forecast(self, crop_name: str, days: int = 30) -> Dict[str, Any]:
        """Get market price forecast"""
        current_data = await self.get_agmarknet_data(crop_name)
        
        # Simple forecasting based on trend
        current_price = current_data["current_price_per_kg"]
        trend = current_data["price_trend"]
        
        if trend == "rising":
            forecast_price = current_price * 1.05
        elif trend == "falling":
            forecast_price = current_price * 0.95
        else:
            forecast_price = current_price
        
        return {
            "current_price": current_price,
            "forecast_price": forecast_price,
            "trend": trend,
            "confidence": 0.7,
            "forecast_days": days
        }
    
    def get_best_selling_time(self, crop_name: str, current_data: MarketData) -> Dict[str, Any]:
        """Recommend the best time to sell based on market conditions"""
        if current_data.price_trend == "rising" and current_data.demand_level == "high":
            recommendation = "Hold for better prices"
            urgency = "low"
        elif current_data.price_trend == "falling" and current_data.supply_level == "high":
            recommendation = "Sell soon to avoid further price drops"
            urgency = "high"
        elif current_data.demand_level == "high" and current_data.supply_level == "low":
            recommendation = "Good time to sell"
            urgency = "medium"
        else:
            recommendation = "Monitor market conditions"
            urgency = "low"
        
        return {
            "recommendation": recommendation,
            "urgency": urgency,
            "reasoning": f"Price trend: {current_data.price_trend}, Demand: {current_data.demand_level}, Supply: {current_data.supply_level}"
        }
