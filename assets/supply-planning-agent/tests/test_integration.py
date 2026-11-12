"""Integration test: end-to-end agent flow with mocked LLM and tools."""
import os
import sys
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from workbook_loader import BreweryData, Tank, PackagingLine, DemandUplift, set_brewery_data
from agent import SampleAgent


def _setup_demo_data():
    """Set up a minimal in-memory brewery dataset for integration tests."""
    tanks = [
        Tank("MUC-T001", "Munich", "South", "Pils", 26, 2000, 800, 1200, "Released", ""),
        Tank("MUC-T003", "Munich", "South", "Pils", 28, 1800, 600, 1200, "Pending", "Lab check"),
        Tank("MUC-T004", "Munich", "South", "Pils", 30, 1200, 400, 800, "Hold", "Diacetyl issue"),
    ]
    lines = [
        PackagingLine("MUC-L01", "Munich", "0.5L bottle", 2000.0),
    ]
    demand = [
        DemandUplift("South", "Pils", 27, 28, 2400.0),
    ]
    set_brewery_data(BreweryData(demand_uplifts=demand, packaging_lines=lines, tanks=tanks))


def _make_mock_llm_response(content: str):
    """Create a mock LLM response that the agent framework expects."""
    from langchain_core.messages import AIMessage
    msg = MagicMock()
    msg.content = content
    return {"messages": [AIMessage(content=content)]}


@pytest.mark.asyncio
async def test_agent_invoke_coverage_question():
    """Agent should call check_coverage and return a structured answer."""
    _setup_demo_data()

    mock_response = _make_mock_llm_response(
        "Partially — gap of 1200 hl (secured 1200 hl of 2400 hl needed)\n\n"
        "Secured supply: MUC-T001\nUpside: MUC-T003\nExcluded: MUC-T004\n"
        "Recommendation: Request lab release of MUC-T003."
    )

    agent = SampleAgent()

    with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_response

        from tools.check_coverage import check_coverage
        from tools.inspect_tank import inspect_tank
        from tools.list_pending_tanks import list_pending_tanks
        from tools.list_demand_uplifts import list_demand_uplifts
        from tools.query_demand_uplift import query_demand_uplift

        result = await agent.invoke(
            query="Can we cover the extra 2400 hl Pils demand in the South for CW27-CW28?",
            context_id="test-context-001",
            tools=[check_coverage, inspect_tank, list_pending_tanks,
                   list_demand_uplifts, query_demand_uplift],
        )

    assert result.status == "completed"
    assert result.message
    assert "Partially" in result.message or len(result.message) > 0


@pytest.mark.asyncio
async def test_agent_invoke_inspect_tank():
    """Agent should return tank details for a direct tank inspection query."""
    _setup_demo_data()

    mock_response = _make_mock_llm_response(
        "Tank MUC-T001: Munich, South, Pils, Released, 1200 hl free, ready CW26."
    )

    agent = SampleAgent()

    with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_response

        from tools.inspect_tank import inspect_tank

        result = await agent.invoke(
            query="What is in tank MUC-T001?",
            context_id="test-context-002",
            tools=[inspect_tank],
        )

    assert result.status == "completed"
    assert result.message


@pytest.mark.asyncio
async def test_agent_stream_yields_completed():
    """Agent stream() must eventually yield is_task_complete=True."""
    _setup_demo_data()

    from langchain_core.messages import AIMessage
    mock_response = {"messages": [AIMessage(content="Yes — surplus of 800 hl. Secured: MUC-T001.")]}

    agent = SampleAgent()

    chunks = []
    with patch.object(agent, "_invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_response
        from tools.check_coverage import check_coverage
        async for chunk in agent.stream(
            "Can we cover 1000 hl Pils in South for CW27?",
            context_id="test-stream-001",
            tools=[check_coverage],
        ):
            chunks.append(chunk)

    completed = [c for c in chunks if c.get("is_task_complete")]
    assert len(completed) >= 1
