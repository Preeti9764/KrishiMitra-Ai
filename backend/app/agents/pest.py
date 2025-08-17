from ..models.schemas import AdvisoryRequest, AgentRecommendation


class PestAgent:
    """MVP placeholder: rule-of-thumb risk based on season and crop.

    Future: CNN vision model + regional outbreak feeds.
    """

    async def recommend(self, request: AdvisoryRequest) -> AgentRecommendation:
        crop = request.profile.crop.lower()
        tasks = [
            "Scout fields twice this week for pest/disease symptoms",
            "Use pheromone traps if available; replace lures every 3-4 weeks",
        ]
        if crop == "rice":
            tasks.append("Monitor for stem borer and brown planthopper; check tillers and leaf sheaths")
        elif crop == "wheat":
            tasks.append("Monitor for rusts and aphids; inspect lower leaves for lesions")

        return AgentRecommendation(
            agent="pest",
            priority=6,
            confidence_score=0.7,
            summary="Routine scouting and crop-specific pest watchlist.",
            explanation="Pest monitoring recommendations focus on regular field scouting and crop-specific pest identification to enable early intervention.",
            tasks=tasks,
            details={"crop": crop},
        )


