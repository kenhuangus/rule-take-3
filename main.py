# main.py
import streamlit as st
import nest_asyncio
import atexit
from typing import Dict, Any
import logging

from event_loop import run_async, cleanup, init_event_loop
from state_management import (
    initialize_session_state, add_message, format_tools_for_llm,
    reset_system
)
from agent_executor import process_agent, stop_agents
from ui_components import (
    setup_page, render_sidebar, render_chat_history,
    render_input_area, render_footer
)
from agents import AgentGenerator
from tools import ToolRegistry
from state import StateManager

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Apply nest_asyncio
nest_asyncio.apply()

# Initialize session state
initialize_session_state()

# Register cleanup
if 'cleanup_registered' not in st.session_state:
    atexit.register(cleanup)
    st.session_state.cleanup_registered = True

# Setup UI
setup_page()

# Render sidebar
if render_sidebar():
    reset_system()

# Setup chat container
chat_container = st.container()

# Render input area and get user input components
user_input, submit_button, stop_button = render_input_area()

# Process user input
if submit_button and user_input:
    try:
        add_message("user", user_input)

        with st.spinner("Initializing system..."):
            # Initialize components
            generator = AgentGenerator(
                st.session_state.user_id,
                ToolRegistry(),
                StateManager("agents.db")
            )
            tools_description = format_tools_for_llm()

        with st.spinner("Generating agent rules..."):
            # Generate rules
            rules_json = run_async(generator.generate_rules(
                f"""
                Task: {user_input}
                Available tools: {tools_description}
                Create a system of specialized agents to accomplish this task.
                """
            ))
            st.session_state.current_task = rules_json

        # Process agents sequentially
        add_message("system", f"Generated {len(rules_json['agents'])} agents for your task")

        for agent_data in rules_json["agents"]:
            add_message(
                "agent",
                f"🤖 {agent_data['name']}: {agent_data['description']}",
                agent_data["name"]
            )

            try:
                with st.spinner(f"Processing agent: {agent_data['name']}"):
                    run_async(process_agent(
                        agent_data,
                        generator.tool_registry,
                        generator.state_manager
                    ))
            except TimeoutError:
                st.warning(f"Agent {agent_data['name']} timed out")
                continue
            except Exception as e:
                st.error(f"Agent {agent_data['name']} failed: {str(e)}")
                continue

        st.success("Task processing completed")

    except TimeoutError as e:
        st.error("Operation timed out. Please try again.")
        add_message("system", "Operation timed out")
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        add_message("system", f"Error: {str(e)}")

# Handle stop button
if stop_button:
    try:
        run_async(stop_agents())
        st.experimental_rerun()
    except Exception as e:
        error_msg = f"Error handling stop: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)

# Render chat history
render_chat_history(chat_container)

# Render footer
render_footer()

if __name__ == "__main__":
    try:
        run_async(init_event_loop())
    except Exception as e:
        logger.error(f"Failed to initialize system: {str(e)}")
        st.error(f"Failed to initialize system: {str(e)}")