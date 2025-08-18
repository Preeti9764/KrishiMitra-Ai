import asyncio
from typing import List, Dict, Any
from datetime import datetime

from ..models.schemas import (
    AdvisoryRequest,
    AdvisoryResponse,
    AgentRecommendation,
)
from ..agents.irrigation import IrrigationAgent
from ..agents.fertilizer import FertilizerAgent
from ..agents.pest import PestAgent
from ..agents.market import MarketAgent
from ..agents.weather_risk import WeatherRiskAgent
from ..agents.seed_crop import SeedCropAgent
from ..agents.finance_policy import FinancePolicyAgent


class AdvisoryCoordinator:
    """Enhanced Coordinator with LangChain-style orchestration and conflict resolution"""

    def __init__(self) -> None:
        # Initialize all agents
        self.irrigation = IrrigationAgent()
        self.fertilizer = FertilizerAgent()
        self.pest = PestAgent()
        self.market = MarketAgent()
        self.weather_risk = WeatherRiskAgent()
        self.seed_crop = SeedCropAgent()
        self.finance_policy = FinancePolicyAgent()
        
        # Agent registry for easy access
        self.agents = {
            "irrigation": self.irrigation,
            "fertilizer": self.fertilizer,
            "pest": self.pest,
            "market": self.market,
            "weather_risk": self.weather_risk,
            "seed_crop": self.seed_crop,
            "finance_policy": self.finance_policy
        }
        
        # Language translations for common terms
        self.language_translations = {
            "hi": {  # Hindi
                "irrigation": "सिंचाई",
                "fertilizer": "उर्वरक",
                "pest": "कीट",
                "market": "बाजार",
                "weather_risk": "मौसम जोखिम",
                "seed_crop": "बीज फसल",
                "finance_policy": "वित्त नीति",
                "high_priority": "उच्च प्राथमिकता",
                "medium_priority": "मध्यम प्राथमिकता",
                "low_priority": "कम प्राथमिकता",
                "risk_level": "जोखिम स्तर",
                "confidence": "विश्वास",
                "recommendations": "सिफारिशें"
            },
            "pa": {  # Punjabi
                "irrigation": "ਸਿੰਚਾਈ",
                "fertilizer": "ਖਾਦ",
                "pest": "ਕੀੜਾ",
                "market": "ਬਾਜ਼ਾਰ",
                "weather_risk": "ਮੌਸਮ ਜੋਖਮ",
                "seed_crop": "ਬੀਜ ਫਸਲ",
                "finance_policy": "ਵਿੱਤ ਨੀਤੀ"
            },
            "bn": {  # Bengali
                "irrigation": "সেচ",
                "fertilizer": "সার",
                "pest": "পোকা",
                "market": "বাজার",
                "weather_risk": "আবহাওয়া ঝুঁকি",
                "seed_crop": "বীজ ফসল",
                "finance_policy": "অর্থনীতি নীতি"
            }
        }
        
        # Conflict resolution rules
        self.conflict_rules = {
            "irrigation_fertilizer": {
                "description": "Irrigation should be scheduled before fertilizer application",
                "priority_order": ["irrigation", "fertilizer"],
                "time_gap_days": 1
            },
            "weather_risk_irrigation": {
                "description": "Weather risk mitigation takes priority over regular irrigation",
                "priority_order": ["weather_risk", "irrigation"],
                "time_gap_days": 0
            },
            "pest_fertilizer": {
                "description": "Pest control should be applied before fertilizer to avoid waste",
                "priority_order": ["pest", "fertilizer"],
                "time_gap_days": 2
            }
        }

    def _translate_text(self, text: str, language: str) -> str:
        """Translate common terms to the specified language"""
        if language == "en" or language not in self.language_translations:
            return text
        
        translations = self.language_translations[language]
        for english, translated in translations.items():
            text = text.replace(english, translated)
        
        return text

    def _translate_recommendation(self, recommendation: AgentRecommendation, language: str) -> AgentRecommendation:
        """Translate recommendation text to specified language"""
        if language == "en":
            return recommendation
        
        # Create a copy to avoid modifying the original
        translated_rec = recommendation.copy()
        
        # Translate summary and explanation
        translated_rec.summary = self._translate_text(translated_rec.summary, language)
        translated_rec.explanation = self._translate_text(translated_rec.explanation, language)
        
        # Translate tasks
        translated_rec.tasks = [self._translate_text(task, language) for task in translated_rec.tasks]
        
        return translated_rec

    async def build_advisory_plan(self, request: AdvisoryRequest) -> AdvisoryResponse:
        """Build comprehensive advisory plan with all agents"""
        # Execute all agents concurrently
        agent_tasks = []
        for agent_name, agent in self.agents.items():
            task = asyncio.create_task(agent.recommend(request))
            agent_tasks.append((agent_name, task))
        
        # Wait for all agents to complete
        agent_outputs = []
        for agent_name, task in agent_tasks:
            try:
                result = await task
                agent_outputs.append(result)
            except Exception as e:
                print(f"Error in {agent_name} agent: {e}")
                # Create fallback recommendation
                fallback = self._create_fallback_recommendation(agent_name, request)
                agent_outputs.append(fallback)
        
        # Apply conflict resolution
        resolved_recommendations = self._resolve_conflicts(agent_outputs)
        
        # Apply language translation if requested
        if request.language != "en":
            resolved_recommendations = [
                self._translate_recommendation(rec, request.language) 
                for rec in resolved_recommendations
            ]
        
        # Generate unified plan
        unified_plan = self._generate_unified_plan(resolved_recommendations, request)
        
        # Translate unified plan if needed
        if request.language != "en":
            unified_plan = [self._translate_text(task, request.language) for task in unified_plan]
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(resolved_recommendations)
        
        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(resolved_recommendations)
        
        # Generate summaries
        weather_summary = self._generate_weather_summary(resolved_recommendations)
        market_summary = self._generate_market_summary(resolved_recommendations)
        soil_summary = self._generate_soil_summary(resolved_recommendations)
        
        return AdvisoryResponse(
            farmer_id=request.profile.farmer_id,
            crop=request.profile.crop,
            horizon_days=request.horizon_days,
            generated_at=datetime.now(),
            recommendations=resolved_recommendations,
            unified_plan=unified_plan,
            confidence_overall=overall_confidence,
            risk_assessment=risk_assessment,
            weather_summary=weather_summary,
            market_summary=market_summary,
            soil_summary=soil_summary
        )

    def _resolve_conflicts(self, recommendations: List[AgentRecommendation]) -> List[AgentRecommendation]:
        """Resolve conflicts between agent recommendations"""
        resolved = recommendations.copy()
        
        # Sort by priority first
        resolved.sort(key=lambda r: r.priority, reverse=True)
        
        # Apply conflict resolution rules
        for rule_name, rule in self.conflict_rules.items():
            resolved = self._apply_conflict_rule(resolved, rule)
        
        # Remove duplicate tasks
        resolved = self._remove_duplicate_tasks(resolved)
        
        return resolved

    def _apply_conflict_rule(self, recommendations: List[AgentRecommendation], rule: Dict[str, Any]) -> List[AgentRecommendation]:
        """Apply a specific conflict resolution rule"""
        priority_order = rule["priority_order"]
        time_gap = rule.get("time_gap_days", 0)
        
        # Find agents involved in the conflict
        involved_agents = {}
        for rec in recommendations:
            if rec.agent in priority_order:
                involved_agents[rec.agent] = rec
        
        # Reorder based on priority
        if len(involved_agents) >= 2:
            for i, agent_name in enumerate(priority_order):
                if agent_name in involved_agents:
                    # Adjust priority to ensure proper ordering
                    involved_agents[agent_name].priority = 10 - i
        
        return recommendations

    def _remove_duplicate_tasks(self, recommendations: List[AgentRecommendation]) -> List[AgentRecommendation]:
        """Remove duplicate tasks across recommendations"""
        seen_tasks = set()
        for rec in recommendations:
            unique_tasks = []
            for task in rec.tasks:
                # Simple deduplication based on task content
                task_key = task.lower().replace(" ", "").replace(".", "")
                if task_key not in seen_tasks:
                    seen_tasks.add(task_key)
                    unique_tasks.append(task)
            rec.tasks = unique_tasks
        
        return recommendations

    def _generate_unified_plan(self, recommendations: List[AgentRecommendation], request: AdvisoryRequest) -> List[str]:
        """Generate unified plan from all recommendations"""
        unified_plan = []
        
        # Add high-priority tasks first
        high_priority_tasks = []
        medium_priority_tasks = []
        low_priority_tasks = []
        
        for rec in recommendations:
            if rec.priority >= 8:
                high_priority_tasks.extend(rec.tasks)
            elif rec.priority >= 6:
                medium_priority_tasks.extend(rec.tasks)
            else:
                low_priority_tasks.extend(rec.tasks)
        
        # Add tasks in priority order
        unified_plan.extend(high_priority_tasks[:3])  # Top 3 high priority
        unified_plan.extend(medium_priority_tasks[:4])  # Top 4 medium priority
        unified_plan.extend(low_priority_tasks[:3])  # Top 3 low priority
        
        # Add crop-specific summary
        if request.profile.growth_stage:
            unified_plan.append(f"Monitor {request.profile.crop} during {request.profile.growth_stage} stage")
        
        # Add general monitoring task
        unified_plan.append("Monitor weather conditions and adjust plans accordingly")
        
        return unified_plan[:10]  # Limit to 10 tasks

    def _calculate_overall_confidence(self, recommendations: List[AgentRecommendation]) -> float:
        """Calculate overall confidence score"""
        if not recommendations:
            return 0.5
        
        # Weighted average based on priority
        total_weight = 0
        weighted_confidence = 0
        
        for rec in recommendations:
            weight = rec.priority
            total_weight += weight
            weighted_confidence += rec.confidence_score * weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.5

    def _generate_risk_assessment(self, recommendations: List[AgentRecommendation]) -> Dict[str, Any]:
        """Generate overall risk assessment"""
        risk_levels = {}
        high_risks = []
        medium_risks = []
        
        for rec in recommendations:
            if rec.risk_level:
                risk_levels[rec.agent] = rec.risk_level
                if rec.risk_level == "high":
                    high_risks.append(rec.agent)
                elif rec.risk_level == "medium":
                    medium_risks.append(rec.agent)
        
        overall_risk = "low"
        if high_risks:
            overall_risk = "high"
        elif medium_risks:
            overall_risk = "medium"
        
        return {
            "overall_risk_level": overall_risk,
            "agent_risks": risk_levels,
            "high_risk_agents": high_risks,
            "medium_risk_agents": medium_risks,
            "risk_mitigation_priority": high_risks + medium_risks
        }

    def _generate_weather_summary(self, recommendations: List[AgentRecommendation]) -> Dict[str, Any]:
        """Generate weather summary from relevant agents"""
        weather_agents = ["irrigation", "weather_risk"]
        weather_data = {}
        
        for rec in recommendations:
            if rec.agent in weather_agents:
                weather_data[rec.agent] = {
                    "summary": rec.summary,
                    "risk_level": rec.risk_level,
                    "confidence": rec.confidence_score
                }
        
        return weather_data

    def _generate_market_summary(self, recommendations: List[AgentRecommendation]) -> Dict[str, Any]:
        """Generate market summary from relevant agents"""
        market_agents = ["market", "finance_policy"]
        market_data = {}
        
        for rec in recommendations:
            if rec.agent in market_agents:
                market_data[rec.agent] = {
                    "summary": rec.summary,
                    "estimated_impact": rec.estimated_impact,
                    "confidence": rec.confidence_score
                }
        
        return market_data

    def _generate_soil_summary(self, recommendations: List[AgentRecommendation]) -> Dict[str, Any]:
        """Generate soil summary from relevant agents"""
        soil_agents = ["irrigation", "fertilizer", "seed_crop"]
        soil_data = {}
        
        for rec in recommendations:
            if rec.agent in soil_agents:
                soil_data[rec.agent] = {
                    "summary": rec.summary,
                    "priority": rec.priority,
                    "confidence": rec.confidence_score
                }
        
        return soil_data

    def _create_fallback_recommendation(self, agent_name: str, request: AdvisoryRequest) -> AgentRecommendation:
        """Create fallback recommendation when agent fails"""
        fallback_summaries = {
            "irrigation": "Monitor soil moisture and irrigate as needed",
            "fertilizer": "Apply balanced fertilizer based on soil test",
            "pest": "Monitor for pest activity and apply control measures if needed",
            "market": "Monitor market prices and sell at appropriate time",
            "weather_risk": "Monitor weather forecasts for potential risks",
            "seed_crop": "Select appropriate crop variety for your region",
            "finance_policy": "Check for available government schemes and loans"
        }
        
        return AgentRecommendation(
            agent=agent_name,
            priority=5,
            confidence_score=0.5,
            summary=fallback_summaries.get(agent_name, "General recommendation"),
            explanation=f"Fallback recommendation for {agent_name} agent",
            data_sources=["Fallback"],
            tasks=[fallback_summaries.get(agent_name, "Follow general best practices")],
            risk_level="low",
            estimated_impact="neutral"
        )

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {
            "total_agents": len(self.agents),
            "agents_online": len(self.agents),
            "agent_list": list(self.agents.keys()),
            "last_updated": datetime.now().isoformat()
        }
        return status

    def get_conflict_rules(self) -> Dict[str, Any]:
        """Get current conflict resolution rules"""
        return self.conflict_rules


