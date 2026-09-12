"""Unit tests for opportunity ranking."""

import pytest

from app.application.intelligence.buyer_scoring import BuyerScoringService
from app.application.ranking.ranker import OpportunityRanker
from app.domain.opportunity.models import AccountCandidate


@pytest.fixture
def ranker() -> OpportunityRanker:
    return OpportunityRanker()


@pytest.fixture
def scoring_service() -> BuyerScoringService:
    return BuyerScoringService()


def _make_candidate(name: str, total_raw: int) -> AccountCandidate:
    """Helper to create a candidate with proportional raw_data."""
    ratio = total_raw / 100
    return AccountCandidate(
        platform="douyin",
        account_name=name,
        profile_url=f"https://www.douyin.com/user/{name}",
        raw_data={
            "icp_fit": int(25 * ratio),
            "pain_intensity": int(20 * ratio),
            "usage_frequency": int(15 * ratio),
            "existing_spend": int(15 * ratio),
            "customer_value": int(10 * ratio),
            "buy_vs_build": int(10 * ratio),
            "reachability": int(5 * ratio),
        },
    )


class TestOpportunityRanker:
    """Tests for the OpportunityRanker."""

    def test_sorts_descending_by_total_score(
        self, ranker: OpportunityRanker, scoring_service: BuyerScoringService
    ) -> None:
        """Opportunities should be sorted by total score descending."""
        candidates = [
            (_make_candidate("Low", 40), None),
            (_make_candidate("High", 90), None),
            (_make_candidate("Medium", 65), None),
        ]
        # Score them
        scored = []
        for candidate, _ in candidates:
            score = scoring_service.score(candidate)
            scored.append((candidate, score))

        opportunities = ranker.rank(scored)
        assert len(opportunities) >= 2
        # Highest score first
        assert opportunities[0].buyer_score.total >= opportunities[1].buyer_score.total

    def test_filters_below_min_score(
        self, ranker: OpportunityRanker, scoring_service: BuyerScoringService
    ) -> None:
        """Candidates below min_score threshold should be excluded."""
        scored = []
        for name, raw in [("High", 90), ("Low", 20)]:
            candidate = _make_candidate(name, raw)
            score = scoring_service.score(candidate)
            scored.append((candidate, score))

        opportunities = ranker.rank(scored, min_score=30)
        # Low score candidate should be filtered out
        names = [o.candidate.account_name for o in opportunities]
        assert "Low" not in names

    def test_limits_to_top_n(
        self, ranker: OpportunityRanker, scoring_service: BuyerScoringService
    ) -> None:
        """Should return at most top_n opportunities."""
        scored = []
        for i in range(10):
            candidate = _make_candidate(f"Candidate_{i}", 50 + i * 3)
            score = scoring_service.score(candidate)
            scored.append((candidate, score))

        opportunities = ranker.rank(scored, top_n=5)
        assert len(opportunities) <= 5

    def test_opportunity_has_level(
        self, ranker: OpportunityRanker, scoring_service: BuyerScoringService
    ) -> None:
        """Each opportunity should have a level assigned."""
        candidate = _make_candidate("Test", 85)
        score = scoring_service.score(candidate)
        opportunities = ranker.rank([(candidate, score)])
        assert len(opportunities) == 1
        assert opportunities[0].level in ("S", "A", "B", "C")

    def test_opportunity_has_value_hypothesis(
        self, ranker: OpportunityRanker, scoring_service: BuyerScoringService
    ) -> None:
        """Each opportunity should have a value hypothesis."""
        candidate = _make_candidate("Test", 80)
        score = scoring_service.score(candidate)
        opportunities = ranker.rank([(candidate, score)])
        assert len(opportunities) == 1
        assert len(opportunities[0].value_hypothesis) > 0
