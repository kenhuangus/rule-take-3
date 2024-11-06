# agents/generator.py
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import logging
import traceback

from config import llm  # Import configured LLM from config
from .base import Agent
from state.state_manager import StateManager
from tools.registry import ToolRegistry

# Enhanced logging setup
logger = logging.getLogger(__name__)
DEBUG = True  # Global debug flag

def debug_log(msg: str, data: Any = None):
    """Utility function for debug logging"""
    if DEBUG:
        call_frame = traceback.extract_stack()[-2]  # Get calling frame
        calling_func = call_frame.name
        if data:
            logger.debug(f"[{calling_func}] {msg} | Data: {json.dumps(data, default=str, indent=2)}")
        else:
            logger.debug(f"[{calling_func}] {msg}")

class AgentGenerator:
    """Generates and manages agents based on problem descriptions"""
    
    def __init__(
        self,
        user_id: str,
        tool_registry: ToolRegistry,
        state_manager: StateManager
    ):
        debug_log(f"Initializing AgentGenerator for user_id: {user_id}")
        
        self.user_id = user_id
        self.tool_registry = tool_registry
        self.state_manager = state_manager
        
        # Get list of tool names
        debug_log("Getting tool list from registry")
        tool_list = self.tool_registry.list_tools()
        debug_log("Raw tool list", tool_list)
        
        self.available_tools = tool_list if isinstance(tool_list, list) else []
        debug_log("Processed available tools", self.available_tools)
        
        logger.info(f"AgentGenerator initialized with {len(self.available_tools)} tools")
    
    async def generate_rules(self, problem_description: str) -> Dict:
        """Generate agent rules based on problem description"""
        debug_log(f"Generating rules for problem: {problem_description}")
        
        # Define the template with proper format
        prompt_template = (
            "Create a JSON configuration for agents to solve this problem: {problem_description}\n\n"
            "Respond with ONLY a JSON object containing an 'agents' array. Each agent must have:\n"
            "- name: string\n"
            "- description: string\n"
            "- tools: array of strings (available tools: {available_tools})\n"
            "- initial_step: string\n"
            "- steps: array of strings\n"
            "- final_step: string\n"
            "- exception_handling: object with retry count and failure action\n\n"
            "Keep the response concise and ensure it's valid JSON format."
        )

        # Format the prompt with available tools
        debug_log("Formatting prompt template")
        formatted_prompt = prompt_template.format(
            problem_description=problem_description,
            available_tools=", ".join(str(tool) for tool in self.available_tools)
        )
        debug_log("Formatted prompt", formatted_prompt)

        try:
            debug_log("Sending request to LLM")
            # Get response from LLM
            response = llm.complete(formatted_prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            debug_log("Raw LLM response", response_text)
            
            response_text = self._clean_response_text(response_text)
            debug_log("Cleaned response text", response_text)
            
            # Parse and validate JSON
            response_json = self._parse_json(response_text)
            debug_log("Parsed JSON response", response_json)
            
            self._validate_response(response_json)
            debug_log("Response validation successful")
            
            # Create agents and initialize their states
            debug_log("Creating agent instances")
            agents = await self._create_agents(response_json["agents"])
            debug_log(f"Created {len(agents)} agents")
            
            result = {
                "problem": problem_description,
                "agents": [
                    {
                        "name": agent.name,
                        "description": agent.description,
                        "tools": agent.tools,
                        "initial_step": agent.initial_step,
                        "steps": agent.steps,
                        "final_step": agent.final_step,
                        "exception_handling": agent.exception_handling
                    }
                    for agent in agents
                ]
            }
            debug_log("Final result", result)
            return result

        except Exception as e:
            error_msg = f"Error generating rules: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise
    
    def _clean_response_text(self, text: str) -> str:
        """Clean the LLM response text to extract valid JSON"""
        debug_log("Cleaning response text", {"input": text})
        
        text = text.strip()
        debug_log("After stripping", {"text": text})
        
        if not text.startswith('{'):
            start_idx = text.find('{')
            if start_idx != -1:
                text = text[start_idx:]
                debug_log("Found JSON start", {"start_index": start_idx, "text": text})
        
        end_idx = text.rfind('}')
        if end_idx != -1:
            text = text[:end_idx + 1]
            debug_log("Found JSON end", {"end_index": end_idx, "text": text})
            
        return text

    def _parse_json(self, text: str) -> Dict:
        """Parse and validate JSON response"""
        debug_log("Parsing JSON text", {"text": text})
        try:
            parsed = json.loads(text)
            debug_log("Successfully parsed JSON", parsed)
            return parsed
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON. Response text: {text}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise ValueError(f"Invalid JSON response: {str(e)}")

    def _validate_response(self, response_json: Dict):
        """Validate the JSON response structure"""
        debug_log("Validating response JSON", response_json)
        
        if not isinstance(response_json, dict):
            error_msg = "Response is not a dictionary"
            debug_log(error_msg, {"type": type(response_json)})
            raise ValueError(error_msg)
        
        agents_data = response_json.get("agents")
        debug_log("Checking agents data", agents_data)
        
        if not isinstance(agents_data, list):
            error_msg = "No 'agents' array found in response"
            debug_log(error_msg, {"agents_type": type(agents_data)})
            raise ValueError(error_msg)
        
        # Validate each agent
        for idx, agent_data in enumerate(agents_data):
            debug_log(f"Validating agent {idx}", agent_data)
            self._validate_agent_data(agent_data)

    def _validate_agent_data(self, agent_data: Dict):
        """Validate individual agent data"""
        debug_log("Validating agent data", agent_data)
        
        required_fields = [
            "name", "description", "tools", "initial_step",
            "steps", "final_step", "exception_handling"
        ]
        
        debug_log("Checking required fields")
        missing_fields = [
            field for field in required_fields 
            if field not in agent_data
        ]
        
        if missing_fields:
            error_msg = f"Missing required fields: {missing_fields}"
            debug_log(error_msg, {"missing": missing_fields})
            raise ValueError(error_msg)
        
        # Validate tools exist in available tools
        debug_log("Validating tools", {"agent_tools": agent_data["tools"], "available_tools": self.available_tools})
        invalid_tools = [
            tool for tool in agent_data["tools"]
            if str(tool) not in [str(t) for t in self.available_tools]
        ]
        
        if invalid_tools:
            error_msg = f"Invalid tools specified: {invalid_tools}"
            debug_log(error_msg, {"invalid": invalid_tools})
            raise ValueError(error_msg)
        
        debug_log("Agent data validation successful")

    async def _create_agents(self, agents_data: List[Dict]) -> List[Agent]:
        """Create agent instances from JSON data"""
        debug_log(f"Creating {len(agents_data)} agents", agents_data)
        
        agents = []
        for idx, agent_data in enumerate(agents_data):
            debug_log(f"Creating agent {idx}", agent_data)
            
            try:
                agent = Agent(
                    name=agent_data["name"],
                    description=agent_data["description"],
                    tools=agent_data["tools"],
                    initial_step=agent_data["initial_step"],
                    steps=agent_data["steps"],
                    final_step=agent_data["final_step"],
                    exception_handling=agent_data["exception_handling"],
                    user_id=self.user_id,
                    tool_registry=self.tool_registry,
                    state_manager=self.state_manager
                )
                
                # Initialize agent state
                debug_log(f"Initializing state for agent {agent.name}")
                await agent.initialize_state()
                agents.append(agent)
                debug_log(f"Successfully created agent {agent.name}")
                
            except Exception as e:
                error_msg = f"Failed to create agent {idx}"
                logger.error(f"{error_msg}: {str(e)}\n{traceback.format_exc()}")
                raise
        
        debug_log(f"Successfully created {len(agents)} agents")
        return agents

    async def execute_agents(self, rules_json: Dict):
        """Execute agents according to generated rules"""
        debug_log("Starting agent execution", rules_json)
        
        try:
            agents_data = rules_json.get("agents", [])
            debug_log(f"Processing {len(agents_data)} agents")
            
            if not isinstance(agents_data, list):
                error_msg = "Invalid rules format: missing agents array"
                debug_log(error_msg, {"type": type(agents_data)})
                raise ValueError(error_msg)
            
            # Create tasks for each agent
            for idx, agent_data in enumerate(agents_data):
                debug_log(f"Creating agent {idx}", agent_data)
                
                agent = Agent(
                    name=agent_data["name"],
                    description=agent_data["description"],
                    tools=agent_data["tools"],
                    initial_step=agent_data["initial_step"],
                    steps=agent_data["steps"],
                    final_step=agent_data["final_step"],
                    exception_handling=agent_data["exception_handling"],
                    user_id=self.user_id,
                    tool_registry=self.tool_registry,
                    state_manager=self.state_manager
                )
                
                # Execute agent
                debug_log(f"Executing agent: {agent.name}")
                await agent.execute()
                
                # Get final state
                debug_log(f"Getting final state for agent {agent.name}")
                final_state = await self.state_manager.get_state(
                    agent.name,
                    self.user_id
                )
                
                if final_state:
                    debug_log(f"Agent {agent.name} final state", {
                        "status": final_state.status,
                        "current_step": final_state.current_step,
                        "tools_state": final_state.tools_state
                    })
                    
                    if final_state.status != "completed":
                        logger.warning(
                            f"Agent {agent.name} execution incomplete: {final_state.status}"
                        )
                else:
                    debug_log(f"No final state found for agent {agent.name}")
            
            debug_log("Agent execution completed successfully")
            
        except Exception as e:
            error_msg = f"Error executing agents: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise

# Example usage:
async def run_agent_system(problem_description: str, user_id: str):
    """Run the complete agent system"""
    debug_log(f"Starting agent system for user {user_id}", {
        "problem": problem_description
    })
    
    try:
        # Initialize components
        debug_log("Initializing system components")
        tool_registry = ToolRegistry()
        state_manager = StateManager("agents.db")
        
        # Create agent generator
        debug_log("Creating AgentGenerator")
        generator = AgentGenerator(user_id, tool_registry, state_manager)
        
        # Generate and execute agents
        debug_log("Generating rules")
        rules = await generator.generate_rules(problem_description)
        debug_log("Generated rules", rules)
        
        debug_log("Executing agents")
        await generator.execute_agents(rules)
        debug_log("Agent execution completed")
        
        return rules
        
    except Exception as e:
        error_msg = f"Agent system execution failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise