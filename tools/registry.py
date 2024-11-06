# tools/registry.py
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json
from .BaseTool import BaseTool, ToolExecutionError

logger = logging.getLogger(__name__)

class RegistryError(Exception):
    """Base exception for registry errors"""
    pass

class ToolAlreadyRegisteredError(RegistryError):
    """Raised when attempting to register a tool that already exists"""
    pass

class ToolNotFoundError(RegistryError):
    """Raised when requesting a tool that doesn't exist"""
    pass

class ToolValidationError(RegistryError):
    """Raised when a tool fails validation"""
    pass

class ToolRegistry:
    def __init__(self, persistence_path: Optional[str] = None):
        # Tool storage
        self._tools: Dict[str, BaseTool] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[str, List[str]] = {}
        
        # Define available tools
        self._available_tools = [
            "web_search",
            "API_caller",
            "LLM_model",
            "RAG_tool",
            "knowledge_tool",
            "feedback_tool",
            "db_tool"
        ]
        
        # Persistence
        self._persistence_path = persistence_path
        self._performance_metrics = {}
        
        logger.info(f"Initialized ToolRegistry with {len(self._available_tools)} available tools")
    
    async def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return self._available_tools
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return self._available_tools

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool in the registry"""
        if tool.name in self._tools:
            raise ToolAlreadyRegisteredError(f"Tool '{tool.name}' is already registered")
        
        if tool.name not in self._available_tools:
            logger.warning(f"Registering unknown tool: {tool.name}")
            
        self._tools[tool.name] = tool
        self._tool_metadata[tool.name] = {
            "registered_at": datetime.now().isoformat(),
            "execution_count": 0,
            "error_count": 0
        }
        logger.info(f"Successfully registered tool: {tool.name}")

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool"""
        if name in self._tools:
            del self._tools[name]
            if name in self._tool_metadata:
                del self._tool_metadata[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False

    async def update_tool_metrics(self, name: str, success: bool) -> None:
        """Update tool execution metrics"""
        if name in self._tool_metadata:
            self._tool_metadata[name]["execution_count"] += 1
            if not success:
                self._tool_metadata[name]["error_count"] += 1

    def get_tool_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific tool"""
        return self._tool_metadata.get(name)