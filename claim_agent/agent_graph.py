from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from .data_models import (
    CheckResult,
    PatientRecord,
    PolicyDocument,
)
from .prompts import SYSTEM_PROMPT
from .tools import build_record_summaries, check_claim_coverage, find_policy_summaries


class AgentState(BaseModel):
    record: PatientRecord
    policy: PolicyDocument
    outputs: List[str] = []


def create_graph(model):
    # Bind tools
    tools = [build_record_summaries, find_policy_summaries, check_claim_coverage]
    llm = model.bind_tools(tools)  # type: ignore[attr-defined]

    graph = StateGraph(AgentState)

    def call_model(state: AgentState):
        msgs = [SystemMessage(content=SYSTEM_PROMPT)]
        msgs.append(
            HumanMessage(
                content=(
                    "Generate decisions using tools for this record and policy. "
                    "Return only the final Decision and Reason."
                )
            )
        )
        response = llm.invoke(msgs)  # LLM will decide tool usage via ReAct
        return {"outputs": [response.content] if isinstance(response.content, str) else [str(response.content)]}

    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools=tools))

    def route(state: AgentState):
        # If the LLM requested tools, ToolNode will handle; else end.
        return "tools"

    graph.set_entry_point("agent")
    graph.add_edge("agent", "tools")
    graph.add_edge("tools", END)

    return graph.compile()
