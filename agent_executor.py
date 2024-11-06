# agent_executor.py
import asyncio
from typing import Dict, Any
import logging
import traceback
import streamlit as st
from agents import Agent
from tools import ToolRegistry
from state import StateManager
from state_management import add_message, show_agent_status

logger = logging.getLogger(__name__)
DEBUG = False


def debug_log(msg: str, data: Any = None):
    if DEBUG:
        call_frame = traceback.extract_stack()[-2]
        calling_func = call_frame.name
        if data:
            logger.debug(f"[{calling_func}] {msg} | Data: {data}")
        else:
            logger.debug(f"[{calling_func}] {msg}")


async def execute_agent(agent_instance: Agent):
    """Execute the agent with proper error handling and timeout"""
    debug_log(f"Executing agent: {agent_instance.name}")
    try:
        await asyncio.wait_for(
            agent_instance.execute(),
            timeout=30
        )

        debug_log(f"Agent {agent_instance.name} completed successfully")
        show_agent_status(agent_instance.name, "completed", 1.0)
        add_message("system", f"Agent {agent_instance.name} completed successfully")

    except asyncio.TimeoutError:
        debug_log(f"Agent {agent_instance.name} execution timed out")
        show_agent_status(agent_instance.name, "timeout", 0.0)
        add_message("system", f"Agent {agent_instance.name} timed out")
        raise

    except Exception as e:
        debug_log(f"Agent {agent_instance.name} execution failed: {str(e)}")
        show_agent_status(agent_instance.name, "failed", 0.0)
        add_message("system", f"Agent {agent_instance.name} failed: {str(e)}")
        raise


async def process_agent(agent_data: Dict, tool_registry: ToolRegistry, state_manager: StateManager):
    """Process a single agent with proper event loop handling"""
    debug_log(f"Processing agent: {agent_data['name']}")
    try:
        agent_instance = Agent(
            name=agent_data["name"],
            description=agent_data["description"],
            tools=agent_data["tools"],
            initial_step=agent_data["initial_step"],
            steps=agent_data["steps"],
            final_step=agent_data["final_step"],
            exception_handling=agent_data["exception_handling"],
            user_id=st.session_state.user_id,
            tool_registry=tool_registry,
            state_manager=state_manager
        )

        await agent_instance.initialize_state()
        show_agent_status(agent_data["name"], "Starting", 0.0)

        await asyncio.wait_for(
            execute_agent(agent_instance),
            timeout=30
        )

    except asyncio.TimeoutError:
        show_agent_status(agent_data["name"], "timeout", 0.0)
        add_message("system", f"Agent {agent_data['name']} timed out")
    except Exception as e:
        show_agent_status(agent_data["name"], "failed", 0.0)
        add_message("system", f"Agent {agent_data['name']} failed: {str(e)}")


async def stop_agents():
    """Stop all running agents"""
    debug_log("Stopping all agents")
    try:
        for agent_name, status in st.session_state.execution_status.items():
            if status["status"] == "running":
                show_agent_status(agent_name, "stopped", status["progress"])
                add_message("system", f"Agent {agent_name} stopped by user")

        st.session_state.current_task = None

    except Exception as e:
        error_msg = f"Error stopping agents: {str(e)}"
        debug_log(error_msg)
        add_message("system", f"Error: {error_msg}")
