# state/__init__.py
from typing import Dict, Any, List, Optional, Union, Tuple
from .state_manager import StateManager, AgentState, initialize_state_manager

__all__ = [
    'StateManager',
    'AgentState',
    'create_state_manager',
    'get_state',
    'update_state'
]

# Version info
__version__ = '1.0.0'
__author__ = 'Your Name'
__description__ = 'State management system for agents'

# Default configuration
DEFAULT_CONFIG = {
    'db_path': 'data/agent_states.db',
    'enable_cache': True,
    'cache_size': 1000,
    'cache_ttl': 3600  # 1 hour
}

# Global state manager instance
_global_state_manager: Optional[StateManager] = None

def create_state_manager(
    db_path: Optional[str] = None,
    **kwargs
) -> StateManager:
    """Create a new state manager instance"""
    global _global_state_manager
    
    if _global_state_manager is None:
        _global_state_manager = StateManager(
            db_path or DEFAULT_CONFIG['db_path']
        )
    
    return _global_state_manager

async def get_state(
    agent_id: str,
    user_id: str,
    state_manager: Optional[StateManager] = None
) -> Optional[AgentState]:
    """Get agent state using global or provided state manager"""
    sm = state_manager or _global_state_manager
    if sm is None:
        raise RuntimeError("No state manager available")
    
    return await sm.get_state(agent_id, user_id)

async def update_state(
    state: AgentState,
    state_manager: Optional[StateManager] = None
):
    """Update agent state using global or provided state manager"""
    sm = state_manager or _global_state_manager
    if sm is None:
        raise RuntimeError("No state manager available")
    
    await sm.update_state(state)