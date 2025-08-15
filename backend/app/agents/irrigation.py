from ..models.schemas import AdvisoryRequest, AgentRecommendation


class IrrigationAgent:
    """Rule-based MVP: simple thresholds using soil moisture and forecast horizon.

    Future: incorporate NASA POWER weather forecast and ET0 models.
    """

    def recommend(self, request: AdvisoryRequest) -> AgentRecommendation:
        moisture = request.sensors.soil_moisture_pct if request.sensors else None
        crop = request.profile.crop.lower()

        summary = "Maintain optimal soil moisture for crop growth."
        priority = 8
        tasks = []

        low_threshold = 22 if crop in {"wheat", "rice"} else 20
        high_threshold = 35 if crop in {"wheat", "rice"} else 32

        if moisture is None:
            tasks.append("Check soil moisture sensor and irrigate if topsoil is dry to touch")
        elif moisture < low_threshold:
            tasks.append(f"Irrigate today to raise soil moisture above {low_threshold}%")
        elif moisture > high_threshold:
            tasks.append("Skip irrigation; soil moisture is sufficient")
        else:
            tasks.append("Monitor; schedule light irrigation within 2-3 days")

        details = {
            "soil_moisture_pct": moisture,
            "low_threshold": low_threshold,
            "high_threshold": high_threshold,
        }

        return AgentRecommendation(
            agent="irrigation", priority=priority, summary=summary, tasks=tasks, details=details
        )


