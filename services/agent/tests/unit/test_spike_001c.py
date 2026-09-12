"""Unit tests for OR-SPIKE-001C Human-assisted Candidate Intake."""

from pathlib import Path

import pytest

from spikes.or_spike_001c.models import (
    IntakeQualityReport,
    NormalizedCandidate,
    RawCandidateInput,
)
from spikes.or_spike_001c.normalizer import (
    deduplicate_and_merge,
    normalize_candidate,
    normalize_row,
)
from spikes.or_spike_001c.validator import validate_row

# === Fixtures ===


@pytest.fixture
def valid_row() -> dict:
    """A valid input row."""
    return {
        "source_query": "短视频代运营",
        "account_name": "XX工业品营销",
        "profile_url": "https://www.douyin.com/user/xxxxx",
        "video_title": "专注制造业短视频代运营",
        "video_url": "https://www.douyin.com/video/xxxxx",
        "evidence_text": "专注制造业企业短视频代运营服务5年",
        "evidence_url": "https://www.douyin.com/user/xxxxx",
        "source_page_url": "https://www.douyin.com/search/短视频代运营",
        "captured_at": "2026-09-12T08:00:00+00:00",
        "human_note": "制造业代运营服务商",
    }


@pytest.fixture
def partial_row() -> dict:
    """A partial row (no profile_url, but has video_url)."""
    return {
        "source_query": "企业短视频获客",
        "account_name": "YY科技",
        "profile_url": "",
        "video_title": "B2B企业短视频获客方案",
        "video_url": "https://www.douyin.com/video/yyyyy",
        "evidence_text": "帮助企业通过短视频获取B2B客户",
        "evidence_url": "",
        "source_page_url": "https://www.douyin.com/search/企业短视频获客",
        "captured_at": "",
        "human_note": "",
    }


@pytest.fixture
def invalid_row() -> dict:
    """An invalid row (missing source_query)."""
    return {
        "source_query": "",
        "account_name": "NoQueryUser",
        "profile_url": "https://www.douyin.com/user/nquery",
        "video_title": "",
        "video_url": "",
        "evidence_text": "没有关键词",
        "evidence_url": "",
        "source_page_url": "https://www.douyin.com/search/xxx",
        "captured_at": "",
        "human_note": "",
    }


@pytest.fixture
def untraceable_row() -> dict:
    """An untraceable row (no object-level URL)."""
    return {
        "source_query": "测试关键词",
        "account_name": "SomeUser",
        "profile_url": "",
        "video_title": "",
        "video_url": "",
        "evidence_text": "没有对象级URL",
        "evidence_url": "",
        "source_page_url": "https://www.douyin.com/search/xxx",
        "captured_at": "",
        "human_note": "",
    }


# === Validator Tests ===


class TestValidator:
    """Test CSV row validation."""

    def test_valid_row_accepted(self, valid_row: dict) -> None:
        """A complete valid row should be accepted."""
        result = validate_row(valid_row)
        assert result["status"] == "valid"
        assert len(result["errors"]) == 0

    def test_valid_row_normalized(self, valid_row: dict) -> None:
        """Valid row should have normalized fields."""
        result = validate_row(valid_row)
        norm = result["normalized"]
        assert norm["source_query"] == "短视频代运营"
        assert norm["account_name"] == "XX工业品营销"
        assert norm["profile_url"] == "https://www.douyin.com/user/xxxxx"

    def test_partial_row_accepted(self, partial_row: dict) -> None:
        """A partial row (missing profile_url but has video_url) should be valid
        because video_url provides traceability."""
        result = validate_row(partial_row)
        assert result["status"] == "valid"

    def test_invalid_row_missing_query(self, invalid_row: dict) -> None:
        """A row missing source_query should be invalid."""
        result = validate_row(invalid_row)
        assert result["status"] == "invalid"
        assert any("source_query" in e for e in result["errors"])

    def test_untraceable_row(self, untraceable_row: dict) -> None:
        """A row with no object-level URL should be untraceable."""
        result = validate_row(untraceable_row)
        assert result["status"] == "untraceable"

    def test_invalid_url_rejected(self) -> None:
        """Invalid URLs should be rejected."""
        row = {
            "source_query": "test",
            "account_name": "Test",
            "profile_url": "not-a-valid-url",
            "video_url": "",
            "evidence_url": "",
            "source_page_url": "",
        }
        result = validate_row(row)
        assert result["status"] in ("partial", "untraceable")
        assert any("Invalid" in e for e in result["errors"])

    def test_whitespace_query_trimmed(self) -> None:
        """Whitespace in query should be trimmed."""
        row = {
            "source_query": "  test query  ",
            "account_name": "Test",
            "profile_url": "https://www.douyin.com/user/test",
        }
        result = validate_row(row)
        assert result["normalized"]["source_query"] == "test query"


# === Normalizer Tests ===


class TestNormalizer:
    """Test candidate normalization."""

    def test_normalize_preserves_query(self, valid_row: dict) -> None:
        """Normalization should preserve source_query."""
        validated = validate_row(valid_row)
        raw = normalize_row(validated)
        candidate = normalize_candidate(raw)
        assert candidate.source_query == "短视频代运营"

    def test_normalize_url_cleanup(self, valid_row: dict) -> None:
        """URLs should be normalized (tracking params removed)."""
        row = dict(valid_row)
        row["profile_url"] = "https://www.douyin.com/user/xxxxx?from_tab_name=main&utm_source=test"
        validated = validate_row(row)
        raw = normalize_row(validated)
        candidate = normalize_candidate(raw)
        assert "from_tab_name" not in (candidate.profile_url or "")
        assert "utm_source" not in (candidate.profile_url or "")

    def test_normalize_text_whitespace(self) -> None:
        """Text fields should have whitespace cleaned."""
        raw = RawCandidateInput(
            source_query="test",
            account_name="  Test   Name  ",
            evidence_text="  Some   evidence  text  ",
            collection_mode="human_assisted",
        )
        candidate = normalize_candidate(raw)
        assert candidate.account_name == "Test Name"
        assert candidate.evidence_text == "Some evidence text"

    def test_null_stays_null(self) -> None:
        """Missing fields should stay null, not be filled by AI."""
        raw = RawCandidateInput(
            source_query="test",
            account_name=None,
            profile_url=None,
            video_url=None,
            collection_mode="human_assisted",
        )
        candidate = normalize_candidate(raw)
        assert candidate.account_name is None
        assert candidate.profile_url is None
        assert candidate.video_url is None

    def test_collection_mode_is_human_assisted(self, valid_row: dict) -> None:
        """Collection mode should be human_assisted."""
        validated = validate_row(valid_row)
        raw = normalize_row(validated)
        candidate = normalize_candidate(raw)
        assert candidate.collection_mode == "human_assisted"

    def test_platform_is_douyin(self, valid_row: dict) -> None:
        """Platform should be douyin."""
        validated = validate_row(valid_row)
        raw = normalize_row(validated)
        candidate = normalize_candidate(raw)
        assert candidate.platform == "douyin"


# === Traceability Tests ===


class TestTraceability:
    """Test candidate traceability."""

    def test_profile_url_traceable(self) -> None:
        """Having profile_url makes candidate traceable."""
        raw = RawCandidateInput(
            source_query="test",
            profile_url="https://www.douyin.com/user/xxxxx",
            collection_mode="human_assisted",
        )
        candidate = normalize_candidate(raw)
        assert candidate.is_traceable is True
        assert candidate.traceability_source == "profile_url"

    def test_video_url_traceable(self) -> None:
        """Having video_url makes candidate traceable."""
        raw = RawCandidateInput(
            source_query="test",
            video_url="https://www.douyin.com/video/xxxxx",
            collection_mode="human_assisted",
        )
        candidate = normalize_candidate(raw)
        assert candidate.is_traceable is True
        assert candidate.traceability_source == "video_url"

    def test_evidence_url_traceable(self) -> None:
        """Having evidence_url makes candidate traceable."""
        raw = RawCandidateInput(
            source_query="test",
            evidence_url="https://www.douyin.com/user/yyyyy",
            collection_mode="human_assisted",
        )
        candidate = normalize_candidate(raw)
        assert candidate.is_traceable is True
        assert candidate.traceability_source == "evidence_url"

    def test_no_object_url_untraceable(self) -> None:
        """No object-level URL means untraceable."""
        raw = RawCandidateInput(
            source_query="test",
            source_page_url="https://www.douyin.com/search/test",
            collection_mode="human_assisted",
        )
        candidate = normalize_candidate(raw)
        assert candidate.is_traceable is False
        assert candidate.traceability_source is None


# === Dedup Tests ===


class TestDedup:
    """Test candidate deduplication."""

    def _make_candidate(
        self,
        id_: str,
        query: str,
        name: str,
        url: str | None,
    ) -> NormalizedCandidate:
        """Helper to create a properly normalized candidate."""
        raw = RawCandidateInput(
            id=id_,
            source_query=query,
            account_name=name,
            profile_url=url,
            collection_mode="human_assisted",
        )
        return normalize_candidate(raw)

    def test_same_profile_url_merges(self) -> None:
        """Same profile_url should merge into one candidate."""
        c1 = self._make_candidate("1", "query1", "Test", "https://www.douyin.com/user/xxxxx")
        c2 = self._make_candidate("2", "query2", "Test", "https://www.douyin.com/user/xxxxx")
        unique, dups, merged = deduplicate_and_merge([c1, c2])
        assert len(unique) == 1
        assert dups == 1
        assert merged == 1

    def test_source_queries_merged(self) -> None:
        """source_queries should be merged when deduplicating."""
        c1 = self._make_candidate("1", "query1", "Test", "https://www.douyin.com/user/xxxxx")
        c2 = self._make_candidate("2", "query2", "Test", "https://www.douyin.com/user/xxxxx")
        unique, _, _ = deduplicate_and_merge([c1, c2])
        assert set(unique[0].source_queries) == {"query1", "query2"}

    def test_different_urls_not_merged(self) -> None:
        """Different profile_urls should not merge."""
        c1 = self._make_candidate("1", "query1", "Test1", "https://www.douyin.com/user/xxxxx")
        c2 = self._make_candidate("2", "query2", "Test2", "https://www.douyin.com/user/yyyyy")
        unique, dups, merged = deduplicate_and_merge([c1, c2])
        assert len(unique) == 2
        assert dups == 0

    def test_name_based_fallback_dedup(self) -> None:
        """Same name without URL should use name-based fallback."""
        c1 = self._make_candidate("1", "query1", "TestUser", None)
        c2 = self._make_candidate("2", "query2", "TestUser", None)
        unique, dups, merged = deduplicate_and_merge([c1, c2])
        assert len(unique) == 1
        assert dups == 1


# === Report Tests ===


class TestReport:
    """Test intake quality report."""

    def test_traceable_rate_calculation(self) -> None:
        """Traceable rate should be calculated correctly."""
        report = IntakeQualityReport(
            rows_received=10,
            unique_candidates=8,
            traceable_candidates=7,
        )
        assert report.traceable_rate == 7 / 8

    def test_valid_rate_calculation(self) -> None:
        """Valid rate should be calculated correctly."""
        report = IntakeQualityReport(
            rows_received=10,
            valid_rows=6,
            partial_rows=2,
            invalid_rows=1,
            untraceable_rows=1,
        )
        assert report.valid_rate == 8 / 10

    def test_markdown_generation(self) -> None:
        """Report should generate markdown."""
        report = IntakeQualityReport(
            run_id="test-123",
            rows_received=10,
            unique_candidates=5,
        )
        md = report.to_markdown()
        assert "test-123" in md
        assert "10" in md
        assert "5" in md


# === Integration Test ===


class TestIntegration:
    """End-to-end integration test using fixtures."""

    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Test the full intake pipeline with a fixture CSV."""
        from spikes.or_spike_001c.run import run_intake

        # Create a temp CSV from fixture
        fixture_path = Path(__file__).parent.parent / "fixtures" / "candidate_intake_valid.csv"
        if not fixture_path.exists():
            pytest.skip("Fixture not found")

        output_dir = tmp_path / "runs"
        report = run_intake(str(fixture_path), str(output_dir))

        assert report.rows_received == 3
        assert report.valid_rows >= 1
        assert report.unique_candidates >= 1
        assert report.traceable_candidates >= 1

    def test_invalid_csv(self, tmp_path: Path) -> None:
        """Test intake with invalid rows."""
        from spikes.or_spike_001c.run import run_intake

        fixture_path = Path(__file__).parent.parent / "fixtures" / "candidate_intake_invalid.csv"
        if not fixture_path.exists():
            pytest.skip("Fixture not found")

        output_dir = tmp_path / "runs"
        report = run_intake(str(fixture_path), str(output_dir))

        assert report.rows_received == 3
        assert report.invalid_rows + report.untraceable_rows >= 1

    def test_duplicates_csv(self, tmp_path: Path) -> None:
        """Test intake with duplicate candidates."""
        from spikes.or_spike_001c.run import run_intake

        fixture_path = Path(__file__).parent.parent / "fixtures" / "candidate_intake_duplicates.csv"
        if not fixture_path.exists():
            pytest.skip("Fixture not found")

        output_dir = tmp_path / "runs"
        report = run_intake(str(fixture_path), str(output_dir))

        assert report.rows_received == 4
        assert report.unique_candidates < report.rows_received
        assert report.duplicate_rows >= 1
        assert report.cross_query_merged_candidates >= 1
