# config.py

import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Set up logging
def setup_logging():
    """Configure logging with both file and console handlers"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_filename = log_dir / f'config_{datetime.now().strftime("%Y%m%d")}.log'
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_filename, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    # Setup logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# Load environment variables
try:
    load_dotenv()
    logger.info("Successfully loaded environment variables")
except Exception as e:
    logger.error(f"Failed to load environment variables: {str(e)}")
    raise

# Import necessary LlamaIndex components
from llama_index.llms.nvidia import NVIDIA
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.gemini import Gemini
from llama_index.llms.together import TogetherLLM
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Configuration Metrics
class ConfigMetrics:
    def __init__(self):
        self.initialization_times: Dict[str, float] = {}
        self.model_stats: Dict[str, Dict[str, Any]] = {
            "llm": {"initialization_time": 0, "errors": 0},
            "embedding": {"initialization_time": 0, "errors": 0}
        }
        self.start_time = time.time()

    def record_initialization(self, model_type: str, duration: float):
        self.initialization_times[model_type] = duration
        self.model_stats[model_type]["initialization_time"] = duration

    def record_error(self, model_type: str):
        self.model_stats[model_type]["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "uptime": time.time() - self.start_time,
            "initialization_times": self.initialization_times,
            "model_stats": self.model_stats
        }

config_metrics = ConfigMetrics()

# Default model and embedding settings
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "nvidia")
DEFAULT_EMBEDDING = os.getenv("DEFAULT_EMBEDDING", "nvidia")

# Workflow Configuration
WORKFLOW_CONFIG = {
    "max_retries": 3,
    "timeout_seconds": 30,
    "batch_size": 5,
    "max_concurrent_tasks": 3
}

# Tool Configuration
TOOL_CONFIG = {
    "cache_enabled": True,
    "cache_ttl_seconds": 3600,
    "max_cache_size": 1000,
    "tool_types": ["knowledge", "assessment", "feedback"]
}

# Assessment Configuration
ASSESSMENT_CONFIG = {
    "min_questions": 3,
    "max_questions": 10,
    "time_limit_minutes": 30,
    "passing_score": 70,
    "difficulty_levels": ["easy", "medium", "hard"],
    "skill_areas": ["concept", "application", "analysis"],
    "feedback_types": ["detailed", "summary", "quick"],
    "metrics_tracking": True
}

# Learning Configuration
LEARNING_CONFIG = {
    "max_subtopics": 5,
    "min_confidence": 0.7,
    "max_retries_per_topic": 2,
    "feedback_threshold": 0.8,
    "topics_per_session": 3,
    "min_examples": 2,
    "max_examples": 5
}

# Model Functions
def get_llm():
    """Initialize and return LLM instance"""
    start_time = time.time()
    try:
        logger.info(f"Initializing LLM with model type: {DEFAULT_MODEL}")
        
        if DEFAULT_MODEL == "nvidia" and os.getenv('NVIDIA_API_KEY'):
            model = NVIDIA(
                model="meta/llama3-70b-instruct", 
                api_key=os.getenv('NVIDIA_API_KEY')
            )
        elif DEFAULT_MODEL == "openai" and os.getenv('OPENAI_API_KEY'):
            model = OpenAI(
                model="gpt-4", 
                api_key=os.getenv('OPENAI_API_KEY')
            )
        elif DEFAULT_MODEL == "anthropic" and os.getenv('ANTHROPIC_API_KEY'):
            model = Anthropic(
                model="claude-3-sonnet", 
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
        elif DEFAULT_MODEL == "google" and os.getenv('GOOGLE_API_KEY'):
            model = Gemini(
                model="gemini-3", 
                api_key=os.getenv('GOOGLE_API_KEY')
            )
        elif DEFAULT_MODEL == "together" and os.getenv('TOGETHER_API_KEY'):
            model = TogetherLLM(
                model="together-llm", 
                api_key=os.getenv('TOGETHER_API_KEY')
            )
        else:
            raise ValueError(
                f"No valid LLM configuration found. Current model: {DEFAULT_MODEL}"
            )
        
        initialization_time = time.time() - start_time
        config_metrics.record_initialization("llm", initialization_time)
        logger.info(f"LLM initialized in {initialization_time:.2f} seconds")
        return model
        
    except Exception as e:
        config_metrics.record_error("llm")
        logger.error(f"Failed to initialize LLM: {str(e)}")
        raise

def get_embedding():
    """Initialize and return embedding model instance"""
    start_time = time.time()
    try:
        logger.info(f"Initializing embedding with type: {DEFAULT_EMBEDDING}")
        
        if DEFAULT_EMBEDDING == "nvidia" and os.getenv('NVIDIA_API_KEY'):
            model = NVIDIAEmbedding(
                model="NV-Embed-QA", 
                api_key=os.getenv('NVIDIA_API_KEY')
            )
        elif DEFAULT_EMBEDDING == "openai" and os.getenv('OPENAI_API_KEY'):
            model = OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=os.getenv('OPENAI_API_KEY')
            )
        elif DEFAULT_EMBEDDING == "huggingface":
            model = HuggingFaceEmbedding(
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
        else:
            raise ValueError(
                f"No valid embedding configuration found. Current type: {DEFAULT_EMBEDDING}"
            )
        
        initialization_time = time.time() - start_time
        config_metrics.record_initialization("embedding", initialization_time)
        logger.info(f"Embedding initialized in {initialization_time:.2f} seconds")
        return model
        
    except Exception as e:
        config_metrics.record_error("embedding")
        logger.error(f"Failed to initialize embedding: {str(e)}")
        raise

def get_config_status() -> Dict[str, Any]:
    """Get current configuration status and metrics"""
    return {
        "model_type": DEFAULT_MODEL,
        "embedding_type": DEFAULT_EMBEDDING,
        "workflow_config": WORKFLOW_CONFIG,
        "tool_config": TOOL_CONFIG,
        "assessment_config": ASSESSMENT_CONFIG,
        "learning_config": LEARNING_CONFIG,
        "metrics": config_metrics.get_metrics()
    }

# Initialize models
try:
    logger.info("Starting global model initialization")
    llm = get_llm()
    embed_model = get_embedding()
    logger.info("Successfully initialized all models")
except Exception as e:
    logger.critical(f"Failed to initialize models: {str(e)}")
    raise

# Export components
__all__ = [
    'llm', 
    'embed_model', 
    'get_config_status', 
    'config_metrics',
    'WORKFLOW_CONFIG',
    'TOOL_CONFIG',
    'ASSESSMENT_CONFIG',
    'LEARNING_CONFIG'
]