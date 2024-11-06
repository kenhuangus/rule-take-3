# tools/__init__.py
from typing import Dict, Any, List, Optional, Union, Tuple
from .BaseTool import BaseTool, ToolExecutionError
from .registry import ToolRegistry

__all__ = [
    'BaseTool',
    'ToolExecutionError',
    'ToolRegistry',
    'register_tool',
    'get_tool',
    'list_tools'
]

# Version info
__version__ = '1.0.0'
__author__ = 'Ken Huang'
__description__ = 'Tool system for agent operations'

# Global tool registry instance
_global_registry = ToolRegistry()

def register_tool(tool: BaseTool):
    """Register a tool in the global registry"""
    _global_registry.register_tool(tool)

def get_tool(name: str) -> Optional[BaseTool]:
    """Get a tool from the global registry"""
    return _global_registry.get_tool(name)

def list_tools() -> List[str]:
    """List all registered tools"""
    return _global_registry.list_tools()

# Tool categories
TOOL_CATEGORIES = {
    'search': 'Tools for searching and retrieving information',
    'processing': 'Tools for processing data',
    'storage': 'Tools for data storage and retrieval',
    'communication': 'Tools for communication and messaging',
    'analysis': 'Tools for data analysis and insights'
}

# Tool metadata schema
TOOL_METADATA_SCHEMA = {
    'name': str,
    'description': str,
    'category': str,
    'version': str,
    'required_params': List[str],
    'optional_params': Dict[str, Any],
    'returns': Dict[str, Any]
}

def validate_tool(tool: BaseTool) -> bool:
    """Validate tool implementation"""
    try:
        # Check required attributes
        assert hasattr(tool, 'name'), "Tool must have a name"
        assert hasattr(tool, 'description'), "Tool must have a description"
        assert callable(getattr(tool, 'execute')), "Tool must have execute method"
        
        # Check method signatures
        import inspect
        execute_sig = inspect.signature(tool.execute)
        assert 'params' in execute_sig.parameters, "execute() must accept params argument"
        
        return True
    except Exception as e:
        logger.error(f"Tool validation failed: {str(e)}")
        return False