# langgraph_agent.py
from typing_extensions import TypedDict
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from retriever_chain import load_chain
from typing import Annotated
from langgraph.graph.message import add_messages
import config 

# langgraph_agent.py
import streamlit as st
from retriever_chain import load_chain

# ✅ Cache the chain so it reuses the same Qdrant client
@st.cache_resource
def get_chains(project_name: str, collection_name: str):
    return load_chain(project_name, collection_name)

qa_chain, naive_retriever = get_chains(
    st.session_state["selected_project"],
    st.session_state["collection_name"]
)


llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0)
tavily_tool = TavilySearchResults(max_results=5)

@tool
def tavily_search_tool(query: str) -> str:
    """Use this tool to search the web for recent, current, or external information not present in the historical documents. 
    This complements the historical document search by providing modern context, current events, or additional perspectives."""
    results = tavily_tool.invoke(query)

    if isinstance(results, list) and results:
        formatted = "\n\n".join(
            f"{i+1}. {r.get('title', 'No title')} — {r.get('url', 'No URL')}"
            for i, r in enumerate(results)
        )
        return f"Web search results:\n\n{formatted}"
    else:
        return "No web search results found."

@tool
def historical_rag_tool(question: str) -> str:
    """Search and retrieve information from uploaded historical documents. 
    Use this tool first for any question to check what historical information is available, 
    then consider using web search to supplement with current information."""
    response = qa_chain.invoke(question)
    return f"Historical documents result:\n\n{response['result']}"


# Tool belt
tool_belt = [tavily_search_tool, historical_rag_tool]
model_with_tools  = llm.bind_tools(tool_belt)

# Define AgentState
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: list[Document]

# Model call
def call_model(state: AgentState) -> AgentState:
    messages = state["messages"]

    # Enhanced system message to encourage using both tools when appropriate
    system_message = """You are a comprehensive research assistant. For most questions, you should use BOTH available tools to provide a complete answer:

1. ALWAYS start with historical_rag_tool to check your historical document knowledge base
2. THEN use tavily_search_tool to find current information, additional context, or verification
3. Combine insights from both sources in your final answer
4. Be explicit about which information comes from historical documents vs. web search

Only use a single tool if:
- The question is purely about historical events already covered in documents AND no modern context would be helpful
- The question is purely about very recent events not covered in historical documents

Default to using both tools for comprehensive research. This provides users with both historical context and current perspectives."""

    # Add system message if not already present
    if not any(msg.type == "system" for msg in messages):
        from langchain_core.messages import SystemMessage
        messages = [SystemMessage(content=system_message)] + messages

    response = model_with_tools.invoke(messages)
    return {
        "messages": [response],
        "context": state.get("context", [])
    }

# ToolNode
tool_node = ToolNode(tool_belt)

# Should continue logic
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the last message has tool calls, continue to action
    if last_message.tool_calls:
        return "action"
    else:
        return "end"

# Build graph
def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("action", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"action": "action", "end": END})
    graph.add_edge("action", "agent")

    return graph.compile()
