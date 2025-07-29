#!/usr/bin/env python3
"""
Multi-Runner for Whimperizer
Handles running the whimperizer multiple times with different models
"""

import os
import sys
import yaml
import argparse
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

def setup_logging(verbose: bool = False):
    """Setup logging for multi-runner"""
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

def get_run_model_config(config: dict, run_number: int) -> Optional[Dict]:
    """Get model configuration for a specific run number"""
    multi_run_config = config.get('multi_run', {})
    run_models = multi_run_config.get('run_models', {})
    
    # Look for run_N_model
    run_key = f"run_{run_number}_model"
    if run_key in run_models:
        return run_models[run_key]
    
    # If no specific model, return None (will use default)
    return None

def create_temp_config(base_config: dict, run_model_config: Dict, run_number: int, temp_dir: Path) -> str:
    """Create a temporary config file with run-specific model settings"""
    # Make a copy of the base config
    temp_config = base_config.copy()
    
    # Override the default provider and model settings
    if 'api' not in temp_config:
        temp_config['api'] = {}
    
    # Set the provider from run model config
    temp_config['api']['default_provider'] = run_model_config['provider']
    
    # Update provider-specific settings
    if 'providers' not in temp_config['api']:
        temp_config['api']['providers'] = {}
    
    provider = run_model_config['provider']
    if provider not in temp_config['api']['providers']:
        temp_config['api']['providers'][provider] = {}
    
    # Update the model settings for this provider
    temp_config['api']['providers'][provider]['model'] = run_model_config['model']
    temp_config['api']['providers'][provider]['temperature'] = run_model_config.get('temperature', 0.7)
    
    if 'max_tokens' in run_model_config:
        temp_config['api']['providers'][provider]['max_tokens'] = run_model_config['max_tokens']
    
    # Write temporary config file
    temp_config_path = temp_dir / f"config_run_{run_number}.yaml"
    with open(temp_config_path, 'w') as f:
        yaml.dump(temp_config, f, default_flow_style=False)
    
    return str(temp_config_path)

def run_whimperizer(config_path: str, groups: List[str], run_number: int, verbose: bool = False) -> bool:
    """Run whimperizer with specified configuration"""
    logger = logging.getLogger(__name__)
    
    cmd = [
        'python', 'whimperizer.py',
        '--config', config_path
    ]
    
    if groups:
        cmd.extend(['--groups'] + groups)
    
    if verbose:
        cmd.append('--verbose')
    
    logger.info(f"🔄 Running whimperizer (Run {run_number})")
    logger.debug(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=not verbose, 
            text=True, 
            check=True
        )
        if verbose and result.stdout:
            print(result.stdout)
        logger.info(f"✅ Run {run_number} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Run {run_number} failed:")
        logger.error(f"Exit code: {e.returncode}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        if e.stdout:
            logger.error(f"Output: {e.stdout}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Runner for Whimperizer - Run whimperizer multiple times with different models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run whimperizer 3 times with different models
  python multi_runner.py --runs 3 --groups zaltz-1a
  
  # Run with custom config
  python multi_runner.py --runs 2 --config ../config/config.yaml --groups zaltz-1a zaltz-1b
  
  # Verbose output
  python multi_runner.py --runs 3 --groups zaltz-1a --verbose
        """
    )
    
    parser.add_argument('--runs', '-r', type=int, required=True,
                        help='Number of times to run whimperizer')
    parser.add_argument('--groups', nargs='+', metavar='GROUP',
                        help='Process specific groups (e.g., zaltz-1a zaltz-1b)')
    parser.add_argument('--config', type=str, default='../config/config.yaml',
                        help='Configuration file (default: ../config/config.yaml)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    logger = setup_logging(args.verbose)
    
    # Validate inputs
    if args.runs < 1:
        logger.error("Number of runs must be at least 1")
        sys.exit(1)
    
    if args.runs > 10:
        logger.warning("Running more than 10 times may be excessive")
    
    # Load base configuration
    try:
        base_config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create temporary directory for run-specific configs
    temp_dir = Path('./temp_configs')
    temp_dir.mkdir(exist_ok=True)
    
    logger.info(f"🚀 Starting multi-run with {args.runs} runs")
    if args.groups:
        logger.info(f"Processing groups: {', '.join(args.groups)}")
    
    success_count = 0
    
    try:
        for run_num in range(1, args.runs + 1):
            logger.info(f"\n📋 Preparing Run {run_num}/{args.runs}")
            
            # Get model config for this run
            run_model_config = get_run_model_config(base_config, run_num)
            
            if run_model_config:
                logger.info(f"Using model: {run_model_config['provider']}/{run_model_config['model']}")
                # Create temporary config with run-specific model
                config_path = create_temp_config(base_config, run_model_config, run_num, temp_dir)
            else:
                logger.info(f"Using default model (no run_{run_num}_model configured)")
                config_path = args.config
            
            if args.dry_run:
                logger.info(f"[DRY RUN] Would run whimperizer with config: {config_path}")
                continue
            
            # Run whimperizer
            success = run_whimperizer(config_path, args.groups, run_num, args.verbose)
            
            if success:
                success_count += 1
            else:
                logger.error(f"Run {run_num} failed - continuing with remaining runs")
    
    finally:
        # Clean up temporary config files
        if temp_dir.exists():
            for temp_file in temp_dir.glob("config_run_*.yaml"):
                temp_file.unlink()
            temp_dir.rmdir()
    
    # Summary
    logger.info(f"\n📊 Multi-run Summary:")
    logger.info(f"Total runs: {args.runs}")
    logger.info(f"Successful runs: {success_count}")
    logger.info(f"Failed runs: {args.runs - success_count}")
    
    if success_count == args.runs:
        logger.info("🎉 All runs completed successfully!")
        return 0
    elif success_count > 0:
        logger.warning("⚠️  Some runs failed")
        return 1
    else:
        logger.error("❌ All runs failed")
        return 2

if __name__ == '__main__':
    sys.exit(main())