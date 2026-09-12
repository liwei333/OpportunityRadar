"""Mock Planner — generates search queries from a research goal.

V0 implementation uses a predefined query set.
Future: LLM-powered planner that dynamically generates queries
based on the user's goal and discovered concepts.
"""

from ...domain.research.models import QueryType, ResearchTask, SearchQuery

# Predefined search queries organized by type
DEFAULT_QUERIES: list[tuple[str, QueryType, str]] = [
    # Direct business queries
    ("企业短视频获客", QueryType.DIRECT, "核心业务词：企业通过短视频获取客户"),
    ("短视频代运营", QueryType.DIRECT, "核心业务词：短视频代运营服务"),
    ("B2B短视频", QueryType.DIRECT, "核心业务词：B2B领域短视频"),
    ("工业品短视频", QueryType.DIRECT, "核心业务词：工业品行业短视频"),
    ("制造业短视频运营", QueryType.DIRECT, "核心业务词：制造业短视频运营"),
    # Pain point queries
    ("企业短视频怎么获客", QueryType.PAIN, "问题词：企业短视频获客方法"),
    ("工业品怎么做抖音", QueryType.PAIN, "问题词：工业品抖音运营方法"),
    ("ToB短视频怎么找客户", QueryType.PAIN, "问题词：ToB短视频客户获取"),
    ("短视频精准获客", QueryType.PAIN, "问题词：短视频精准获客策略"),
    # Scenario queries
    ("制造业抖音运营", QueryType.SCENARIO, "场景词：制造业抖音运营"),
    ("机械设备短视频", QueryType.SCENARIO, "场景词：机械设备短视频内容"),
    ("工厂短视频运营", QueryType.SCENARIO, "场景词：工厂短视频运营"),
    ("企业账号矩阵", QueryType.SCENARIO, "场景词：企业抖音账号矩阵"),
    # Expanded queries
    ("短视频营销服务商", QueryType.EXPANDED, "扩展词：短视频营销服务公司"),
    ("工业自动化抖音", QueryType.EXPANDED, "扩展词：工业自动化行业抖音"),
    ("建材企业短视频", QueryType.EXPANDED, "扩展词：建材企业短视频服务"),
    ("医疗器械短视频代运营", QueryType.EXPANDED, "扩展词：医疗器械短视频"),
]


class MockPlanner:
    """Generates search queries for a research task.

    V0: returns a fixed set of queries.
    Future: LLM-generated queries based on goal analysis.
    """

    def plan(self, task: ResearchTask) -> list[SearchQuery]:
        """Generate search queries for the research task.

        Args:
            task: The research task to plan for.

        Returns:
            List of SearchQuery objects ready for collection.
        """
        queries: list[SearchQuery] = []
        for query_text, query_type, reason in DEFAULT_QUERIES:
            queries.append(
                SearchQuery(
                    research_task_id=task.id,
                    query=query_text,
                    query_type=query_type,
                    reason=reason,
                )
            )
        return queries
