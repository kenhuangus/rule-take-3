# tools/BaseTool.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from datetime import datetime
import logging
import asyncio
from contextlib import contextmanager
import traceback

logger = logging.getLogger(__name__)

class ToolExecutionError(Exception):
    """Custom exception for tool execution errors"""
    pass

class BaseTool(ABC):
    """Abstract base class for all tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._last_execution = None
        self._execution_count = 0
        self._error_count = 0
        
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    async def safe_execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Safely execute the tool with validation and error handling"""
        try:
            # Validate parameters
            if not await self._validate_params(params):
                raise ToolExecutionError("Missing required parameters")
            
            # Set execution context
            self._last_execution = datetime.now()
            self._execution_count += 1
            
            # Execute tool
            try:
                result = await asyncio.wait_for(
                    self.execute(params),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                raise ToolExecutionError("Tool execution timed out")
            
            # Validate result
            if not isinstance(result, dict):
                raise ToolExecutionError("Tool must return a dictionary")
            
            # Add execution metadata
            result["execution_metadata"] = {
                "timestamp": self._last_execution.isoformat(),
                "execution_count": self._execution_count,
                "error_count": self._error_count
            }
            
            return result
            
        except Exception as e:
            self._error_count += 1
            error_msg = f"Tool {self.name} execution failed: {str(e)}"
            stack_trace = traceback.format_exc()
            logger.error(f"{error_msg}\n{stack_trace}")
            
            return {
                "status": "error",
                "error": str(e),
                "stack_trace": stack_trace,
                "state": {
                    "last_error": datetime.now().isoformat(),
                    "error_count": self._error_count
                }
            }
    
    async def _validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        required_params = ["step", "user_id"]
        return all(param in params for param in required_params)