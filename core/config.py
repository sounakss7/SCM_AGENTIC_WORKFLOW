import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class AppSettings(BaseSettings):
    """Central configuration for Supply Chain Disruption Response Engine."""
    
    # LLM Settings
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", None)
    ROUTING_PREFERENCE: str = os.getenv("ROUTING_PREFERENCE", "gemini")
    
    # LangSmith Observability
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() in ("true", "1")
    LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY", None)
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "scm-disruption-response")
    
    # Database Settings
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "true").lower() in ("true", "1")
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "local_orders.db")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "scm_agentic_db")
    
    # Human-in-the-Loop Threshold
    # Recovery plans with cost exceeding this threshold require human approval
    HITL_APPROVAL_THRESHOLD_USD: float = float(os.getenv("HITL_APPROVAL_THRESHOLD_USD", "5000.0"))
    
    # Default Solver Limits
    SOLVER_TIMEOUT_SEC: int = int(os.getenv("SOLVER_TIMEOUT_SEC", "10"))
    MAX_CRITIC_RETRIES: int = int(os.getenv("MAX_CRITIC_RETRIES", "2"))
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = AppSettings()
