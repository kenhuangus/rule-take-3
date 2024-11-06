# state_management.py
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
import json
import logging
import uuid
import traceback

logger = logging.getLogger(__name__)
DEBUG = False

def debug_log(msg: str, data: Any = None):
    if DEBUG:
        call_frame = traceback.extract_stack()[-2]
        calling_func = call_frame.name
        if data:
            logger.debug(f"[{calling_func}] {msg} | Data: {json.dumps(data, default=str, indent=2)}")
        else:
            logger.debug(f"[{calling_func}] {msg}")

def initialize_session_state():
    """Initialize all session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if 'active_agents' not in st.session_state:
        st.session_state.active_agents = {}
    if 'execution_status' not in st.session_state:
        st.session_state.execution_status = {}
    if 'current_task' not in st.session_state:
        st.session_state.current_task = None
    if 'available_tools' not in st.session_state:
        st.session_state.available_tools = {}

def add_message(role: str, content: str, agent_name: Optional[str] = None):
    """Add a message to the chat history."""
    debug_log("Adding message", {
        "role": role,
        "content": content,
        "agent": agent_name
    })
    try:
        st.session_state.messages.append({
            "role": role,
            "content": content,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        debug_log(f"Error adding message: {str(e)}")
        raise

def show_agent_status(agent_name: str, status: str, progress: float):
    """Update agent status in the sidebar."""
    debug_log("Updating agent status", {
        "agent": agent_name,
        "status": status,
        "progress": progress
    })
    try:
        st.session_state.execution_status[agent_name] = {
            "status": status,
            "progress": progress,
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        debug_log(f"Error updating agent status: {str(e)}")
        raise

def reset_system():
    """Reset the system state safely"""
    st.session_state.messages = []
    st.session_state.active_agents = {}
    st.session_state.execution_status = {}
    st.session_state.current_task = None
    st.experimental_rerun()

def format_tools_for_llm() -> str:
    """Format available tools into a string for LLM prompt."""
    debug_log("Formatting tools for LLM")
    try:
        tools_description = "Available tools:\n\n"
        for tool_name, tool_info in st.session_state.available_tools.items():
            tools_description += f"""
Tool: {tool_name}
Description: {tool_info['description']}
Parameters: {json.dumps(tool_info['parameters'], indent=2)}
Return Type: {tool_info['return_type']}
---
"""
        return tools_description
    except Exception as e:
        debug_log(f"Error formatting tools: {str(e)}")
        raise