from typing import List

from ..models.schemas import (
    AdvisoryRequest,
    AdvisoryResponse,
    AgentRecommendation,
)
from ..agents.irrigation import IrrigationAgent
from ..agents.fertilizer import FertilizerAgent
from ..agents.pest import PestAgent
from ..agents.market import MarketAgent


class AdvisoryCoordinator:
    """Coordinates multiple specialized agents and merges outputs."""

    def __init__(self) -> None:
        self.irrigation = IrrigationAgent()
        self.fertilizer = FertilizerAgent()
        self.pest = PestAgent()
        self.market = MarketAgent()

    def build_advisory_plan(self, request: AdvisoryRequest) -> AdvisoryResponse:
        agent_outputs: List[AgentRecommendation] = []

        agent_outputs.append(self.irrigation.recommend(request))
        agent_outputs.append(self.fertilizer.recommend(request))
        agent_outputs.append(self.pest.recommend(request))
        agent_outputs.append(self.market.recommend(request))

        unified_plan = self._merge_recommendations(agent_outputs)

        return AdvisoryResponse(
            farmer_id=request.profile.farmer_id,
            crop=request.profile.crop,
            horizon_days=request.horizon_days,
            recommendations=agent_outputs,
            unified_plan=unified_plan,
        )

    def _merge_recommendations(self, outputs: List[AgentRecommendation]) -> List[str]:
        # Extremely simple MVP merger: sort by priority and flatten tasks
        outputs_sorted = sorted(outputs, key=lambda r: r.priority, reverse=True)
        merged_tasks: List[str] = []

        # Basic conflict resolution rules for MVP
        # Example: if fertilizer says "apply N" and irrigation says "irrigate", schedule irrigation first
        irrigation_tasks = [t for r in outputs_sorted if r.agent == "irrigation" for t in r.tasks]
        fertilizer_tasks = [t for r in outputs_sorted if r.agent == "fertilizer" for t in r.tasks]

        if irrigation_tasks and fertilizer_tasks:
            merged_tasks.extend(irrigation_tasks)
            merged_tasks.extend(fertilizer_tasks)
        else:
            for rec in outputs_sorted:
                merged_tasks.extend(rec.tasks)

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for task in merged_tasks:
            if task not in seen:
                seen.add(task)
                deduped.append(task)
        return deduped


