"""Integration tests for the API endpoints."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.infrastructure.database import Base, async_engine
from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Create an async test client with a fresh database."""
    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """GET /api/health should return status ok."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "opportunity-radar-agent"


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient) -> None:
    """POST /api/research/tasks should create a new task."""
    response = await client.post(
        "/api/research/tasks",
        json={"goal": "帮我寻找最可能购买 OpportunityRadar 的客户"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_create_task_validation(client: AsyncClient) -> None:
    """POST /api/research/tasks should reject too-short goals."""
    response = await client.post(
        "/api/research/tasks",
        json={"goal": "短"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient) -> None:
    """GET /api/research/tasks/{id} should return task details."""
    # Create task first
    create_resp = await client.post(
        "/api/research/tasks",
        json={"goal": "测试研究任务"},
    )
    task_id = create_resp.json()["task_id"]

    # Get task
    response = await client.get(f"/api/research/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["goal"] == "测试研究任务"


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient) -> None:
    """GET /api/research/tasks/{id} should return 404 for unknown task."""
    response = await client.get("/api/research/tasks/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_run_task_and_get_opportunities(client: AsyncClient) -> None:
    """Full pipeline: create → run → get opportunities."""
    # Create task
    create_resp = await client.post(
        "/api/research/tasks",
        json={"goal": "帮我寻找最可能购买 OpportunityRadar 的客户"},
    )
    task_id = create_resp.json()["task_id"]

    # Run task
    run_resp = await client.post(f"/api/research/tasks/{task_id}/run")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["queries_generated"] > 0
    assert run_data["candidates_collected"] > 0
    assert run_data["opportunities_found"] > 0

    # Get task status
    task_resp = await client.get(f"/api/research/tasks/{task_id}")
    assert task_resp.status_code == 200
    assert task_resp.json()["status"] == "COMPLETED"

    # Get opportunities
    opp_resp = await client.get(f"/api/research/tasks/{task_id}/opportunities")
    assert opp_resp.status_code == 200
    opp_data = opp_resp.json()
    assert opp_data["total"] > 0
    assert len(opp_data["opportunities"]) > 0

    # Verify sorted by total_score descending
    scores = [o["total_score"] for o in opp_data["opportunities"]]
    assert scores == sorted(scores, reverse=True)

    # Verify first opportunity has required fields
    top = opp_data["opportunities"][0]
    assert "account_name" in top
    assert "level" in top
    assert "buyer_score" in top
    assert "evidence" in top


@pytest.mark.asyncio
async def test_get_opportunities_not_found(client: AsyncClient) -> None:
    """GET opportunities for nonexistent task should return 404."""
    response = await client.get("/api/research/tasks/fake-id/opportunities")
    assert response.status_code == 404
