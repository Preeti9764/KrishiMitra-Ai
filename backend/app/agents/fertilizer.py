from ..models.schemas import AdvisoryRequest, AgentRecommendation


NPK_DEFAULTS = {
    "wheat": {"N": 120, "P": 60, "K": 40},
    "rice": {"N": 150, "P": 60, "K": 40},
}


class FertilizerAgent:
    """Simple rule-based MVP for NPK recommendation by crop and stage."""

    def recommend(self, request: AdvisoryRequest) -> AgentRecommendation:
        crop = request.profile.crop.lower()
        stage = (request.profile.growth_stage or "").lower()
        defaults = NPK_DEFAULTS.get(crop, {"N": 100, "P": 50, "K": 40})

        # Split-N logic by stage
        split_plan = []
        if "sow" in stage or "plant" in stage:
            split_plan.append("Apply 40% of N and full P and K as basal dose")
        elif any(x in stage for x in ["till", "vegetative"]):
            split_plan.append("Top-dress 30% of N")
        elif any(x in stage for x in ["boot", "flower", "panicle"]):
            split_plan.append("Top-dress remaining 30% of N")
        else:
            split_plan.append("Follow split N application based on growth stage (40/30/30)")

        tasks = [
            f"Target total season NPK (kg/ha): N {defaults['N']}, P {defaults['P']}, K {defaults['K']}"
        ] + split_plan

        details = {"npk_target_kg_per_ha": defaults, "stage": stage}

        return AgentRecommendation(
            agent="fertilizer",
            priority=7,
            confidence_score=0.8,
            summary="Provide stage-wise NPK recommendation based on crop.",
            explanation="NPK recommendations are based on crop type and current growth stage, following split application principles for optimal nutrient uptake.",
            tasks=tasks,
            details=details,
        )


