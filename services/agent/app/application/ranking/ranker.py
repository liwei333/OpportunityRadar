"""Opportunity Ranker — sorts and filters scored opportunities."""

import logging

from ...domain.opportunity.models import AccountCandidate, Opportunity
from ...domain.scoring.models import BuyerScore

logger = logging.getLogger(__name__)


class OpportunityRanker:
    """Rank opportunities by buyer score descending.

    Filters out competitors and applies minimum score threshold.
    """

    def rank(
        self,
        scored_candidates: list[tuple[AccountCandidate, BuyerScore]],
        top_n: int = 20,
        min_score: int = 30,
    ) -> list[Opportunity]:
        """Rank scored candidates into opportunities.

        Args:
            scored_candidates: List of (candidate, score) tuples.
            top_n: Maximum number of opportunities to return.
            min_score: Minimum total score to include.

        Returns:
            Ranked list of Opportunity objects.
        """
        opportunities: list[Opportunity] = []

        for candidate, score in scored_candidates:
            # Skip competitors (score = 0 and flagged)
            if candidate.raw_data.get("is_competitor", False):
                continue
            # Skip below minimum threshold
            if score.total < min_score:
                continue

            opportunity = Opportunity.from_score(
                candidate=candidate,
                buyer_score=score,
                value_hypothesis=self._build_value_hypothesis(candidate, score),
                recommended_action=self._build_recommended_action(score),
            )
            opportunities.append(opportunity)

        # Sort by total score descending
        opportunities.sort(key=lambda o: o.buyer_score.total, reverse=True)

        logger.info(
            "Ranked %d opportunities (from %d candidates, min_score=%d)",
            len(opportunities),
            len(scored_candidates),
            min_score,
        )

        return opportunities[:top_n]

    def _build_value_hypothesis(
        self,
        candidate: AccountCandidate,
        score: BuyerScore,
    ) -> str:
        """Generate a value hypothesis for the opportunity."""
        name = candidate.account_name
        if score.total >= 85:
            return (
                f"{name} 高度匹配目标客户画像，"
                f"有强烈的高频内容需求和获客痛点，"
                f"OpportunityRadar 可显著提升其市场研究效率"
            )
        if score.total >= 70:
            return (
                f"{name} 有明确的企业服务需求，"
                f"存在持续的市场研究和选题策划需求，"
                f"AI研究Agent可帮助其节省大量人工调研时间"
            )
        return (
            f"{name} 有一定匹配度，"
            f"可尝试展示OpportunityRadar在其服务行业的应用场景"
        )

    def _build_recommended_action(self, score: BuyerScore) -> str:
        """Generate recommended action based on score level."""
        if score.total >= 90:
            return "第一优先级联系，直接提供真实业务Demo"
        if score.total >= 80:
            return "高优先级联系，提供行业定制化演示"
        if score.total >= 70:
            return "次级联系，先发送产品介绍和案例"
        return "观察，后续跟进"
