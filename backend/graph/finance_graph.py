from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    query: str
    plan: str
    research_data: str
    financial_analysis: str
    risk_score: str
    quant_analysis: str
    quant_data: dict
    portfolio_allocation: str
    portfolio_data: dict
    quant_error: bool
    error_message: str
    monte_carlo_results: dict
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

def quant_node(state: AgentState):
    from agents.quant_agent import run_quant_agent
    return run_quant_agent(state)

def portfolio_node(state: AgentState):
    from agents.portfolio_agent import run_portfolio_agent
    return run_portfolio_agent(state)

def final_node(state: AgentState):
    if state.get("quant_error"):
        final = (f"**⚠️ DATA GROUNDING ERROR:**\n{state.get('error_message')}\n\n"
                 f"**1. Action Plan:**\n{state.get('plan')}\n\n"
                 f"**2. Research & Context:**\n{state.get('research_data')}\n\n"
                 f"**Note:** Quantitative Analysis, Financial Analysis, Risk, and Portfolio segments were skipped due to missing/unresolved market data.")
    else:
        final = (f"**1. Action Plan:**\n{state.get('plan')}\n\n"
                 f"**2. Research & Context:**\n{state.get('research_data')}\n\n"
                 f"**3. Quant Metrics:**\n{state.get('quant_analysis')}\n\n"
                 f"**4. Financial Analysis:**\n{state.get('financial_analysis')}\n\n"
                 f"**5. Risk Assessment:**\n{state.get('risk_score')}\n\n"
                 f"**6. Optimized Portfolio:**\n{state.get('portfolio_allocation')}\n\n"
                 f"---\n"
                 f"### 📊 Technical Data Appendix (Institutional Grade)\n")
        
        # Append signal scores and quant raw data
        quant_data = state.get("quant_data", {})
        if quant_data:
            final += f"\n**Signal Scores & Factors:**\n`{json.dumps(quant_data.get('signal_scores', {}), indent=2)}`"
            
        # Append Monte Carlo Results
        mc = state.get("monte_carlo_results", {})
        if mc:
            final += f"\n\n**10k Monte Carlo Simulation Results:**\n`{json.dumps(mc, indent=2)}`"
            
        # Append Portfolio Weights
        weights = state.get("portfolio_data", {})
        if weights:
            final += f"\n\n**Optimized Weights:**\n`{json.dumps(weights, indent=2)}`"
            
    return {"final_response": final}

def get_finance_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("research", research_node)
    workflow.add_node("quant", quant_node)
    workflow.add_node("financial", financial_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("portfolio", portfolio_node)
    workflow.add_node("final", final_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "research")
    workflow.add_edge("research", "quant")
    workflow.add_edge("quant", "financial")
    workflow.add_edge("financial", "risk")
    workflow.add_edge("risk", "portfolio")
    workflow.add_edge("portfolio", "final")
    workflow.add_edge("final", END)
    
    return workflow.compile()
