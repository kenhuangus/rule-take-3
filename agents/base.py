# agents/base.py
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
from dataclasses import dataclass, asdict
import json
import uuid
from .messaging import MessageQueue, AgentMessage

logger = logging.getLogger(__name__)

class Agent:
    def __init__(
        self,
        name: str,
        description: str,
        tools: List[str],
        initial_step: str,
        steps: List[str],
        final_step: str,
        exception_handling: Dict[str, Any],
        user_id: str,
        tool_registry: 'ToolRegistry',
        state_manager: 'StateManager',
        message_queue: Optional[MessageQueue] = None
    ):
        self.name = name
        self.description = description
        self.tools = tools
        self.initial_step = initial_step
        self.steps = steps
        self.final_step = final_step
        self.exception_handling = exception_handling
        self.user_id = user_id
        self.tool_registry = tool_registry
        self.state_manager = state_manager
        
        # Initialize messaging
        self.message_queue = message_queue or MessageQueue()
        self._status = "initialized"
        self._current_step = None
      
        # Subscribe to messages
        self.message_queue.subscribe(self.name, self._handle_message)
    
    async def initialize_state(self):
        """Initialize agent state"""
        state = await self.state_manager.create_state(
            agent_id=self.name,
            user_id=self.user_id,
            current_step=None,
            tools_state={},
            shared_data={},
            last_updated=datetime.now(),
            status="initialized",
            step_results={}
        )
        return state

    async def _handle_message(self, message: AgentMessage):
        """Handle incoming messages"""
        logger.info(f"Agent {self.name} received message: {message.message_type}")
        if message.message_type == "stop":
            self._status = "stopped"
    
    async def _update_state_status(self, state, status: str, current_step: Optional[str] = None, error: Optional[str] = None):
        """Update state status"""
        state.status = status
        if current_step:
            state.current_step = current_step
        if error:
            state.shared_data['last_error'] = error
        state.last_updated = datetime.now()
        await self.state_manager.update_state(state)
    
    async def execute(self):
        """Execute agent's workflow"""
        state = None
        try:
            # Initialize state
            state = await self.initialize_state()
            self._status = "running"
            await self._update_state_status(state, "running")
            
            # Start message queue if not already running
            if not self.message_queue._running:
                await self.message_queue.start()
            
            # Execute steps
            steps = [self.initial_step] + self.steps + [self.final_step]
            for step in steps:
                if self._status == "stopped":
                    logger.info(f"Agent {self.name} stopped during execution")
                    await self._update_state_status(state, "stopped")
                    return
                
                logger.info(f"Agent {self.name}: Executing step {step}")
                await self._execute_step(step, state)
                
                if self._status == "failed":
                    return
            
            # Mark completion
            self._status = "completed"
            await self._update_state_status(state, "completed")
            logger.info(f"Agent {self.name}: Execution completed successfully")
            
        except Exception as e:
            logger.error(f"Agent {self.name} execution failed: {str(e)}")
            self._status = "failed"
            if state:
                await self._update_state_status(state, "failed", error=str(e))
            raise
        finally:
            # Unsubscribe from messages
            self.message_queue.unsubscribe(self.name)
    
    async def _execute_step(self, step: str, state) -> Dict[str, Any]:
        """Execute a single step using available tools"""
        try:
            self._current_step = step
            await self._update_state_status(state, "running", current_step=step)
            
            # Execute each tool
            step_results = {}
            for tool_name in self.tools:
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    logger.warning(f"Tool {tool_name} not found in registry")
                    continue
                
                try:
                    # Prepare tool parameters
                    params = {
                        "step": step,
                        "user_id": self.user_id,
                        "query": f"Execute {step} step",
                        "current_state": state.tools_state.get(tool_name, {}),
                        "shared_data": state.shared_data,
                        "input_data": state.step_results
                    }
                    
                    # Execute tool
                    result = await tool.safe_execute(params)
                    step_results[tool_name] = result
                    
                    # Update tool state
                    if result.get("state"):
                        state.tools_state[tool_name] = result["state"]
                    
                except Exception as e:
                    logger.error(f"Tool {tool_name} execution failed: {str(e)}")
                    if self.exception_handling.get("continue_on_error", False):
                        step_results[tool_name] = {"error": str(e)}
                    else:
                        raise
            
            # Store step results
            state.step_results[step] = step_results
            await self.state_manager.update_state(state)
            
            # Send progress message
            await self._send_progress_message(step, step_results)
            
            return step_results
            
        except Exception as e:
            logger.error(f"Step {step} execution failed: {str(e)}")
            raise

    async def _send_progress_message(self, step: str, results: Dict[str, Any]):
        """Send progress message"""
        if self.message_queue._running:
            message = AgentMessage(
                sender=self.name,
                receiver="managing_agent",
                content={
                    "step": step,
                    "status": "completed",
                    "results": results
                },
                message_type="progress_update",
                timestamp=datetime.now()
            )
            await self.message_queue.send(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "initial_step": self.initial_step,
            "steps": self.steps,
            "final_step": self.final_step,
            "status": self._status,
            "current_step": self._current_step
        }