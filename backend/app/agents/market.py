from ..models.schemas import AdvisoryRequest, AgentRecommendation


class MarketAgent:
    """MVP placeholder: recommend checking local markets and aggregators.

    Future: integrate AGMARKNET and time-series price forecasting.
    """

    def recommend(self, request: AdvisoryRequest) -> AgentRecommendation:
        crop = request.profile.crop.lower()
        tasks = [
            f"Track weekly prices for {crop} at nearest mandis and online platforms",
            "If storage available, compare expected price trend vs. storage cost",
        ]

        return AgentRecommendation(
            agent="market",
            priority=4,
            confidence_score=0.7,
            summary="Monitor market prices and plan sales timing.",
            explanation="Market recommendations focus on price monitoring and optimal sales timing to maximize farmer profits.",
            tasks=tasks,
            details={"crop": crop},
        )


