"""Buyer Scoring Service.

V0 uses deterministic scoring based on pre-defined candidate attributes.
This avoids random.randint() and ensures reproducible results.

The interface is designed to allow future replacement with:
- Rules engine
- LLM-powered intelligence
- Evidence-based reasoning

LLM may never modify raw facts — only interpret them.
"""

from ...domain.evidence.models import Evidence, EvidenceType
from ...domain.opportunity.models import AccountCandidate
from ...domain.scoring.models import BuyerScore

# V0 scoring weights (must sum to 100)
WEIGHTS = {
    "icp_fit": 25,
    "pain_intensity": 20,
    "usage_frequency": 15,
    "existing_spend": 15,
    "customer_value": 10,
    "buy_vs_build": 10,
    "reachability": 5,
}


class BuyerScoringService:
    """Score account candidates on the V0 seven-dimension model.

    V0 implementation: deterministic scoring from raw_data attributes.
    Future: rules + LLM + evidence pipeline.
    """

    def score(self, candidate: AccountCandidate) -> BuyerScore:
        """Calculate buyer score for a candidate.

        Uses pre-defined dimension values from candidate.raw_data
        to ensure reproducible, deterministic scoring.

        Args:
            candidate: The account candidate to score.

        Returns:
            Populated BuyerScore with all dimensions and total.
        """
        raw = candidate.raw_data

        # Check for competitor flag
        if raw.get("is_competitor", False):
            return BuyerScore(
                candidate_id=candidate.id,
                icp_fit=0,
                pain_intensity=0,
                usage_frequency=0,
                existing_spend=0,
                customer_value=0,
                buy_vs_build=0,
                reachability=0,
                total=0,
                score_reason="竞品，不进入推荐列表",
                risk="已经是同类产品的提供者",
                confidence=0.95,
            )

        # Extract dimension scores from raw data (deterministic)
        icp_fit = min(raw.get("icp_fit", 0), WEIGHTS["icp_fit"])
        pain_intensity = min(raw.get("pain_intensity", 0), WEIGHTS["pain_intensity"])
        usage_frequency = min(raw.get("usage_frequency", 0), WEIGHTS["usage_frequency"])
        existing_spend = min(raw.get("existing_spend", 0), WEIGHTS["existing_spend"])
        customer_value = min(raw.get("customer_value", 0), WEIGHTS["customer_value"])
        buy_vs_build = min(raw.get("buy_vs_build", 0), WEIGHTS["buy_vs_build"])
        reachability = min(raw.get("reachability", 0), WEIGHTS["reachability"])

        total = (
            icp_fit
            + pain_intensity
            + usage_frequency
            + existing_spend
            + customer_value
            + buy_vs_build
            + reachability
        )

        # Build score reason from top dimensions
        score_reason = self._build_reason(
            icp_fit, pain_intensity, usage_frequency,
            existing_spend, customer_value, buy_vs_build,
            candidate.account_name,
        )

        risk = self._assess_risk(raw, total)

        return BuyerScore(
            candidate_id=candidate.id,
            icp_fit=icp_fit,
            pain_intensity=pain_intensity,
            usage_frequency=usage_frequency,
            existing_spend=existing_spend,
            customer_value=customer_value,
            buy_vs_build=buy_vs_build,
            reachability=reachability,
            total=total,
            score_reason=score_reason,
            risk=risk,
            confidence=0.85 if total > 60 else 0.7,
        )

    def generate_evidence(self, candidate: AccountCandidate) -> list[Evidence]:
        """Generate evidence list for a candidate.

        In V0, evidence comes from pre-defined raw_data.
        Future: LLM-generated evidence from actual content analysis.
        """
        raw = candidate.raw_data
        evidence_items: list[Evidence] = []

        for text in raw.get("evidence", []):
            evidence_type = EvidenceType.ICP_FIT
            text_lower = text.lower()
            if "获客" in text_lower or "线索" in text_lower:
                evidence_type = EvidenceType.PAIN_SIGNAL
            elif "研究" in text_lower or "调研" in text_lower:
                evidence_type = EvidenceType.USAGE_FREQUENCY
            elif "客户" in text_lower and ("服务" in text_lower or "合作" in text_lower):
                evidence_type = EvidenceType.CUSTOMER_VALUE
            elif "工具" in text_lower or "预算" in text_lower or "投入" in text_lower:
                evidence_type = EvidenceType.EXISTING_SPEND
            elif "竞品" in text_lower:
                evidence_type = EvidenceType.COMPETITOR

            evidence_items.append(
                Evidence(
                    candidate_id=candidate.id,
                    evidence_type=evidence_type,
                    evidence_text=text,
                    source_url=candidate.profile_url,
                    confidence=0.8,
                )
            )

        return evidence_items

    def _build_reason(
        self,
        icp_fit: int,
        pain_intensity: int,
        usage_frequency: int,
        existing_spend: int,
        customer_value: int,
        buy_vs_build: int,
        account_name: str,
    ) -> str:
        """Build a human-readable scoring reason."""
        reasons: list[str] = []
        if icp_fit >= 20:
            reasons.append("高度符合ICP")
        elif icp_fit >= 10:
            reasons.append("部分符合ICP")

        if pain_intensity >= 15:
            reasons.append("获客需求强烈")
        if usage_frequency >= 12:
            reasons.append("高频内容产出需求")
        if existing_spend >= 10:
            reasons.append("已有营销投入信号")
        if customer_value >= 7:
            reasons.append("服务企业客户，价值高")
        if buy_vs_build >= 8:
            reasons.append("更可能采购而非自研")

        if not reasons:
            reasons.append("匹配度一般")

        return f"{account_name}：{'，'.join(reasons)}"

    def _assess_risk(self, raw: dict, total: int) -> str:
        """Assess risk factors for a candidate."""
        risks: list[str] = []
        if raw.get("is_competitor"):
            risks.append("竞品")
        if raw.get("business_type", "").startswith("large"):
            risks.append("规模大，可能自研")
        if raw.get("business_type", "").startswith("tiny") or raw.get("business_type", "").startswith("side"):
            risks.append("规模小，预算有限")
        if raw.get("business_type", "").startswith("manufacturer") and "self" in raw.get("business_type", ""):
            risks.append("制造商自用，非服务商")

        if not risks:
            if total >= 80:
                return "低风险，优先联系"
            return "中等风险，建议联系"

        return "；".join(risks)
