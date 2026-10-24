"""
autonomous_agent.py
-------------------
LangChain agent for the POST /agent autonomous manager endpoint.

Architecture (two-phase)
────────────────────────
Phase 1 — Data collection  (LangChain agent with MCP tools only)
  The agent receives the manager's request, autonomously decides which MCP
  data tools to call (get_order_stats_tool, get_top_items_tool, etc.), and
  returns once all tool results are collected.  generate_document_tool is NOT
  in this agent's tool list — keeping the output small and preventing
  MAX_TOKENS on the reasoning budget.

Phase 2 — Document composition  (direct LLM call + document_generator)
  run() extracts every ToolMessage result from the agent's message history,
  then makes a single focused LLM call asking the model to produce a compact
  JSON section list from the collected data.  document_generator.generate_document()
  builds and saves the .docx from those sections.

This split means no single LLM call has to produce a large JSON blob while
simultaneously reasoning about tool orchestration — each call has one job.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware, SummarizationMiddleware
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from agents.autonomous_prompt import AutonomousPrompt
from models.model import AgentResponse, TaskItem
from utilities.document_generator import generate_document
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode
from utilities.logger import get_logger

logger = get_logger(__name__)


# ── document type inference ───────────────────────────────────────────────────

_DOC_TYPE_KEYWORDS: list[tuple[list[str], str]] = [
    (["sales", "revenue", "income"],                        "sales_report"),
    (["menu proposal", "expand", "new item", "new drink"],  "menu_proposal"),
    (["menu review", "menu analysis", "item performance"],  "menu_review"),
    (["meeting", "minutes", "agenda"],                      "meeting_minutes"),
    (["sop", "procedure", "policy", "process", "handling"], "sop"),
    (["performance", "overview", "shop report"],            "performance_report"),
]

def _infer_doc_type(request: str) -> str:
    lower = request.lower()
    for keywords, doc_type in _DOC_TYPE_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return doc_type
    return "performance_report"

def _infer_doc_title(request: str, doc_type: str) -> str:
    titles = {
        "sales_report":       "Sales Report – Brew Buddy Coffee Shop",
        "menu_proposal":      "Menu Expansion Proposal – Brew Buddy Coffee Shop",
        "menu_review":        "Menu Review Report – Brew Buddy Coffee Shop",
        "meeting_minutes":    "Meeting Minutes – Brew Buddy Coffee Shop",
        "sop":                "Standard Operating Procedure – Brew Buddy Coffee Shop",
        "performance_report": "Shop Performance Report – Brew Buddy Coffee Shop",
    }
    return titles.get(doc_type, "Business Report – Brew Buddy Coffee Shop")


# ── agent class ───────────────────────────────────────────────────────────────

class ManagerAgent:
    """
    Two-phase autonomous manager agent.

    Phase 1: LangChain agent collects data via MCP tools.
    Phase 2: A direct LLM call composes document sections; generate_document saves the .docx.
    """

    def __init__(self, data_agent, composition_model, mcp_client) -> None:
        self._data_agent       = data_agent        # compiled LangChain agent (data-only tools)
        self._composition_model = composition_model # LLM used for section composition
        self._mcp_client       = mcp_client

    # ── factory ───────────────────────────────────────────────────────────────

    @classmethod
    async def create(cls, model, summary_model, composition_model, mcp_client):
        """
        Build and return a ManagerAgent.

        Parameters
        ----------
        model             : LLM for the data-collection agent (moderate tokens).
        summary_model     : LLM for SummarizationMiddleware (small).
        composition_model : LLM for document section composition (high tokens).
        mcp_client        : MultiServerMCPClient to fetch MCP tools.
        """
        logger.info("Fetching MCP tools for manager agent")
        mcp_tools = await mcp_client.get_tools()
        # Expose only the manager data tools — not customer-facing tools,
        # and NOT generate_document_tool (that runs outside the agent).
        manager_tool_names = {
            "get_menu_tool",
            "get_shop_details_tool",
            "get_all_orders_tool",
            "get_top_items_tool",
            "get_order_stats_tool",
        }
        data_tools = [t for t in mcp_tools if t.name in manager_tool_names]
        logger.info("Manager data tool list: %s", [t.name for t in data_tools])

        prompt = AutonomousPrompt()
        compiled = create_agent(
            model=model,
            tools=data_tools,
            middleware=[
                SummarizationMiddleware(
                    model=summary_model,
                    trigger=("fraction", 0.2),
                    keep=("messages", 2),
                    system_prompt=prompt.summary_system_prompt(),
                ),
                PIIMiddleware(
                    "email",
                    strategy="redact",
                    apply_to_input=True,
                    apply_to_output=True,
                ),
            ],
            system_prompt=prompt.get_data_collection_prompt(),
            checkpointer=None,
        )
        logger.info("Manager data-collection agent compiled successfully")
        return cls(compiled, composition_model, mcp_client)

    # ── runner ────────────────────────────────────────────────────────────────

    async def run(self, request: str) -> AgentResponse:
        try:
            logger.info("ManagerAgent: phase 1 — data collection")

            # ── Phase 1: agent collects data ──────────────────────────────
            result = await self._data_agent.ainvoke(
                {"messages": [("user", request)]}
            )
            logger.info("Phase 1 result keys: %s", list(result.keys()) if isinstance(result, dict) else type(result))
            messages: list = result.get("messages", [])
            logger.info("Phase 1 message count: %d  types: %s",
                len(messages),
                [type(m).__name__ for m in messages]
            )
            task_list: list[TaskItem] = []
            step = 1
            for msg in messages:
                if not isinstance(msg, AIMessage):
                    continue
                for tc in (getattr(msg, "tool_calls", None) or []):
                    name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "")
                    task_list.append(TaskItem(
                        step=step,
                        description=_describe_tool_call(tc),
                        tool=name,
                        status="completed",
                    ))
                    step += 1

            # Aggregate all ToolMessage results into one dict keyed by tool name
            tool_results: dict[str, str] = {}
            for msg in messages:
                if not isinstance(msg, ToolMessage):
                    continue
                tool_name = getattr(msg, "name", "unknown")
                raw = msg.content
                if isinstance(raw, list):
                    # Gemini wraps content in a list of dicts
                    tool_results[tool_name] = " ".join(
                        block.get("text", "") for block in raw
                        if isinstance(block, dict)
                    )
                else:
                    tool_results[tool_name] = str(raw)

            logger.info("Phase 1 done — tools called: %s", list(tool_results.keys()))

            # ── Out-of-scope guard ────────────────────────────────────────
            # If the agent called no tools, check whether it signalled
            # OUT_OF_SCOPE in its final message.
            if not tool_results:
                rejection_text = _extract_summary(messages)
                logger.info("No tools called — checking for OUT_OF_SCOPE signal")
                if "OUT_OF_SCOPE" in rejection_text or not rejection_text:
                    # Strip the sentinel prefix for the user-facing message
                    clean_message = (
                        rejection_text
                        .replace("OUT_OF_SCOPE:", "")
                        .strip()
                    ) or (
                        "I can only assist with Brew Buddy Coffee Shop management "
                        "tasks such as sales reports, menu analysis, SOPs, and "
                        "performance reports. Your request appears to be outside "
                        "my scope."
                    )
                    logger.info("Request rejected as out of scope")
                    return AgentResponse(
                        task_list=[],
                        assumptions=[],
                        summary=clean_message,
                        document_filename="",
                    )

            # ── Phase 2: compose document sections ────────────────────────
            doc_type  = _infer_doc_type(request)
            doc_title = _infer_doc_title(request, doc_type)
            logger.info("ManagerAgent: phase 2 — document composition (doc_type=%s)", doc_type)

            prompt = AutonomousPrompt()
            system_msg = SystemMessage(content=prompt.get_composition_prompt(doc_type))
            user_msg = HumanMessage(content=(
                f"Manager request: {request}\n\n"
                f"Document type: {doc_type}\n"
                f"Document title: {doc_title}\n\n"
                f"Collected data:\n"
                + "\n\n".join(
                    f"[{name}]\n{data}"
                    for name, data in tool_results.items()
                )
            ))
            composition_response = await self._composition_model.ainvoke(
                [system_msg, user_msg]
            )
            logger.info("Phase 2 composition done — finish_reason: %s tokens: %s",
                composition_response.response_metadata.get("finish_reason"),
                composition_response.usage_metadata,
            )

            # Parse sections JSON from composition response
            raw_content = composition_response.content
            if isinstance(raw_content, list):
                raw_text = " ".join(
                    b.get("text", "") for b in raw_content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            else:
                raw_text = str(raw_content)

            sections = _parse_sections_json(raw_text)
            logger.info("Sections parsed: %d sections", len(sections))

            # ── Phase 3: generate document ────────────────────────────────
            logger.info("ManagerAgent: phase 3 — generating document")
            filename = generate_document(
                title=doc_title,
                document_type=doc_type,
                sections=sections,
                metadata={
                    "generated_by": "Autonomous Manager Agent",
                    "date": datetime.now().strftime("%B %d, %Y"),
                },
            )

            # Add document generation as final task
            task_list.append(TaskItem(
                step=step,
                description="Generated Word (.docx) document",
                tool="generate_document_tool",
                status="completed",
            ))

            # Summary = last non-empty AIMessage text from phase 1
            summary = _extract_summary(messages) or (
                f"{doc_title} has been generated successfully. "
                f"The report covers {len(tool_results)} data source(s) "
                f"and is saved as {filename}."
            )

            logger.info("ManagerAgent: completed — doc=%s", filename)
            return AgentResponse(
                task_list=task_list,
                assumptions=[],
                summary=summary,
                document_filename=filename,
            )

        except Custom_Exception:
            raise
        except Exception as exc:
            logger.exception("ManagerAgent: execution failed — %s", exc)
            raise Custom_Exception(
                "The manager agent could not complete the request.",
                ErrorCode.INTERNAL_SERVER_ERROR,
                HttpStatusCode.INTERNAL_SERVER_ERROR,
            )


# ── helpers ───────────────────────────────────────────────────────────────────

_TOOL_DESCRIPTIONS = {
    "get_menu_tool":          "Fetched menu catalog from the coffee shop database",
    "get_shop_details_tool":  "Retrieved coffee shop details (name, location, contact)",
    "get_all_orders_tool":    "Fetched all orders across customers for analysis",
    "get_top_items_tool":     "Calculated top-selling items by units sold and revenue",
    "get_order_stats_tool":   "Computed aggregate order statistics (revenue, counts, status breakdown)",
    "generate_document_tool": "Generated Word (.docx) document",
}


def _describe_tool_call(tc) -> str:
    name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "")
    return _TOOL_DESCRIPTIONS.get(name, f"Called tool: {name}")


def _parse_sections_json(text: str) -> list[dict]:
    """Extract and parse the JSON array from the LLM composition response."""
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    # Find the first [ ... ] block
    start = cleaned.find("[")
    end   = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(cleaned[start:end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError as exc:
            logger.warning("Section JSON parse failed: %s", exc)
    # Fallback: wrap the raw text as a single content section
    logger.warning("Could not parse sections JSON — using raw text as content")
    return [{"heading": "Report", "content": cleaned[:2000]}]


def _extract_summary(messages: list) -> str:
    """Return the last AIMessage text that has no pending tool calls."""
    for msg in reversed(messages):
        if not isinstance(msg, AIMessage):
            continue
        if getattr(msg, "tool_calls", None):
            continue
        content = msg.content or ""
        if isinstance(content, list):
            text = " ".join(
                b.get("text", "") for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            ).strip()
        else:
            text = str(content).strip()
        if text:
            return text
    return ""
