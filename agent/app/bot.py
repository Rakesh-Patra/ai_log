# WHY THIS EXISTS:
# Sentinel-Ops is the 'brain' of the autonomous SRE system. 
# Using LangGraph allows us to define a state-driven workflow where the
# agent can loop between observing (tools) and acting (remediation).
# This replaces manual on-call triage for known patterns like OOMKills
# or idle resource waste.

import os
from typing import TypedDict, Annotated, List, Union
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from agent.app.tools import (
    query_loki_logs,
    get_k8s_events,
    get_namespace_utilization,
    execute_k8s_action,
    get_kubecost_metrics,
)

# Define the state of the graph
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]

# Initialize Tools and Model
tools = [query_loki_logs, get_k8s_events, get_namespace_utilization, execute_k8s_action, get_kubecost_metrics]
tool_executor = ToolExecutor(tools)

# Model Selection (Default to Gemini but can be swapped)
model = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

SYSTEM_PROMPT = """
You are Sentinel-Ops, an autonomous L3 SRE and FinOps Engineer. 
Your mission is to maintain cluster health and optimize cloud spend.

SRE OPERATING LOGIC:
1. When triggered by an error alert (e.g., CrashLoopBackOff, OOMKill):
   - GATHER context using `get_k8s_events` and `query_loki_logs`.
   - DIAGNOSE the root cause (e.g., memory leak, missing config).
   - ACT safely. If it's a known transient issue, you can `rollout restart`. If it's an OOMKill, report it for human limit adjustment.
   - REPORT your findings and actions clearly.

FINOPS OPERATING LOGIC:
1. When triggered by a Budget Breach or Idle Resource alert:
   - CHECK financial impact using `get_kubecost_metrics`.
   - CHECK utilization using `get_namespace_utilization`.
   - EVALUATE: If the cost is significant but utilization is near zero (idle), the namespace is wasting money.
   - ACT: Scale non-critical deployments to 0 using `execute_k8s_action`.
   - REPORT: "Scaled down {namespace} saving approximately ${X}/month according to Kubecost."


SECURITY GUARDRAILS:
- Never attempt to delete resources.
- Never scale or restart anything in `kube-system`, `vault`, or `monitoring`.
- Always verify the namespace utilization before scaling down.
"""

def call_model(state):
    messages = state['messages']
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    # We bind tools here
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def call_tool(state):
    messages = state['messages']
    last_message = messages[-1]
    
    tool_invocations = []
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            action = ToolInvocation(
                tool=tool_call["name"],
                tool_input=tool_call["args"],
            )
            tool_invocations.append(action)
            
    responses = []
    for invocation in tool_invocations:
        response = tool_executor.invoke(invocation)
        responses.append(ToolMessage(content=str(response), tool_call_id=last_message.tool_calls[0]['id'])) # Simplified for 1 tool call
        
    return {"messages": responses}

def should_continue(state):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "continue"
    return "end"

# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("sentinel", call_model)
workflow.add_node("action", call_tool)

workflow.set_entry_point("sentinel")

workflow.add_conditional_edges(
    "sentinel",
    should_continue,
    {
        "continue": "action",
        "end": END
    }
)

workflow.add_edge("action", "sentinel")

# Compile the app
sentinel_app = workflow.compile()
