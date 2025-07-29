#!/usr/bin/env python3
"""
Consolidator for Whimperizer
Takes multiple AI-generated outputs and combines the best pieces into one final product
"""

import os
import sys
import yaml
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re
from collections import defaultdict

# AI Provider imports (reusing from whimperizer)
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

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logging(verbose: bool = False):
    """Setup logging for consolidator"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise Exception(f"Failed to load config from {config_path}: {e}")

def find_whimperized_files(whimper_dir: str, groups: Optional[List[str]] = None) -> Dict[str, List[Path]]:
    """Find whimperized files grouped by group key"""
    logger = logging.getLogger(__name__)
    
    whimper_path = Path(whimper_dir)
    if not whimper_path.exists():
        logger.error(f"Whimperized content directory not found: {whimper_dir}")
        return {}
    
    # Find all whimperized files
    all_files = list(whimper_path.glob('*whimperized*.md'))
    all_files.extend(list(whimper_path.glob('*whimperized*.txt')))
    
    # Group files by group key
    grouped_files = defaultdict(list)
    
    for file_path in all_files:
        # Extract group key from filename
        # Format: zaltz-2a-whimperized-iterative-gpt-4-1-20250724_164521.md
        name_parts = file_path.stem.split('-whimperized-')
        if len(name_parts) >= 2:
            full_prefix = name_parts[0]  # e.g., "zaltz-2a" or "zaltz-2a-16to21"
            
            # Extract actual group key (first two dash-separated parts)
            prefix_parts = full_prefix.split('-')
            if len(prefix_parts) >= 2:
                group_key = f"{prefix_parts[0]}-{prefix_parts[1]}"  # e.g., "zaltz-2a"
            else:
                group_key = full_prefix
            
            # Filter by groups if specified
            if groups and group_key not in groups:
                continue
            
            grouped_files[group_key].append(file_path)
    
    # Sort files within each group by timestamp (newest first)
    for group_key in grouped_files:
        grouped_files[group_key].sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return dict(grouped_files)

def read_file_content(file_path: Path) -> str:
    """Read content from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to read {file_path}: {e}")
        return ""

def create_consolidation_prompt(contents: List[str]) -> str:
    """Create the consolidation prompt for the AI"""
    base_prompt = """Please take all these examples and compare them against each other; take the best, MOST whimperized pieces from them all and combine it into one GREAT final product.

Focus on:
- The most vivid and childlike descriptions
- The best Wimpy Kid-style humor and voice
- The most engaging storytelling elements
- The clearest and most accessible language for children
- The most creative and imaginative elements

Here are the examples to consolidate:

"""
    
    # Add each content with a clear separator
    for i, content in enumerate(contents, 1):
        base_prompt += f"\n=== EXAMPLE {i} ===\n"
        base_prompt += content
        base_prompt += f"\n=== END EXAMPLE {i} ===\n"
    
    base_prompt += """

Now please create the BEST consolidated version by taking the strongest elements from all examples above. Make sure the final result maintains the Wimpy Kid style and is engaging for children."""
    
    return base_prompt

class AIProvider:
    """Base class for AI providers (simplified from whimperizer.py)"""
    def __init__(self, config: dict):
        self.config = config
    
    def generate(self, prompt: str) -> Optional[str]:
        raise NotImplementedError

class OpenAIProvider(AIProvider):
    def __init__(self, config: dict):
        super().__init__(config)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate(self, prompt: str) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model=self.config.get('model', 'gpt-4'),
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 4000)
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.getLogger(__name__).error(f"OpenAI API error: {e}")
            return None

class AnthropicProvider(AIProvider):
    def __init__(self, config: dict):
        super().__init__(config)
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not available")
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate(self, prompt: str) -> Optional[str]:
        try:
            response = self.client.messages.create(
                model=self.config.get('model', 'claude-3-sonnet-20240229'),
                max_tokens=self.config.get('max_tokens', 4000),
                temperature=self.config.get('temperature', 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logging.getLogger(__name__).error(f"Anthropic API error: {e}")
            return None

class GoogleProvider(AIProvider):
    def __init__(self, config: dict):
        super().__init__(config)
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google GenerativeAI library not available")
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.config.get('model', 'gemini-pro'))
    
    def generate(self, prompt: str) -> Optional[str]:
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config.get('temperature', 0.7),
                    max_output_tokens=self.config.get('max_tokens', 4000)
                )
            )
            return response.text
        except Exception as e:
            logging.getLogger(__name__).error(f"Google API error: {e}")
            return None

def create_ai_provider(config: dict) -> AIProvider:
    """Create AI provider based on configuration"""
    provider_type = config.get('provider', 'openai')
    
    if provider_type == 'openai':
        return OpenAIProvider(config)
    elif provider_type == 'anthropic':
        return AnthropicProvider(config)
    elif provider_type == 'google':
        return GoogleProvider(config)
    else:
        raise ValueError(f"Unknown provider: {provider_type}")

def consolidate_group(group_key: str, files: List[Path], ai_provider: AIProvider, output_dir: str, verbose: bool = False) -> Optional[str]:
    """Consolidate multiple whimperized files for a single group"""
    logger = logging.getLogger(__name__)
    
    if len(files) < 2:
        logger.warning(f"Group {group_key} has only {len(files)} file(s), skipping consolidation")
        return None
    
    logger.info(f"🔄 Consolidating {len(files)} files for group {group_key}")
    
    # Read all file contents
    contents = []
    for file_path in files:
        content = read_file_content(file_path)
        if content:
            contents.append(content)
            if verbose:
                logger.info(f"   📄 Loaded: {file_path.name}")
    
    if len(contents) < 2:
        logger.warning(f"Could not read enough valid content for group {group_key}")
        return None
    
    # Create consolidation prompt
    prompt = create_consolidation_prompt(contents)
    
    if verbose:
        logger.debug(f"Consolidation prompt length: {len(prompt)} characters")
    
    # Generate consolidated content
    logger.info(f"🤖 Running AI consolidation for group {group_key}")
    consolidated_content = ai_provider.generate(prompt)
    
    if not consolidated_content:
        logger.error(f"Failed to generate consolidated content for group {group_key}")
        return None
    
    # Save consolidated content
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{group_key}-whimperized-consolidated-{timestamp}.md"
    output_path = Path(output_dir) / output_filename
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(consolidated_content)
        
        logger.info(f"✅ Saved consolidated content: {output_path}")
        return str(output_path)
    
    except Exception as e:
        logger.error(f"Failed to save consolidated content: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Consolidator for Whimperizer - Combine multiple AI outputs into one best version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Consolidate all available groups
  python consolidator.py
  
  # Consolidate specific groups
  python consolidator.py --groups zaltz-1a zaltz-1b
  
  # Consolidate specific files
  python consolidator.py --files file1.md file2.md file3.md
  
  # Use custom directories and config
  python consolidator.py --whimper-dir ../output/whimperized_content --output-dir ../output/consolidated --config ../config/config.yaml
  
  # Verbose output
  python consolidator.py --groups zaltz-1a --verbose
        """
    )
    
    parser.add_argument('--groups', nargs='+', metavar='GROUP',
                        help='Consolidate specific groups (e.g., zaltz-1a zaltz-1b). If not specified, consolidates all available groups.')
    parser.add_argument('--files', nargs='+', metavar='FILE',
                        help='Specific whimperized files to consolidate (e.g., file1.md file2.md). Overrides --whimper-dir and --groups.')
    parser.add_argument('--whimper-dir', type=str, default='../output/whimperized_content',
                        help='Directory containing whimperized files (default: ../output/whimperized_content)')
    parser.add_argument('--output-dir', type=str, default='../output/whimperized_content',
                        help='Output directory for consolidated files (default: same as whimper-dir)')
    parser.add_argument('--config', type=str, default='../config/config.yaml',
                        help='Configuration file (default: ../config/config.yaml)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    logger = setup_logging(args.verbose)
    
    # Validate arguments
    if args.files and args.groups:
        logger.warning("Both --files and --groups specified. --files takes priority and --groups will be ignored.")
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Get consolidation config
    consolidation_config = config.get('multi_run', {}).get('consolidation', {})
    if not consolidation_config:
        logger.error("No consolidation configuration found in config file")
        sys.exit(1)
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find whimperized files
    if args.files:
        # Use specific files provided
        logger.info(f"🔍 Using specified files: {args.files}")
        grouped_files = {}
        
        # Validate files exist and group them
        valid_files = []
        for file_path_str in args.files:
            file_path = Path(file_path_str)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                continue
            if not file_path.suffix.lower() in ['.md', '.txt']:
                logger.warning(f"Skipping non-text file: {file_path}")
                continue
            valid_files.append(file_path)
        
        if not valid_files:
            logger.error("No valid whimperized files found in specified files")
            sys.exit(1)
        
        # Extract group key from first file for naming
        first_file = valid_files[0]
        name_parts = first_file.stem.split('-whimperized-')
        if len(name_parts) >= 2:
            full_prefix = name_parts[0]
            prefix_parts = full_prefix.split('-')
            if len(prefix_parts) >= 2:
                group_key = f"{prefix_parts[0]}-{prefix_parts[1]}"
            else:
                group_key = full_prefix
        else:
            group_key = "custom-consolidation"
        
        grouped_files[group_key] = valid_files
        logger.info(f"Grouped {len(valid_files)} files under key: {group_key}")
    else:
        # Auto-discover files in directory
        logger.info(f"🔍 Searching for whimperized files in: {args.whimper_dir}")
        grouped_files = find_whimperized_files(args.whimper_dir, args.groups)
        
        if not grouped_files:
            logger.error("No whimperized files found")
            sys.exit(1)
        
        logger.info(f"Found {len(grouped_files)} group(s) to consolidate:")
        for group_key, files in grouped_files.items():
            logger.info(f"  📁 {group_key}: {len(files)} files")
    
    if args.dry_run:
        logger.info("[DRY RUN] Would consolidate the above groups")
        sys.exit(0)
    
    # Create AI provider
    try:
        ai_provider = create_ai_provider(consolidation_config)
        logger.info(f"Using {consolidation_config['provider']}/{consolidation_config['model']} for consolidation")
    except Exception as e:
        logger.error(f"Failed to create AI provider: {e}")
        sys.exit(1)
    
    # Consolidate each group
    successful_consolidations = 0
    total_groups = len(grouped_files)
    
    for group_key, files in grouped_files.items():
        logger.info(f"\n📋 Processing group: {group_key}")
        
        result_path = consolidate_group(
            group_key, 
            files, 
            ai_provider, 
            args.output_dir, 
            args.verbose
        )
        
        if result_path:
            successful_consolidations += 1
        else:
            logger.error(f"Failed to consolidate group {group_key}")
    
    # Summary
    logger.info(f"\n📊 Consolidation Summary:")
    logger.info(f"Total groups: {total_groups}")
    logger.info(f"Successfully consolidated: {successful_consolidations}")
    logger.info(f"Failed: {total_groups - successful_consolidations}")
    
    if successful_consolidations == total_groups:
        logger.info("🎉 All groups consolidated successfully!")
        return 0
    elif successful_consolidations > 0:
        logger.warning("⚠️  Some groups failed")
        return 1
    else:
        logger.error("❌ All groups failed")
        return 2

if __name__ == '__main__':
    sys.exit(main())