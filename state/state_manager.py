# state/state_manager.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional
import aiosqlite
import json
import logging
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    agent_id: str
    user_id: str
    current_step: Optional[str]
    tools_state: Dict[str, Any]
    shared_data: Dict[str, Any]
    last_updated: datetime
    status: str
    step_results: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            **asdict(self),
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """Create state from dictionary"""
        return cls(
            **{
                **data,
                "last_updated": datetime.fromisoformat(
                    data["last_updated"] if isinstance(data["last_updated"], str)
                    else data["last_updated"].isoformat()
                )
            }
        )

class StateManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._setup_done = False
        self._lock = asyncio.Lock()
    
    @asynccontextmanager
    async def _get_db(self):
        """Get database connection with automatic setup"""
        if not self._setup_done:
            async with self._lock:
                if not self._setup_done:
                    await self._setup_database()
        
        async with aiosqlite.connect(self.db_path) as db:
            yield db
    
    async def _setup_database(self):
        """Initialize the SQLite database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS agent_states (
                        agent_id TEXT,
                        user_id TEXT,
                        current_step TEXT,
                        tools_state TEXT,
                        shared_data TEXT,
                        last_updated TIMESTAMP,
                        status TEXT,
                        step_results TEXT,
                        PRIMARY KEY (agent_id, user_id)
                    )
                """)
                await db.commit()
            self._setup_done = True
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise
    
    async def create_state(self, **kwargs) -> AgentState:
        """Create a new agent state"""
        state = AgentState(**kwargs)
        await self.update_state(state)
        return state
    
    async def get_state(self, agent_id: str, user_id: str) -> Optional[AgentState]:
        """Retrieve agent state from database"""
        try:
            async with self._get_db() as db:
                async with db.execute(
                    """
                    SELECT * FROM agent_states 
                    WHERE agent_id = ? AND user_id = ?
                    """, 
                    (agent_id, user_id)
                ) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        return AgentState(
                            agent_id=row[0],
                            user_id=row[1],
                            current_step=row[2],
                            tools_state=json.loads(row[3]),
                            shared_data=json.loads(row[4]),
                            last_updated=datetime.fromisoformat(row[5]),
                            status=row[6],
                            step_results=json.loads(row[7])
                        )
            return None
        except Exception as e:
            logger.error(f"Failed to get state: {str(e)}")
            raise

    async def update_state(self, state: AgentState):
        """Update agent state in database"""
        try:
            async with self._get_db() as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO agent_states 
                    (agent_id, user_id, current_step, tools_state, shared_data, 
                     last_updated, status, step_results)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        state.agent_id,
                        state.user_id,
                        state.current_step,
                        json.dumps(state.tools_state),
                        json.dumps(state.shared_data),
                        state.last_updated.isoformat(),
                        state.status,
                        json.dumps(state.step_results)
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update state: {str(e)}")
            raise
    
    async def delete_state(self, agent_id: str, user_id: str):
        """Delete agent state from database"""
        try:
            async with self._get_db() as db:
                await db.execute(
                    "DELETE FROM agent_states WHERE agent_id = ? AND user_id = ?",
                    (agent_id, user_id)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to delete state: {str(e)}")
            raise


async def initialize_state_manager(db_path: str) -> StateManager:
    """
    Initialize and return a StateManager instance, ensuring the database is set up.
    
    Args:
        db_path: Path to the SQLite database file
    
    Returns:
        Initialized StateManager instance
    """
    manager = StateManager(db_path)
    await manager._setup_database()  # Ensures the database structure is created
    return manager
