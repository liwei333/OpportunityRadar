"""Unit tests for buyer scoring service."""

import pytest

from app.application.intelligence.buyer_scoring import BuyerScoringService
from app.domain.opportunity.models import AccountCandidate, OpportunityLevel


@pytest.fixture
def scoring_service() -> BuyerScoringService:
    return BuyerScoringService()


@pytest.fixture
def high_fit_candidate() -> AccountCandidate:
    return AccountCandidate(
        platform="douyin",
        account_name="星火短视频获客",
        profile_url="https://www.douyin.com/user/mock_xinghuo",
        raw_data={
            "icp_fit": 25,
            "pain_intensity": 20,
            "usage_frequency": 15,
            "existing_spend": 13,
            "customer_value": 9,
            "buy_vs_build": 9,
            "reachability": 4,
        },
    )


@pytest.fixture
def competitor_candidate() -> AccountCandidate:
    return AccountCandidate(
        platform="douyin",
        account_name="AI获客智能科技",
        profile_url="https://www.douyin.com/user/mock_ai_huoke",
        raw_data={
            "is_competitor": True,
            "icp_fit": 0,
            "pain_intensity": 0,
            "usage_frequency": 0,
            "existing_spend": 0,
            "customer_value": 0,
            "buy_vs_build": 0,
            "reachability": 0,
        },
    )


@pytest.fixture
def low_fit_candidate() -> AccountCandidate:
    return AccountCandidate(
        platform="douyin",
        account_name="服装工厂抖音直播",
        profile_url="https://www.douyin.com/user/mock_fuzhuang",
        raw_data={
            "icp_fit": 3,
            "pain_intensity": 4,
            "usage_frequency": 4,
            "existing_spend": 2,
            "customer_value": 2,
            "buy_vs_build": 2,
            "reachability": 3,
        },
    )


class TestBuyerScoring:
    """Tests for the BuyerScoringService."""

    def test_high_fit_scores_high(
        self, scoring_service: BuyerScoringService, high_fit_candidate: AccountCandidate
    ) -> None:
        """A high ICP fit candidate should score high."""
        score = scoring_service.score(high_fit_candidate)
        assert score.total >= 80
        assert score.icp_fit == 25
        assert score.pain_intensity == 20

    def test_competitor_scores_zero(
        self, scoring_service: BuyerScoringService, competitor_candidate: AccountCandidate
    ) -> None:
        """A competitor should score zero."""
        score = scoring_service.score(competitor_candidate)
        assert score.total == 0
        assert "竞品" in score.score_reason

    def test_low_fit_scores_low(
        self, scoring_service: BuyerScoringService, low_fit_candidate: AccountCandidate
    ) -> None:
        """A low-fit candidate should score low."""
        score = scoring_service.score(low_fit_candidate)
        assert score.total < 40

    def test_score_is_deterministic(
        self, scoring_service: BuyerScoringService, high_fit_candidate: AccountCandidate
    ) -> None:
        """Same candidate should produce same score every time."""
        score1 = scoring_service.score(high_fit_candidate)
        score2 = scoring_service.score(high_fit_candidate)
        assert score1.total == score2.total
        assert score1.icp_fit == score2.icp_fit
        assert score1.pain_intensity == score2.pain_intensity

    def test_total_equals_sum_of_dimensions(
        self, scoring_service: BuyerScoringService, high_fit_candidate: AccountCandidate
    ) -> None:
        """Total should equal the sum of all dimension scores."""
        score = scoring_service.score(high_fit_candidate)
        expected_total = (
            score.icp_fit
            + score.pain_intensity
            + score.usage_frequency
            + score.existing_spend
            + score.customer_value
            + score.buy_vs_build
            + score.reachability
        )
        assert score.total == expected_total

    def test_score_reason_not_empty(
        self, scoring_service: BuyerScoringService, high_fit_candidate: AccountCandidate
    ) -> None:
        """Score reason should be populated."""
        score = scoring_service.score(high_fit_candidate)
        assert len(score.score_reason) > 0

    def test_evidence_generation(
        self, scoring_service: BuyerScoringService, high_fit_candidate: AccountCandidate
    ) -> None:
        """Evidence should be generated for candidates with evidence in raw_data."""
        candidate = high_fit_candidate.model_copy()
        candidate.raw_data["evidence"] = [
            "明确提供B2B企业短视频代运营服务",
            "每日发布制造业短视频内容",
        ]
        evidence = scoring_service.generate_evidence(candidate)
        assert len(evidence) >= 2
        assert evidence[0].candidate_id == candidate.id

    def test_classify_level_s(self) -> None:
        """Score >= 90 should classify as S."""
        assert OpportunityLevel("S") == OpportunityLevel.S

    def test_classify_level_a(self) -> None:
        """Score 80-89 should classify as A."""
        from app.domain.opportunity.models import classify_level
        assert classify_level(85) == OpportunityLevel.A

    def test_classify_level_b(self) -> None:
        """Score 65-79 should classify as B."""
        from app.domain.opportunity.models import classify_level
        assert classify_level(70) == OpportunityLevel.B

    def test_classify_level_c(self) -> None:
        """Score < 65 should classify as C."""
        from app.domain.opportunity.models import classify_level
        assert classify_level(50) == OpportunityLevel.C
