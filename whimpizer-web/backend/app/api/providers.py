"""
AI Providers API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.models.jobs import ProviderInfo, AIProvider

router = APIRouter()

@router.get("/", response_model=List[ProviderInfo])
async def list_providers():
    """List all available AI providers and their models"""
    try:
        providers = [
            ProviderInfo(
                name="openai",
                display_name="OpenAI",
                models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                available=True,
                description="OpenAI's GPT models for text generation"
            ),
            ProviderInfo(
                name="anthropic", 
                display_name="Anthropic",
                models=["claude-3-sonnet", "claude-3-haiku", "claude-2"],
                available=True,
                description="Anthropic's Claude models for conversational AI"
            ),
            ProviderInfo(
                name="google",
                display_name="Google",
                models=["gemini-pro", "gemini-1.5-pro"],
                available=True,
                description="Google's Gemini models for multimodal AI"
            )
        ]
        
        return providers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")

@router.get("/{provider_name}", response_model=ProviderInfo)
async def get_provider_info(provider_name: str):
    """Get detailed information about a specific provider"""
    try:
        # For now, return static data - in production this would check actual availability
        providers_map = {
            "openai": ProviderInfo(
                name="openai",
                display_name="OpenAI",
                models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                available=True,
                description="OpenAI's GPT models for text generation"
            ),
            "anthropic": ProviderInfo(
                name="anthropic",
                display_name="Anthropic", 
                models=["claude-3-sonnet", "claude-3-haiku", "claude-2"],
                available=True,
                description="Anthropic's Claude models for conversational AI"
            ),
            "google": ProviderInfo(
                name="google",
                display_name="Google",
                models=["gemini-pro", "gemini-1.5-pro"],
                available=True,
                description="Google's Gemini models for multimodal AI"
            )
        }
        
        if provider_name not in providers_map:
            raise HTTPException(status_code=404, detail="Provider not found")
            
        return providers_map[provider_name]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider info: {str(e)}")