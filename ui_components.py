# ui_components.py
import streamlit as st
from typing import Dict, List, Any


def setup_page():
    """Setup the main page configuration"""
    st.set_page_config(
        page_title="Rule-Based Multi-Agent System",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("🤖 Rule-Based Multi-Agent System")


def render_sidebar():
    """Render the sidebar with tools and agent status"""
    with st.sidebar:
        st.subheader("System Status")
        st.write(f"User ID: {st.session_state.user_id}")

        if st.session_state.available_tools:
            with st.expander("Available Tools", expanded=False):
                for tool_name, tool_info in st.session_state.available_tools.items():
                    st.write(f"**{tool_name}**")
                    st.write(f"Description: {tool_info['description']}")
                    with st.expander("Parameters"):
                        st.json(tool_info['parameters'])

        if st.session_state.execution_status:
            st.write("Active Agents:")
            for agent_name, status in st.session_state.execution_status.items():
                with st.expander(f"Agent: {agent_name}"):
                    st.progress(status["progress"])
                    st.write(f"Status: {status['status']}")
                    st.write(f"Last Update: {status['last_update']}")

        return st.button("Reset System")


def render_chat_history(chat_container):
    """Render the chat history"""
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.write(f"👤 You: {msg['content']}")
            elif msg["role"] == "agent":
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(f"**{msg['agent']}**: {msg['content']}")
            else:
                st.write(f"💻 System: {msg['content']}")
            st.caption(f"Time: {msg['timestamp']}")


def render_input_area():
    """Render the input area and buttons"""
    with st.container():
        col1, col2 = st.columns([4, 1])

        with col1:
            user_input = st.text_area(
                "Enter your task or question:",
                key="user_input",
                height=100
            )

        with col2:
            submit_button = st.button("Submit", use_container_width=True)
            if st.session_state.current_task:
                stop_button = st.button("Stop", use_container_width=True)
            else:
                stop_button = None

        return user_input, submit_button, stop_button


def render_footer():
    """Render the footer"""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <small>Rule-Based Multi-Agent System - v1.0</small>
    </div>
    """, unsafe_allow_html=True)