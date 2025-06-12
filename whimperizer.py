#!/usr/bin/env python3
"""
Whimperizer - Convert downloaded content to Wimpy Kid style children's stories
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
            self.api_logger.info(f"Max tokens: {self.config['max_tokens']}")
            self.api_logger.info(f"Temperature: {self.config['temperature']}")
            self.api_logger.info(f"Number of messages: {len(messages)}")
            
            # Log message details (truncated for readability)
            for i, msg in enumerate(messages):
                content_preview = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                self.api_logger.debug(f"Message {i+1} ({msg['role']}): {content_preview}")
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=messages,
                max_tokens=self.config['max_tokens'],
                temperature=self.config['temperature']
            )
            
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
            
            # Log response content (truncated)
            response_content = response.choices[0].message.content
            content_preview = response_content[:500] + "..." if len(response_content) > 500 else response_content
            self.api_logger.debug(f"Response content: {content_preview}")
            
            return response_content
            
        except Exception as e:
            self.api_logger.error(f"OpenAI API error: {e}")
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
            self.api_logger.error(f"Anthropic API error: {e}")
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
            self.api_logger.error(f"Google API error: {e}")
            return None

class Whimperizer:
    def __init__(self, config_file='config.yaml', provider_override=None):
        self.config = self.load_config(config_file)
        self.provider_name = provider_override or os.getenv('DEFAULT_AI_PROVIDER') or self.config['api']['default_provider']
        self.ai_provider = self.setup_ai_provider()
        self.conversation_history = self.load_prompt()
        
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
    
    def load_prompt(self):
        """Load the conversation history from prompt file"""
        try:
            with open('whimperizer_prompt.txt', 'r', encoding='utf-8') as f:
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
            logger.error("whimperizer_prompt.txt not found")
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
        
        for file_info in group_files:
            content = self.read_file_content(file_info['path'])
            if content:
                combined_content.append(f"=== File: {file_info['filename']} ===\n{content}\n")
        
        return "\n".join(combined_content)
    
    def call_ai_api(self, content):
        """Call AI API to whimperize the content"""
        try:
            logger.info(f"Preparing API call for {self.provider_name}")
            
            # Build messages array
            if isinstance(self.conversation_history, list):
                # JSON format - use conversation history + new content
                messages = self.conversation_history.copy()
                new_message = f"Ok! Here's the next batch of whimperizer files!\n\n{content}"
                messages.append({
                    "role": "user",
                    "content": new_message
                })
                logger.debug(f"Using conversation history with {len(self.conversation_history)} messages")
            else:
                # Legacy plain text format
                full_content = f"{self.conversation_history}\n\n{content}"
                messages = [{
                    "role": "user", 
                    "content": full_content
                }]
                logger.debug("Using legacy plain text format")
            
            logger.info(f"Sending {len(messages)} messages to {self.provider_name}")
            
            # Calculate total input length for logging
            total_chars = sum(len(msg['content']) for msg in messages)
            logger.info(f"Total input length: {total_chars:,} characters")
            
            result = self.ai_provider.generate(messages)
            
            if result:
                logger.info(f"Received response from {self.provider_name}: {len(result):,} characters")
            else:
                logger.warning(f"No response received from {self.provider_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling {self.provider_name} API: {e}")
            return None
    
    def save_output(self, group_key, content):
        """Save the whimperized content to output file"""
        output_dir = Path(self.config['processing']['output_dir'])
        output_file = output_dir / f"{group_key}-whimperized.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved whimperized content to: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving output file {output_file}: {e}")
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
        whimperized_content = self.call_ai_api(combined_content)
        
        if not whimperized_content:
            logger.error(f"Failed to whimperize group {group_key}")
            return False
        
        # Save output
        return self.save_output(group_key, whimperized_content)
    
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
        total = len(grouped_files)
        
        for group_key, group_files in grouped_files.items():
            if self.process_group(group_key, group_files):
                successful += 1
        
        logger.info(f"Processing complete: {successful}/{total} groups successful")

def main():
    parser = argparse.ArgumentParser(description='Whimperize downloaded content into children\'s stories')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
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