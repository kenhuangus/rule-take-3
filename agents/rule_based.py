# agents/rule_based.py
import json
from typing import Dict, Any, List, Optional
from config import llm  # Import configured LLM

# Import required components from agent system
from . import create_agent, Agent

async def generate_rules(
    problem_description: str,
    user_id: str,
    tool_registry: 'ToolRegistry',
    state_manager: 'StateManager',
) -> Dict:
    """
    Generates JSON rules using an LLM based on the user's problem description.
    """
    print(f"Generating rules for problem: {problem_description}")

    prompt_template = (
        "Create a JSON configuration for agents to solve this problem: {problem_description}\n\n"
        "Respond with ONLY a JSON object containing an 'agents' array. Each agent must have:\n"
        "- name: string\n"
        "- description: string\n"
        "- tools: array of strings (choose from: web_search, API_caller, LLM_model, RAG_tool)\n"
        "- initial_step: string\n"
        "- steps: array of strings\n"
        "- final_step: string\n"
        "- exception_handling: object\n\n"
        "Keep the response concise and ensure it's valid JSON format."
    )

    formatted_prompt = prompt_template.format(problem_description=problem_description)

    try:
        response = llm.complete(formatted_prompt)
        response_text = response.text if hasattr(response, 'text') else str(response)
        response_text = response_text.strip()
        
        if not response_text.startswith('{'):
            start_idx = response_text.find('{')
            if start_idx != -1:
                response_text = response_text[start_idx:]
        
        end_idx = response_text.rfind('}')
        if end_idx != -1:
            response_text = response_text[:end_idx + 1]

        response_json = json.loads(response_text)
        
        if not isinstance(response_json, dict):
            raise ValueError("Response is not a dictionary")
        
        agents_data = response_json.get("agents")
        if not isinstance(agents_data, list):
            raise ValueError("No 'agents' array found in response")

        # Convert to proper format without creating agents yet
        rules_json = {
            "problem": problem_description,
            "agents": []
        }
        
        for agent_data in agents_data:
            required_fields = ["name", "description", "tools", "initial_step", 
                             "steps", "final_step", "exception_handling"]
            missing_fields = [field for field in required_fields if field not in agent_data]
            if missing_fields:
                raise ValueError(f"Missing required fields in agent data: {missing_fields}")
            
            agent_config = {
                "agent_name": agent_data["name"],
                "description": agent_data["description"],
                "tools": agent_data["tools"],
                "initial_step": agent_data["initial_step"],
                "steps": agent_data["steps"],
                "final_step": agent_data["final_step"],
                "exception_handling": agent_data["exception_handling"]
            }
            rules_json["agents"].append(agent_config)
        
        return rules_json
    
    except Exception as e:
        raise Exception(f"Error generating rules: {str(e)}")

# agents/rule_based.py

async def execute_agents(
    rules_json: Dict,
    user_id: str,
    tool_registry: 'ToolRegistry',
    state_manager: 'StateManager',
    message_queue: Optional['MessageQueue'] = None
):
    """
    Executes each agent according to the generated JSON rules.
    """
    try:
        print("\nStarting agent execution based on generated rules...\n")
        
        agents_data = rules_json.get("agents")
        if not isinstance(agents_data, list):
            raise ValueError("Invalid rules_json format: missing or invalid 'agents' array")
        
        # Get available tools
        available_tools = await tool_registry.get_available_tools()
        
        agents = []
        for agent_data in agents_data:
            # Create agent using the helper function
            agent = await create_agent(
                name=agent_data["agent_name"],
                description=agent_data["description"],
                tools=agent_data["tools"],
                user_id=user_id,
                tool_registry=tool_registry,
                state_manager=state_manager,
                message_queue=message_queue,
                available_tools=available_tools,
                **{  # Pass these as kwargs
                    'initial_step': agent_data["initial_step"],
                    'steps': agent_data["steps"],
                    'final_step': agent_data["final_step"],
                    'exception_handling': agent_data["exception_handling"]
                }
            )
            agents.append(agent)
        
        # Execute all agents
        for agent in agents:
            await agent.execute()
            
    except Exception as e:
        raise Exception(f"Error executing agents: {str(e)}")

agent = await create_agent(
    name=agent_data["agent_name"],
    description=agent_data["description"],
    tools=agent_data["tools"],
    user_id=user_id,
    tool_registry=tool_registry,
    state_manager=state_manager,
    message_queue=message_queue,
    available_tools=available_tools,
    **{  # Pass these as kwargs
        'initial_step': agent_data["initial_step"],
        'steps': agent_data["steps"],
        'final_step': agent_data["final_step"],
        'exception_handling': agent_data["exception_handling"]
    }
)