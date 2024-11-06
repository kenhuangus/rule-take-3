# agents/__init__.py
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime

from .base import Agent
from .messaging import MessageQueue, AgentMessage
from .generator import AgentGenerator, run_agent_system

__all__ = [
    'Agent',
    'MessageQueue',
    'AgentMessage',
    'AgentGenerator',
    'run_agent_system',
    'create_agent',
    'create_agent_system'
]

# Version info
__version__ = '1.0.0'
__author__ = 'Your Name'
__description__ = 'Multi-Agent System with Rule-Based Generation'

# Default configuration
DEFAULT_CONFIG = {
    'message_queue_timeout': 30,
    'max_retries': 3,
    'continue_on_error': True
}

async def create_agent(
    name: str,
    description: str,
    tools: List[str],
    user_id: str,
    tool_registry: 'ToolRegistry',
    state_manager: 'StateManager',
    message_queue: Optional['MessageQueue'] = None,
    available_tools: Optional[List[str]] = None,  # Add this parameter explicitly
    initial_step: str = 'start',
    steps: List[str] = None,
    final_step: str = 'complete',
    exception_handling: Optional[Dict[str, Any]] = None,
) -> Agent:
    """Helper function to create a new agent"""
    return Agent(
        name=name,
        description=description,
        tools=tools,
        initial_step=initial_step,
        steps=steps or [],
        final_step=final_step,
        exception_handling=exception_handling or DEFAULT_CONFIG,
        user_id=user_id,
        tool_registry=tool_registry,
        state_manager=state_manager,
        message_queue=message_queue,
        available_tools=available_tools  # Pass the parameter explicitly
    )

async def create_agent_system(
    user_id: str,
    tool_registry: 'ToolRegistry',
    state_manager: 'StateManager'
) -> AgentGenerator:
    """Create a complete agent system"""
    return AgentGenerator(
        user_id=user_id,
        tool_registry=tool_registry,
        state_manager=state_manager
    )

# Type hints
AgentDict = Dict[str, Any]
AgentState = Dict[str, Any]
AgentTools = List[str]

# System status codes
class AgentStatus:
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"
    STOPPED = "stopped"

# Export components
__all__ += ['AgentStatus', 'AgentDict', 'AgentState', 'AgentTools']