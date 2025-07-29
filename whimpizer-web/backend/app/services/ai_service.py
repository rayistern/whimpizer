"""
AI Service - Portkey integration for unified AI provider access
"""
import openai
import os
from typing import Optional, Dict, Any
import asyncio
import logging

from app.core.config import settings
from app.models.jobs import AIProvider, JobConfig

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI processing using Portkey as the unified gateway"""
    
    def __init__(self):
        self.base_url = settings.AI_BASE_URL
        self.use_open_source = settings.USE_OPEN_SOURCE_PORTKEY
        
        if self.use_open_source:
            # For open source Portkey, we'll handle provider switching manually
            self.provider_configs = {
                "openai": {
                    "api_key": settings.OPENAI_API_KEY,
                    "base_url": settings.AI_BASE_URL if settings.AI_BASE_URL != "http://localhost:8787" else "https://api.openai.com/v1"
                },
                "anthropic": {
                    "api_key": settings.ANTHROPIC_API_KEY,
                    "base_url": settings.AI_BASE_URL if settings.AI_BASE_URL != "http://localhost:8787" else "https://api.anthropic.com"
                },
                "google": {
                    "api_key": settings.GOOGLE_API_KEY,
                    "base_url": settings.AI_BASE_URL if settings.AI_BASE_URL != "http://localhost:8787" else "https://generativelanguage.googleapis.com"
                }
            }
            # Initialize with OpenAI as default
            self.client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY or settings.AI_API_KEY,
                base_url=self.base_url
            )
        else:
            # Cloud Portkey mode
            self.client = openai.OpenAI(
                api_key=settings.AI_API_KEY,
                base_url=self.base_url
            )
    
    def _get_portkey_headers(self, provider: str, config: JobConfig) -> Dict[str, str]:
        """Get Portkey-specific headers for provider routing"""
        headers = {}
        
        if not self.use_open_source:
            # Cloud Portkey headers
            headers = {
                "x-portkey-provider": provider,
                "x-portkey-trace-id": f"{settings.PORTKEY_TRACE_ID_PREFIX}-{provider}",
            }
            
            # Add optional app ID if configured
            if settings.PORTKEY_APP_ID:
                headers["x-portkey-app-id"] = settings.PORTKEY_APP_ID
            
            # Add provider-specific configurations
            if provider == "anthropic":
                headers["x-portkey-anthropic-version"] = "2023-06-01"
            elif provider == "google":
                headers["x-portkey-google-vertex-project"] = ""  # Can be configured if needed
        
        return headers
    
    def _get_client_for_provider(self, provider: str) -> openai.OpenAI:
        """Get the appropriate client for the provider"""
        if self.use_open_source and provider in self.provider_configs:
            config = self.provider_configs[provider]
            return openai.OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"]
            )
        return self.client
    
    async def whimperize_content(
        self, 
        content: str, 
        config: JobConfig,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Transform content using AI via Portkey
        """
        try:
            # Default system prompt for whimperization
            if not system_prompt:
                # Customize prompt based on config
                tone_instructions = {
                    "funny": "Make it hilarious with lots of jokes, awkward situations, and Greg's classic sarcastic observations",
                    "dramatic": "Add more emotional depth and character development while keeping the Wimpy Kid voice",
                    "chill": "Keep it relaxed and casual, focusing on everyday situations and friendship",
                    "sarcastic": "Emphasize Greg's sarcastic inner voice and cynical observations about life"
                }
                
                age_instructions = {
                    "elementary": "Use simpler vocabulary and more straightforward situations that younger kids can relate to",
                    "middle_school": "Focus on typical middle school drama, friendships, and growing up challenges",
                    "high_school": "Include more mature themes while maintaining the Wimpy Kid voice"
                }
                
                tone_guide = tone_instructions.get(config.story_tone, tone_instructions["funny"])
                age_guide = age_instructions.get(config.target_age, age_instructions["middle_school"])
                
                system_prompt = f"""
You are tasked with converting web content into a children's story in the style of "Diary of a Wimpy Kid" by Jeff Kinney. 

Transform the given content into:
- First-person narrative from Greg Heffley's perspective
- Simple, conversational language
- {tone_guide}
- Include dialogue and character interactions
- Break content into diary-like entries with dates
- {age_guide}
- Keep the story engaging and appropriate for the target audience

{config.custom_prompt_addition if config.custom_prompt_addition else ""}

Format as markdown with proper headings and structure for PDF generation.
"""

            # Prepare the prompt
            user_prompt = f"""
Please convert this content into a Wimpy Kid style story:

{content}

Remember to:
- Use Greg Heffley's voice and perspective
- Include humor and relatable middle school situations  
- Structure as diary entries with dates
- Make it appropriate for children
- Format with proper markdown structure
"""

            # Set up provider-specific headers for Portkey
            headers = self._get_portkey_headers(config.ai_provider, config)
            
            # Get the appropriate client for this provider
            client = self._get_client_for_provider(config.ai_provider)
            
            # Make the API call
            if headers:
                # Cloud Portkey with headers
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=config.ai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    extra_headers=headers
                )
            else:
                # Direct provider call or open source Portkey
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=config.ai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens
                )
            
            # Extract the generated content
            generated_content = response.choices[0].message.content
            
            logger.info(f"Successfully generated content using {config.ai_provider}/{config.ai_model}")
            return generated_content
            
        except Exception as e:
            logger.error(f"AI processing failed: {str(e)}")
            raise Exception(f"AI processing error: {str(e)}")
    
    async def test_connection(self, provider: str = "openai") -> bool:
        """Test the AI connection"""
        try:
            headers = {"x-portkey-provider": provider}
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello, this is a test."}],
                max_tokens=10,
                extra_headers=headers
            )
            
            return True
            
        except Exception as e:
            logger.error(f"AI connection test failed: {str(e)}")
            return False
    
    def get_available_models(self, provider: str) -> list:
        """Get available models for a provider"""
        model_map = {
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-2.1"],
            "google": ["gemini-pro", "gemini-1.5-pro"]
        }
        
        return model_map.get(provider, [])