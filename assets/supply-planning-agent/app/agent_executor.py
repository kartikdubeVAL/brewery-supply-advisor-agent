import logging
import sys
import os

from langchain_core.messages import SystemMessage
from langchain_core.messages.utils import count_tokens_approximately

from a2a.server.agent_execution import AgentExecutor as A2AAgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from agent import SampleAgent
from datetime_tool import get_datetime_tool
from load_skill_resources import get_load_skill_resource_tool
from mcp_providers.agw import get_mcp_tools
from prompt_injection_detector import wrap_tool

# Add app directory to path for peer-level imports
sys.path.insert(0, os.path.dirname(__file__))

logger = logging.getLogger(__name__)


def _load_workbook_at_startup():
    """Load the brewery Excel workbook at startup. Fail fast on error."""
    try:
        from workbook_loader import load_workbook, set_brewery_data
        data = load_workbook()
        set_brewery_data(data)
        logger.info(
            "M1.achieved: Excel workbook loaded — %d demand uplift rows, %d tanks, %d packaging lines",
            len(data.demand_uplifts),
            len(data.tanks),
            len(data.packaging_lines),
        )
    except Exception as exc:
        logger.error("M1.missed: Excel workbook could not be loaded — %s", exc)
        raise


# Load workbook once at module import time (agent startup)
_load_workbook_at_startup()


def _get_brewery_tools():
    """Return all brewery-specific LangChain tools."""
    from tools.query_demand_uplift import query_demand_uplift
    from tools.inspect_tank import inspect_tank
    from tools.check_coverage import check_coverage
    from tools.list_pending_tanks import list_pending_tanks
    from tools.list_demand_uplifts import list_demand_uplifts
    return [query_demand_uplift, inspect_tank, check_coverage, list_pending_tanks, list_demand_uplifts]


class AgentExecutor(A2AAgentExecutor):
    def __init__(self):
        self.agent = SampleAgent()
        self.skill_tools = [get_datetime_tool(), *get_load_skill_resource_tool()]
        self.brewery_tools = _get_brewery_tools()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the agent and stream results back via A2A protocol."""
        query = context.get_user_input()
        task = context.current_task
        if not task:
            assert context.message is not None, "Cannot create task without a message"
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        # Load MCP tools — user token is read from context var set by JWTContextMiddleware
        tools = []
        try:
            tools = await get_mcp_tools()
            if not tools:
                logger.warning("No MCP tools returned from Agent Gateway")
        except Exception as e:
            logger.error("Failed to load tools from Agent Gateway: %s", e)

        # Combine: MCP tools + brewery tools + skill tools
        tools = [*tools, *self.brewery_tools, *self.skill_tools]

        # Wrap all tools with prompt injection scanning
        tools = [wrap_tool(t) for t in tools]

        from agent import get_system_prompt
        _system_prompt = get_system_prompt()
        _msg_tokens = count_tokens_approximately([SystemMessage(content=_system_prompt)])
        _total_tokens = count_tokens_approximately([SystemMessage(content=_system_prompt)], tools=list(tools))
        logger.info(
            "Loaded %d tool(s); token estimate — prompt: %d, tools: %d, total: %d",
            len(tools), _msg_tokens, _total_tokens - _msg_tokens, _total_tokens,
        )

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            async for item in self.agent.stream(query, task.context_id, tools=tools):
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]
                content = item["content"]

                if require_user_input:
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(content, task.context_id, task.id),
                        final=True,
                    )
                    break
                elif is_task_complete:
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))], name="agent_result"
                    )
                    await updater.complete()
                    break
                else:
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(content, task.context_id, task.id),
                    )
        except Exception as e:
            logger.exception("Agent execution error")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
