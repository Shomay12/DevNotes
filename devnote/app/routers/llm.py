"""
DevNote LLM & AI Assistant API Router.
Handles chat completions, LLM connection testing, and provider configurations.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from devnote.app.services.llm_service import llm_service

router = APIRouter(prefix="/api/llm", tags=["llm"])


class ChatRequest(BaseModel):
    prompt: str = Field(..., description="User prompt or instruction")
    system_prompt: Optional[str] = Field(default=None, description="System instructions")
    provider: str = Field(default="ollama", description="LLM provider: ollama, openai, gemini, custom")
    endpoint: Optional[str] = Field(default=None, description="Custom API endpoint URL")
    api_key: Optional[str] = Field(default=None, description="API key if required")
    model: Optional[str] = Field(default=None, description="Model identifier")
    context: Optional[str] = Field(default=None, description="Active notebook code or research text")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class TestConnectionRequest(BaseModel):
    provider: str = Field(default="ollama")
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None


@router.post("/chat")
async def chat_with_llm(req: ChatRequest):
    """Executes a chat completion query against the chosen local or cloud LLM system."""
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty."
        )

    result = await llm_service.chat(
        prompt=req.prompt,
        system_prompt=req.system_prompt,
        provider=req.provider,
        endpoint=req.endpoint,
        api_key=req.api_key,
        model=req.model,
        context=req.context,
        temperature=req.temperature
    )
    return result


@router.post("/test")
async def test_llm_connection(req: TestConnectionRequest):
    """Tests connectivity to local or remote LLM endpoint (Ollama, LM Studio, OpenAI, etc.)."""
    return await llm_service.test_connection(
        provider=req.provider,
        endpoint=req.endpoint,
        api_key=req.api_key,
        model=req.model
    )


@router.get("/config")
def get_llm_default_config():
    """Returns supported LLM providers and standard configuration templates."""
    return {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama (Local & Private)",
                "default_endpoint": "http://localhost:11434",
                "requires_api_key": False,
                "default_model": "llama3",
                "description": "Zero cost, runs completely offline on your computer. Download from ollama.com."
            },
            {
                "id": "openai",
                "name": "OpenAI (GPT-4o)",
                "default_endpoint": "https://api.openai.com/v1",
                "requires_api_key": True,
                "default_model": "gpt-4o-mini",
                "description": "Standard cloud models from OpenAI. Requires an OpenAI API key."
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "default_endpoint": "https://generativelanguage.googleapis.com",
                "requires_api_key": True,
                "default_model": "gemini-1.5-flash",
                "description": "Fast multimodal Google AI models. Requires a Google AI Studio API key."
            },
            {
                "id": "custom",
                "name": "Custom OpenAI-Compatible (LM Studio / vLLM / OpenRouter)",
                "default_endpoint": "http://localhost:1234/v1",
                "requires_api_key": False,
                "default_model": "default",
                "description": "Connect to LM Studio, LocalAI, vLLM, or corporate inference gateways."
            }
        ]
    }
