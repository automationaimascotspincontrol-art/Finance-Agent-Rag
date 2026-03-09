from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    query: str
    plan: str
    research_data: str
    financial_analysis: str
    risk_score: str
    portfolio_allocation: str
    final_response: str

def planner_node(state: AgentState):
    from agents.planner_agent import run_planner_agent
    return run_planner_agent(state)

def research_node(state: AgentState):
    from agents.research_agent import run_research_agent
    return run_research_agent(state)

def financial_node(state: AgentState):
    from agents.financial_agent import run_financial_agent
    return run_financial_agent(state)

def risk_node(state: AgentState):
    from agents.risk_agent import run_risk_agent
    return run_risk_agent(state)

def portfolio_node(state: AgentState):
    from agents.portfolio_agent import run_portfolio_agent
    return run_portfolio_agent(state)

def final_node(state: AgentState):
    final = (f"**Plan:** {state.get('plan')}\n\n"
             f"**Research:** {state.get('research_data')}\n\n"
             f"**Analysis:** {state.get('financial_analysis')}\n\n"
             f"**Risk:** {state.get('risk_score')}\n\n"
             f"**Portfolio:** {state.get('portfolio_allocation')}")
    return {"final_response": final}

def get_finance_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("research", research_node)
    workflow.add_node("financial", financial_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("portfolio", portfolio_node)
    workflow.add_node("final", final_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "research")
    workflow.add_edge("research", "financial")
    workflow.add_edge("financial", "risk")
    workflow.add_edge("risk", "portfolio")
    workflow.add_edge("portfolio", "final")
    workflow.add_edge("final", END)
    
    return workflow.compile()
