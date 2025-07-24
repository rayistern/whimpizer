#!/usr/bin/env python3
"""
Whimperizer - Convert downloaded content to Wimpy Kid style children's stories

Features:
- Multi-provider AI support (OpenAI, Anthropic, Google)
- Fallback system: If primary model fails, automatically tries backup models
- Graceful failure handling: Groups fail completely if all fallbacks are exhausted
- Comprehensive logging and error reporting
"""

import os
import yaml
import argparse
import logging
from pathlib import Path
import re
import json
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from dotenv import load_dotenv

# AI Provider imports
import openai
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging(log_level=logging.INFO):
    """Setup comprehensive logging with file and console handlers"""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.FileHandler('logs/whimperizer.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Separate file handler for API logs
    api_handler = logging.FileHandler('logs/api_calls.log', encoding='utf-8')
    api_handler.setLevel(logging.DEBUG)
    api_handler.setFormatter(detailed_formatter)
    
    # API logger
    api_logger = logging.getLogger('whimperizer.api')
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.DEBUG)
    api_logger.propagate = False  # Don't propagate to root logger
    
    return logging.getLogger(__name__)

logger = setup_logging()

class AIProvider:
    """Base class for AI providers"""
    def __init__(self, config: dict):
        self.config = config
    
    def generate(self, messages: List[Dict]) -> Optional[str]:
        raise NotImplementedError

class OpenAIProvider(AIProvider):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_logger = logging.getLogger('whimperizer.api.openai')
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=config.get('base_url', 'https://api.openai.com/v1')
        )
        self.api_logger.info(f"OpenAI client initialized with model: {config['model']}")
    
    def generate(self, messages: List[Dict]) -> Optional[str]:
        try:
            # Log request details
            self.api_logger.info("=== OpenAI API Request ===")
            self.api_logger.info(f"Model: {self.config['model']}")
            self.api_logger.info(f"Max tokens: {self.config.get('max_tokens', 'Not specified')}")
            self.api_logger.info(f"Temperature: {self.config.get('temperature', 'Not specified')}")
            self.api_logger.info(f"Number of messages: {len(messages)}")
            
            # Log message details (FULL content for debugging)
            for i, msg in enumerate(messages):
                self.api_logger.debug(f"Message {i+1} ({msg['role']}): {msg['content']}")
            
            # Make API call - handle different model parameter requirements
            api_params = {
                'model': self.config['model'],
                'messages': messages,
            }
            
            # Only add temperature for non-reasoning models
            model_name = self.config['model'].lower()
            is_reasoning_model = any(x in model_name for x in ['o1-preview', 'o1-mini', 'o1', 'o4-mini'])
            
            if not is_reasoning_model:
                api_params['temperature'] = self.config['temperature']
            
            # Add max_tokens only if specified in config and not a reasoning model
            if self.config.get('max_tokens') and not is_reasoning_model:
                api_params['max_tokens'] = self.config['max_tokens']
            elif self.config.get('max_tokens') and is_reasoning_model:
                # Reasoning models use max_completion_tokens
                api_params['max_completion_tokens'] = self.config['max_tokens']
            
            self.api_logger.info(f"API parameters for {model_name}: {list(api_params.keys())}")
            
            response = self.client.chat.completions.create(**api_params)
            
            # Log response details
            self.api_logger.info("=== OpenAI API Response ===")
            self.api_logger.info(f"Response ID: {response.id}")
            self.api_logger.info(f"Model used: {response.model}")
            self.api_logger.info(f"Finish reason: {response.choices[0].finish_reason}")
            
            # Log token usage
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                self.api_logger.info(f"Token usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
                
                # Calculate approximate cost (rough estimates)
                if 'gpt-4' in self.config['model']:
                    prompt_cost = usage.prompt_tokens * 0.00003  # $0.03 per 1K tokens
                    completion_cost = usage.completion_tokens * 0.00006  # $0.06 per 1K tokens
                elif 'gpt-3.5' in self.config['model']:
                    prompt_cost = usage.prompt_tokens * 0.0000015  # $0.0015 per 1K tokens
                    completion_cost = usage.completion_tokens * 0.000002  # $0.002 per 1K tokens
                else:
                    prompt_cost = completion_cost = 0
                
                total_cost = prompt_cost + completion_cost
                self.api_logger.info(f"Estimated cost: ${total_cost:.6f}")
            
            # Log response content (FULL content for debugging)
            response_content = response.choices[0].message.content
            self.api_logger.debug(f"Response content: {response_content}")
            
            return response_content
            
        except Exception as e:
            error_msg = f"OpenAI API error: {e}"
            self.api_logger.error(error_msg)
            
            # Print full error details to console
            print(f"\n❌ OpenAI API Error:")
            print(f"   {str(e)}")
            
            # Try to extract and display structured error details
            error_details = None
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    error_details = e.response.json()
                except:
                    pass
            elif hasattr(e, 'body'):
                try:
                    import json
                    error_details = json.loads(e.body) if isinstance(e.body, str) else e.body
                except:
                    error_details = {"body": str(e.body)}
            
            if error_details:
                print(f"\n   📋 Full Error Details:")
                if isinstance(error_details, dict) and 'error' in error_details:
                    error_info = error_details['error']
                    print(f"      • Message: {error_info.get('message', 'N/A')}")
                    print(f"      • Type: {error_info.get('type', 'N/A')}")
                    print(f"      • Code: {error_info.get('code', 'N/A')}")
                    if 'param' in error_info:
                        print(f"      • Parameter: {error_info['param']}")
                else:
                    print(f"      {error_details}")
                self.api_logger.error(f"API Error details: {error_details}")
            
            # Provide specific guidance for common errors
            error_str = str(e).lower()
            if 'max_tokens' in error_str and 'max_completion_tokens' in error_str:
                print(f"\n   💡 Suggestion: This looks like a reasoning model (o1-series). Try:")
                print(f"      1. Set model to 'gpt-4-turbo' or 'gpt-3.5-turbo' in config.yaml")
                print(f"      2. Or remove 'max_tokens' from config.yaml if not needed")
            elif 'temperature' in error_str and 'does not support' in error_str:
                print(f"\n   💡 Suggestion: This reasoning model doesn't support custom temperature. Try:")
                print(f"      1. Remove or comment out 'temperature' line in config.yaml")
                print(f"      2. Or change model to 'gpt-4-turbo' which supports temperature")
            elif 'context length' in error_str:
                print(f"\n   💡 Suggestion: Content too large for model context. Try:")
                print(f"      1. Use 'gpt-4-turbo' model (128K context)")
                print(f"      2. Or split into smaller groups")
            elif 'api key' in error_str:
                print(f"\n   💡 Suggestion: Check your API key in .env file")
            elif 'rate limit' in error_str:
                print(f"\n   💡 Suggestion: You've hit API rate limits, wait a moment and try again")
            
            return None

class AnthropicProvider(AIProvider):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_logger = logging.getLogger('whimperizer.api.anthropic')
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.api_logger.info(f"Anthropic client initialized with model: {config['model']}")
    
    def generate(self, messages: List[Dict]) -> Optional[str]:
        try:
            # Log request details
            self.api_logger.info("=== Anthropic API Request ===")
            self.api_logger.info(f"Model: {self.config['model']}")
            self.api_logger.info(f"Max tokens: {self.config['max_tokens']}")
            self.api_logger.info(f"Temperature: {self.config['temperature']}")
            self.api_logger.info(f"Number of messages: {len(messages)}")
            
            # Log message details (truncated for readability)
            for i, msg in enumerate(messages):
                content_preview = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                self.api_logger.debug(f"Message {i+1} ({msg['role']}): {content_preview}")
            
            # Make API call
            response = self.client.messages.create(
                model=self.config['model'],
                max_tokens=self.config['max_tokens'],
                temperature=self.config['temperature'],
                messages=messages
            )
            
            # Log response details
            self.api_logger.info("=== Anthropic API Response ===")
            self.api_logger.info(f"Response ID: {response.id}")
            self.api_logger.info(f"Model used: {response.model}")
            self.api_logger.info(f"Stop reason: {response.stop_reason}")
            
            # Log token usage
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                self.api_logger.info(f"Token usage - Input: {usage.input_tokens}, Output: {usage.output_tokens}")
                
                # Calculate approximate cost for Claude
                if 'claude-3-opus' in self.config['model']:
                    input_cost = usage.input_tokens * 0.000015  # $15 per 1M tokens
                    output_cost = usage.output_tokens * 0.000075  # $75 per 1M tokens
                elif 'claude-3-sonnet' in self.config['model']:
                    input_cost = usage.input_tokens * 0.000003  # $3 per 1M tokens
                    output_cost = usage.output_tokens * 0.000015  # $15 per 1M tokens
                elif 'claude-3-haiku' in self.config['model']:
                    input_cost = usage.input_tokens * 0.00000025  # $0.25 per 1M tokens
                    output_cost = usage.output_tokens * 0.00000125  # $1.25 per 1M tokens
                else:
                    input_cost = output_cost = 0
                
                total_cost = input_cost + output_cost
                self.api_logger.info(f"Estimated cost: ${total_cost:.6f}")
            
            # Log response content (truncated)
            response_content = response.content[0].text
            content_preview = response_content[:500] + "..." if len(response_content) > 500 else response_content
            self.api_logger.debug(f"Response content: {content_preview}")
            
            return response_content
            
        except Exception as e:
            error_msg = f"Anthropic API error: {e}"
            self.api_logger.error(error_msg)
            # Also log to console for immediate visibility
            print(f"\n❌ {error_msg}")
            
            # If it's an Anthropic API error, try to extract more details
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    error_details = e.response.json()
                    print(f"   Error details: {error_details}")
                    self.api_logger.error(f"API Error details: {error_details}")
                except:
                    pass
            elif hasattr(e, 'body'):
                print(f"   Error body: {e.body}")
                self.api_logger.error(f"API Error body: {e.body}")
            
            return None

class GoogleProvider(AIProvider):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_logger = logging.getLogger('whimperizer.api.google')
        
        if not GOOGLE_AVAILABLE:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.config['model'])
        self.api_logger.info(f"Google client initialized with model: {config['model']}")
    
    def generate(self, messages: List[Dict]) -> Optional[str]:
        try:
            # Log request details
            self.api_logger.info("=== Google API Request ===")
            self.api_logger.info(f"Model: {self.config['model']}")
            self.api_logger.info(f"Max tokens: {self.config['max_tokens']}")
            self.api_logger.info(f"Temperature: {self.config['temperature']}")
            self.api_logger.info(f"Number of messages: {len(messages)}")
            
            # Convert messages to Google's format (simple concatenation for now)
            # Google's chat models have different message format, this is a simplified approach
            prompt = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            # Log message details (truncated for readability)
            for i, msg in enumerate(messages):
                content_preview = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                self.api_logger.debug(f"Message {i+1} ({msg['role']}): {content_preview}")
            
            prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
            self.api_logger.debug(f"Combined prompt: {prompt_preview}")
            
            # Make API call
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config['max_tokens'],
                    temperature=self.config['temperature']
                )
            )
            
            # Log response details
            self.api_logger.info("=== Google API Response ===")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                self.api_logger.info(f"Finish reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings'):
                    self.api_logger.info(f"Safety ratings: {candidate.safety_ratings}")
            
            # Log token usage (if available)
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                self.api_logger.info(f"Token usage - Prompt: {usage.prompt_token_count}, Candidates: {usage.candidates_token_count}, Total: {usage.total_token_count}")
                
                # Google pricing is generally lower, rough estimates
                total_tokens = usage.total_token_count
                estimated_cost = total_tokens * 0.000001  # Very rough estimate
                self.api_logger.info(f"Estimated cost: ${estimated_cost:.6f}")
            
            # Log response content (truncated)
            response_content = response.text
            content_preview = response_content[:500] + "..." if len(response_content) > 500 else response_content
            self.api_logger.debug(f"Response content: {content_preview}")
            
            return response_content
            
        except Exception as e:
            error_msg = f"Google API error: {e}"
            self.api_logger.error(error_msg)
            # Also log to console for immediate visibility
            print(f"\n❌ {error_msg}")
            
            # If it's a Google API error, try to extract more details
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    error_details = e.response.json()
                    print(f"   Error details: {error_details}")
                    self.api_logger.error(f"API Error details: {error_details}")
                except:
                    pass
            elif hasattr(e, 'details'):
                print(f"   Error details: {e.details}")
                self.api_logger.error(f"API Error details: {e.details}")
            
            return None

class Whimperizer:
    def __init__(self, config_file='../config/config.yaml', provider_override=None):
        self.config = self.load_config(config_file)
        self.provider_name = provider_override or os.getenv('DEFAULT_AI_PROVIDER') or self.config['api']['default_provider']
        self.ai_provider = self.setup_ai_provider()
        self.conversation_history = self.load_prompt()
        
        # Log fallback configuration
        fallbacks = self.config.get('api', {}).get('fallbacks', {})
        if fallbacks:
            logger.info("Fallback system configured:")
            for key, fb_config in fallbacks.items():
                logger.info(f"  {key}: {fb_config['provider']} ({fb_config.get('model', 'default')})")
            print(f"🛡️  Fallback system active: {len(fallbacks)} backup models configured")
        else:
            logger.warning("No fallback models configured - single point of failure")
            print(f"⚠️  No fallback models configured - consider adding fallbacks to config")
        
        # Create output directory
        os.makedirs(self.config['processing']['output_dir'], exist_ok=True)
    
    def load_config(self, config_file):
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def setup_ai_provider(self):
        """Setup AI provider based on configuration"""
        provider_config = self.config['api']['providers'].get(self.provider_name)
        if not provider_config:
            raise ValueError(f"Provider '{self.provider_name}' not found in configuration")
        
        logger.info(f"Setting up AI provider: {self.provider_name}")
        
        if self.provider_name == 'openai':
            return OpenAIProvider(provider_config)
        elif self.provider_name == 'anthropic':
            return AnthropicProvider(provider_config)
        elif self.provider_name == 'google':
            return GoogleProvider(provider_config)
        else:
            raise ValueError(f"Unsupported provider: {self.provider_name}")
    
    def create_fallback_provider(self, fallback_config):
        """Create a fallback AI provider from fallback configuration"""
        provider_name = fallback_config['provider']
        
        # Get base provider config and override with fallback settings
        base_config = self.config['api']['providers'].get(provider_name, {}).copy()
        base_config.update(fallback_config)
        
        logger.info(f"Creating fallback provider: {provider_name} with model {fallback_config.get('model', 'default')}")
        
        if provider_name == 'openai':
            return OpenAIProvider(base_config)
        elif provider_name == 'anthropic':
            return AnthropicProvider(base_config)
        elif provider_name == 'google':
            return GoogleProvider(base_config)
        else:
            raise ValueError(f"Unsupported fallback provider: {provider_name}")
    
    def load_prompt(self):
        """Load the conversation history from prompt file"""
        try:
            with open('../config/whimperizer_prompt.txt', 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Try to parse as JSON array first
            if content.startswith('['):
                try:
                    conversation_history = json.loads(content)
                    logger.info("Loaded conversation history as JSON")
                    return conversation_history
                except json.JSONDecodeError:
                    logger.warning("Failed to parse as JSON, treating as plain text")
            
            # Fallback to plain text (legacy format)
            logger.info("Loaded prompt template as plain text")
            return content
            
        except FileNotFoundError:
            logger.error("../config/whimperizer_prompt.txt not found")
            raise
    
    def parse_filename(self, filename):
        """Parse filename to extract group1, group2, and line number"""
        # Expected format: group1-group2-line.txt
        pattern = r'^(.+?)-(.+?)-(.+?)\.txt$'
        match = re.match(pattern, filename)
        if match:
            return {
                'group1': match.group(1),
                'group2': match.group(2),
                'line': match.group(3),
                'filename': filename
            }
        return None
    
    def get_input_files(self):
        """Get all input files and group them"""
        input_dir = Path(self.config['processing']['input_dir'])
        files = []
        
        for file_path in input_dir.glob('*.txt'):
            if file_path.name == '.gitkeep':
                continue
                
            parsed = self.parse_filename(file_path.name)
            if parsed:
                parsed['path'] = file_path
                files.append(parsed)
            else:
                logger.warning(f"Skipping file with unexpected format: {file_path.name}")
        
        logger.info(f"Found {len(files)} input files")
        return files
    
    def group_files(self, files):
        """Group files by group1+group2 combination"""
        groups = defaultdict(list)
        
        for file_info in files:
            group_key = f"{file_info['group1']}-{file_info['group2']}"
            groups[group_key].append(file_info)
        
        # Sort files within each group by line number
        if self.config['options']['sort_by_line']:
            for group_key in groups:
                groups[group_key].sort(key=lambda x: float(x['line']))
        
        logger.info(f"Grouped files into {len(groups)} combinations")
        return dict(groups)
    
    def read_file_content(self, file_path):
        """Read content from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def combine_group_content(self, group_files):
        """Combine content from all files in a group"""
        combined_content = []
        
        logger.info(f"Combining {len(group_files)} files:")
        for i, file_info in enumerate(group_files, 1):
            logger.info(f"  {i}. {file_info['filename']}")
            content = self.read_file_content(file_info['path'])
            if content:
                combined_content.append(f"=== File: {file_info['filename']} ===\n{content}\n")
        
        total_chars = sum(len(section) for section in combined_content)
        logger.info(f"Combined content: {len(combined_content)} sections, {total_chars:,} characters")
        
        return "\n".join(combined_content)
    
    def call_ai_api_with_fallbacks(self, messages):
        """Core fallback logic - try primary provider then fallbacks"""
        # Calculate total input length for logging
        total_chars = sum(len(msg['content']) for msg in messages)
        logger.info(f"Total input length: {total_chars:,} characters")
        
        # Try primary provider first
        provider_attempts = [
            ("primary", self.provider_name, self.ai_provider)
        ]
        
        # Add fallback providers if configured
        fallbacks = self.config.get('api', {}).get('fallbacks', {})
        for fallback_key in ['fallback_1', 'fallback_2']:
            if fallback_key in fallbacks:
                try:
                    fallback_config = fallbacks[fallback_key]
                    fallback_provider = self.create_fallback_provider(fallback_config)
                    provider_name = f"{fallback_config['provider']} ({fallback_config.get('model', 'default')})"
                    provider_attempts.append((fallback_key, provider_name, fallback_provider))
                except Exception as e:
                    logger.error(f"Failed to create {fallback_key} provider: {e}")
        
        logger.info(f"Will attempt {len(provider_attempts)} provider(s) in sequence")
        
        # Try each provider in sequence
        for attempt_num, (attempt_type, provider_name, provider) in enumerate(provider_attempts, 1):
            try:
                logger.info(f"Attempt {attempt_num}/{len(provider_attempts)}: {attempt_type} provider ({provider_name})")
                print(f"🤖 Attempt {attempt_num}/{len(provider_attempts)}: Trying {provider_name}...")
                
                result = provider.generate(messages)
                
                if result:
                    logger.info(f"SUCCESS: {attempt_type} provider ({provider_name}) returned {len(result):,} characters")
                    print(f"✅ Success with {provider_name}")
                    return result
                else:
                    logger.warning(f"FAILURE: {attempt_type} provider ({provider_name}) returned no content")
                    print(f"❌ No response from {provider_name}")
                    
            except Exception as e:
                logger.error(f"FAILURE: {attempt_type} provider ({provider_name}) failed: {e}")
                print(f"❌ {provider_name} failed: {str(e)[:100]}...")
        
        # All providers failed
        logger.error(f"All {len(provider_attempts)} provider attempts failed")
        print(f"💥 All {len(provider_attempts)} providers failed - no fallbacks remaining")
        return None
    
    def call_ai_api(self, content):
        """Call AI API to whimperize the content with fallback support"""
        # Build messages array once
        if isinstance(self.conversation_history, list):
            # JSON format - use conversation history + new content
            messages = self.conversation_history.copy()
            new_message = f"""Ok fine. So here's a full chapter from the book; let's try with this, please generate a full Whimpy Kid rendition off of this text now! Here are those files of chapter 1 of the original Hillel diary (the version for grown ups). Output just the Whimpy version now, in markdown! And don't shorten it vs what I'm giving you here.

{content}"""
            messages.append({
                "role": "user",
                "content": new_message
            })
            logger.debug(f"Using conversation history with {len(self.conversation_history)} messages")
            
            # DEBUG: Show what we're actually sending
            print(f"\n🔍 DEBUG: Final message being sent to AI:")
            print(f"   Last message length: {len(new_message):,} characters")
            print(f"   First 1000 chars of combined content:")
            print(content[:1000])
            print(f"   Last 500 chars of combined content:")
            print(content[-500:])
        else:
            # Legacy plain text format
            full_content = f"{self.conversation_history}\n\n{content}"
            messages = [{
                "role": "user", 
                "content": full_content
            }]
            logger.debug("Using legacy plain text format")
        
        return self.call_ai_api_with_fallbacks(messages)
    
    def call_iterative_api(self, group_files, short_response):
        """Call AI API iteratively for each file when response is too short"""
        try:
            logger.info(f"Starting iterative processing of {len(group_files)} files")
            print(f"🔄 Response was short - processing each story individually...")
            
            # Start with conversation history + short response as overview
            if isinstance(self.conversation_history, list):
                messages = self.conversation_history.copy()
                
                # Add short response as overview
                messages.append({
                    "role": "assistant", 
                    "content": short_response
                })
                
                all_parts = []
                
                for i, file_info in enumerate(group_files, 1):
                    logger.info(f"Processing file {i}/{len(group_files)}: {file_info['filename']}")
                    print(f"📖 Processing story {i}/{len(group_files)}: {file_info['filename']}")
                    
                    # Read individual file content
                    file_content = self.read_file_content(file_info['path'])
                    if not file_content:
                        logger.warning(f"Could not read file {file_info['filename']}")
                        continue
                    
                    # Create message for this specific file
                    if i == 1:
                        file_message = f"""I think there's A LOT of solid content which could make this story much less BORING. Let's instead take this one piece at a time. Here's the first part of the original, let's WHIMPERIZE this one specific incident!

{file_content}

Please give me a full Wimpy Kid style diary entry for just this incident. Don't worry about the other parts - we'll do those next."""
                    else:
                        file_message = f"""OK! Here's the next piece from the original. Let's whimperize this specific incident too:

{file_content}

Please give me another Wimpy Kid style diary entry for this incident. Keep the same character voice and style as before."""
                    
                    messages.append({
                        "role": "user",
                        "content": file_message
                    })
                    
                    # Get response for this file using fallback system
                    result = self.call_ai_api_with_fallbacks(messages)
                    
                    if result:
                        logger.info(f"File {i} response: {len(result):,} characters")
                        print(f"   ✅ Got {len(result):,} characters for this incident")
                        all_parts.append(result)
                        
                        # Add AI's response to conversation for next iteration
                        messages.append({
                            "role": "assistant",
                            "content": result
                        })
                    else:
                        logger.error(f"Failed to process file {file_info['filename']} - all fallbacks exhausted")
                        print(f"   💥 Failed to process {file_info['filename']} - all API providers and fallbacks exhausted")
                        print(f"   🚫 Stopping iterative processing - group cannot be completed")
                        return None  # Return None to indicate complete failure
                
                if all_parts:
                    # Combine all parts into one coherent story
                    combined_result = "\n\n".join(all_parts)
                    logger.info(f"Iterative processing complete: {len(combined_result):,} total characters")
                    print(f"🎯 Iterative processing complete: {len(combined_result):,} total characters")
                    return combined_result
                else:
                    logger.error("No parts successfully processed")
                    return None
            else:
                logger.warning("Using legacy format for iterative processing - not supported")
                return None
            
        except Exception as e:
            logger.error(f"Error in iterative API processing: {e}")
            return None
    
    def save_output(self, group_key, content, mode="normal", line_numbers=None):
        """Save the whimperized content to output file"""
        from datetime import datetime
        
        output_dir = Path(self.config['processing']['output_dir'])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Include line numbers in filename if provided
        if line_numbers:
            if len(line_numbers) == 1:
                line_suffix = f"-{line_numbers[0]}"
            else:
                # Multiple line numbers: show range or list
                sorted_lines = sorted(line_numbers, key=lambda x: float(x))
                if len(sorted_lines) <= 3:
                    line_suffix = f"-{'-'.join(sorted_lines)}"
                else:
                    line_suffix = f"-{sorted_lines[0]}to{sorted_lines[-1]}"
        else:
            line_suffix = ""
        
        output_file = output_dir / f"{group_key}{line_suffix}-whimperized-{mode}-{timestamp}.md"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved {mode} whimperized content to: {output_file}")
            print(f"   💾 Saved {mode} version to: {output_file}")
            return str(output_file)  # Return filename for summary
        except Exception as e:
            logger.error(f"Error saving output file {output_file}: {e}")
            print(f"   ❌ Failed to save {mode} version: {output_file}")
            return False
    
    def process_group(self, group_key, group_files):
        """Process a single group of files"""
        logger.info(f"Processing group: {group_key} ({len(group_files)} files)")
        
        # Combine content from all files in the group
        combined_content = self.combine_group_content(group_files)
        
        if not combined_content.strip():
            logger.warning(f"No content found for group {group_key}")
            return False
        
        # Call AI API to whimperize
        logger.info(f"Calling {self.provider_name} API for group {group_key}...")
        print(f"🤖 Calling {self.provider_name} API for group {group_key}...")
        
        whimperized_content = self.call_ai_api(combined_content)
        
        if not whimperized_content:
            error_msg = f"Failed to whimperize group {group_key} - all fallback models exhausted"
            logger.error(error_msg)
            print(f"💥 Group {group_key} failed: All API providers and fallbacks exhausted")
            print(f"   This group will not be processed further.")
            return False
        
        # Extract line numbers from group files for filename
        line_numbers = [file_info['line'] for file_info in group_files]
        
        # Save the initial response
        normal_file = self.save_output(group_key, whimperized_content, "normal", line_numbers)
        
        # Always use iterative processing for more complete results
        logger.info(f"Starting iterative processing for more comprehensive coverage...")
        print(f"🔄 Using iterative processing for comprehensive whimperization...")
        
        followup_response = self.call_iterative_api(group_files, whimperized_content)
        
        final_content = whimperized_content
        final_mode = "normal"
        iterative_file = None
        
        if followup_response:
            # Save the iterative response
            iterative_file = self.save_output(group_key, followup_response, "iterative", line_numbers)
            
            if len(followup_response) > len(whimperized_content):
                logger.info(f"Iterative processing provided longer response ({len(followup_response)} vs {len(whimperized_content)} chars)")
                print(f"📈 Iterative processing expanded content: {len(whimperized_content):,} → {len(followup_response):,} chars")
                print(f"🎯 Using iterative version for final output")
                final_content = followup_response
                final_mode = "iterative"
            else:
                logger.info(f"Iterative processing provided same/shorter response, keeping original")
                print(f"🎯 Using normal version for final output")
        else:
            logger.warning("Iterative processing failed, keeping original response")
            print(f"🎯 Using normal version for final output")
        
        # Log content-only character counts (input files vs final output, excluding conversation history)
        input_chars = len(combined_content)
        output_chars = len(final_content)
        ratio = output_chars / input_chars if input_chars > 0 else 0
        change_percent = ((output_chars - input_chars) / input_chars * 100) if input_chars > 0 else 0
        
        logger.info(f"=== CONTENT TRANSFORMATION METRICS ===")
        logger.info(f"Input content (files only): {input_chars:,} characters")
        logger.info(f"Final output content ({final_mode}): {output_chars:,} characters")
        logger.info(f"Size ratio: {ratio:.2f}x")
        if change_percent >= 0:
            logger.info(f"Content expansion: +{change_percent:.1f}%")
        else:
            logger.info(f"Content reduction: {change_percent:.1f}%")
        
        # Console output with content metrics
        if change_percent >= 0:
            print(f"✅ Successfully whimperized group {group_key}")
            print(f"   📈 Final content expanded: {input_chars:,} → {output_chars:,} chars (+{change_percent:.1f}%)")
        else:
            print(f"✅ Successfully whimperized group {group_key}")
            print(f"   📉 Final content condensed: {input_chars:,} → {output_chars:,} chars ({change_percent:.1f}%)")
        
        # Return info about both files and which one to use
        return {
            "normal_file": normal_file,
            "iterative_file": iterative_file,
            "final_mode": final_mode,
            "final_file": iterative_file if final_mode == "iterative" else normal_file
        }
    
    def run(self, target_groups=None):
        """Main processing function"""
        logger.info("Starting whimperizer processing...")
        
        # Get and group input files
        files = self.get_input_files()
        if not files:
            logger.error("No input files found")
            return
        
        grouped_files = self.group_files(files)
        
        # Filter to target groups if specified
        if target_groups:
            filtered_groups = {}
            for target in target_groups:
                if target in grouped_files:
                    filtered_groups[target] = grouped_files[target]
                else:
                    logger.warning(f"Target group '{target}' not found in input files")
            grouped_files = filtered_groups
        
        if not grouped_files:
            logger.error("No groups to process")
            return
        
        # Process each group
        successful = 0
        failed = 0
        group_results = []
        total = len(grouped_files)
        
        print(f"\n📁 Processing {total} group(s) with {self.provider_name} (+ fallbacks):")
        
        for group_key, group_files in grouped_files.items():
            logger.info(f"=== Starting group {group_key} ({len(group_files)} files) ===")
            result = self.process_group(group_key, group_files)
            if result:
                successful += 1
                group_results.append(result)
                logger.info(f"=== Group {group_key} completed successfully ===")
            else:
                failed += 1
                logger.error(f"=== Group {group_key} failed completely ===")
        
        # Final summary
        logger.info(f"Processing complete: {successful}/{total} groups successful, {failed} failed")
        print(f"\n🎯 Processing complete: {successful}/{total} groups successful")
        
        if failed > 0:
            print(f"💥 {failed} group(s) failed after all fallback attempts")
            print(f"   This typically indicates API rate limits, authentication issues, or content policy violations")
            print(f"   Check the logs above for specific error details from each provider")
        
        if successful > 0:
            output_dir = Path(self.config['processing']['output_dir']).resolve()
            print(f"✨ {successful} group(s) processed successfully!")
            print(f"\n📁 Output directory: {output_dir}")
            print(f"📝 Generated files:")
            for result in group_results:
                print(f"   • {Path(result['normal_file']).name} (normal)")
                if result['iterative_file']:
                    print(f"   • {Path(result['iterative_file']).name} (iterative)")
                print(f"   🎯 Final choice: {Path(result['final_file']).name} ({result['final_mode']})")
        elif total > 0:
            print(f"❌ No groups were successfully processed")
        
        return group_results

def main():
    parser = argparse.ArgumentParser(description='Whimperize downloaded content into children\'s stories')
    parser.add_argument('--config', default='../config/config.yaml', help='Configuration file path')
    parser.add_argument('--groups', nargs='+', help='Specific group1-group2 combinations to process (e.g., zaltz-1a)')
    parser.add_argument('--list-groups', action='store_true', help='List available groups and exit')
    parser.add_argument('--provider', choices=['openai', 'anthropic', 'google'], 
                       help='AI provider to use (overrides config and env var)')
    parser.add_argument('--list-providers', action='store_true', help='List available AI providers and exit')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Set logging level (default: INFO)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (equivalent to --log-level DEBUG)')
    
    args = parser.parse_args()
    
    # Setup logging with specified level
    log_level = logging.DEBUG if args.verbose else getattr(logging, args.log_level)
    global logger
    logger = setup_logging(log_level)
    
    if args.list_providers:
        print("Available AI providers:")
        print("  openai - OpenAI GPT models")
        if ANTHROPIC_AVAILABLE:
            print("  anthropic - Anthropic Claude models")
        else:
            print("  anthropic - (not installed: pip install anthropic)")
        if GOOGLE_AVAILABLE:
            print("  google - Google Gemini models")
        else:
            print("  google - (not installed: pip install google-generativeai)")
        return
    
    try:
        whimperizer = Whimperizer(args.config, args.provider)
        
        if args.list_groups:
            files = whimperizer.get_input_files()
            grouped_files = whimperizer.group_files(files)
            print("Available groups:")
            for group_key, group_files in grouped_files.items():
                print(f"  {group_key} ({len(group_files)} files)")
            return
        
        whimperizer.run(args.groups)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 