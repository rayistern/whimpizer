#!/usr/bin/env python3
"""
Complete Whimperizer Pipeline
Orchestrates the full process: Download → AI Transform → PDF Generation → Audio Generation
"""

import os
import sys
import argparse
import subprocess
import time
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any

def run_command(cmd: List[str], description: str, verbose: bool = False) -> bool:
    """Run a command and handle errors"""
    if verbose:
        print(f"\n🔄 {description}")
        print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=not verbose, text=True, check=True)
        if verbose and result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}:")
        print(f"Command: {' '.join(cmd)}")
        print(f"Exit code: {e.returncode}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        return False

def check_dependencies():
    """Check if required Python files exist"""
    required_files = [
        'bulk_downloader.py',
        'whimperizer.py', 
        'wimpy_pdf_generator.py'
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing required files: {', '.join(missing)}")

def check_audio_dependencies() -> bool:
    """Check if audio generation dependencies are available"""
    try:
        import torch
        import torchaudio
        from audio.audiobook_generator import AudiobookGenerator
        return True
    except ImportError as e:
        return False

def load_audio_config() -> Dict[str, Any]:
    """Load audio generation configuration"""
    try:
        config_path = Path('../config/audio_config.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Return default config
            return {
                'audio': {
                    'enabled': False,  # Disabled by default
                    'model': {'name': 'sesame/csm-1b', 'device': 'cpu'},
                    'output': {'formats': ['wav', 'mp3']},
                    'voices': {'narrator': 0, 'greg': 1, 'rodrick': 2, 'mom': 3, 'dad': 4}
                }
            }
    except Exception as e:
        print(f"Warning: Failed to load audio config: {e}")
        return {'audio': {'enabled': False}}

def generate_audiobooks(whimper_files: List[Path], audio_dir: str, verbose: bool = False) -> bool:
    """Generate audiobooks from whimperized content"""
    try:
        # Check if audio generation is available
        if not check_audio_dependencies():
            print("⚠️  Audio dependencies not available. Skipping audiobook generation.")
            print("   To enable audio generation, install: pip install -r config/csm_requirements.txt")
            return True  # Not a failure, just not available
        
        # Load configuration
        config = load_audio_config()
        
        if not config.get('audio', {}).get('enabled', False):
            print("⚠️  Audio generation is disabled in configuration")
            return True
        
        print(f"🎵 Generating audiobooks for {len(whimper_files)} files...")
        
        # Import audio generator
        from audio.audiobook_generator import AudiobookGenerator
        
        # Initialize generator
        generator = AudiobookGenerator(config)
        
        # Validate configuration
        validation = generator.validate_configuration()
        if not validation['valid']:
            print(f"❌ Audio configuration validation failed: {validation['errors']}")
            return False
        
        success_count = 0
        
        for whimper_file in whimper_files:
            try:
                # Read the whimperized content
                with open(whimper_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    print(f"⚠️  Empty content in {whimper_file.name}, skipping")
                    continue
                
                # Create title from filename
                title = whimper_file.stem.replace('-whimperized', '').replace('_', ' ')
                
                if verbose:
                    print(f"📖 Processing: {title}")
                    
                    # Show time estimate
                    estimate = generator.estimate_generation_time(content)
                    print(f"   Estimated audio duration: {estimate['estimated_audio_duration_minutes']:.1f} minutes")
                    print(f"   Estimated generation time: {estimate['estimated_generation_time_minutes']:.1f} minutes")
                
                # Generate audiobook
                output_paths = generator.generate_audiobook(
                    content=content,
                    title=title
                )
                
                if output_paths:
                    print(f"✅ Generated audiobook: {title}")
                    if verbose:
                        for format_name, path in output_paths.items():
                            print(f"   {format_name.upper()}: {path}")
                    success_count += 1
                else:
                    print(f"❌ Failed to generate audiobook: {title}")
                
            except Exception as e:
                print(f"❌ Error generating audiobook for {whimper_file.name}: {str(e)}")
                if verbose:
                    import traceback
                    traceback.print_exc()
                continue
        
        print(f"🎵 Audiobook generation completed: {success_count}/{len(whimper_files)} successful")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Audiobook generation failed: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False
        return False
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Complete Whimperizer Pipeline: Download → AI Transform → PDF Generation → Audio Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic pipeline (uses selenium by default for better success rate)
  python pipeline.py --urls urls.csv --groups zaltz-1a
  
  # Specify AI model by editing config.yaml first, then:
  python pipeline.py --urls urls.csv --provider openai --groups zaltz-1a
  
  # Full pipeline with recommended settings
  python pipeline.py --urls urls.csv --provider anthropic --groups zaltz-1a --headless --download-delay 3.0 --pdf-style notebook --verbose
  
  # If downloads are blocked, try different approaches:
  python pipeline.py --urls urls.csv --groups zaltz-1a --download-delay 5.0 --headless
  python pipeline.py --urls urls.csv --groups zaltz-1a --downloader basic --download-format csv
   
  # Skip steps if you have existing content
  python pipeline.py --skip-download --provider anthropic --groups zaltz-1a
  python pipeline.py --skip-download --skip-whimperize --groups zaltz-1a  # PDFs only
   
  # Process multiple groups
  python pipeline.py --urls urls.csv --groups zaltz-1a zaltz-1b --provider openai
   
  # Custom directories
  python pipeline.py --urls urls.csv --groups zaltz-1a --download-dir content --whimper-dir stories --pdf-dir books --audio-dir audiobooks
  
  # Audio generation examples (requires CSM dependencies)
  python pipeline.py --urls urls.csv --groups zaltz-1a --provider anthropic  # Full pipeline with audio
  python pipeline.py --skip-download --skip-whimperize --groups zaltz-1a --audio-only  # Audio only
  python pipeline.py --urls urls.csv --groups zaltz-1a --skip-audio  # Skip audio generation
  
  # Available AI models (edit config.yaml first):
  # OpenAI: gpt-4o, gpt-4-turbo, o1-preview, o1-mini
  # Anthropic: claude-3-sonnet-20240229, claude-3-opus-20240229  
  # Google: gemini-pro
        """
    )
    
    # Input/Output Options
    parser.add_argument('--urls', '-u', type=str, default='urls.txt',
                        help='Input URLs file (default: urls.txt)')
    parser.add_argument('--download-dir', type=str, default='downloaded_content',
                        help='Downloaded content directory (default: downloaded_content)')
    parser.add_argument('--whimper-dir', type=str, default='whimperized_content', 
                        help='Whimperized content directory (default: whimperized_content)')
    parser.add_argument('--pdf-dir', type=str, default='pdfs',
                        help='PDF output directory (default: pdfs)')
    parser.add_argument('--audio-dir', type=str, default='audiobooks',
                        help='Audiobook output directory (default: audiobooks)')
    
    # Pipeline Control
    parser.add_argument('--skip-download', action='store_true',
                        help='Skip download step (use existing downloaded content)')
    parser.add_argument('--skip-whimperize', action='store_true',
                        help='Skip whimperize step (use existing whimperized content)')
    parser.add_argument('--skip-pdf', action='store_true',
                        help='Skip PDF generation step')
    parser.add_argument('--skip-audio', action='store_true',
                        help='Skip audiobook generation step')
    parser.add_argument('--audio-only', action='store_true',
                        help='Only generate audiobooks (skip PDF generation)')
    
    # Download Options
    parser.add_argument('--downloader', choices=['basic', 'selenium'], default='selenium',
                        help='Downloader to use (default: selenium - better for bypassing blocks)')
    parser.add_argument('--download-format', choices=['json', 'csv', 'txt'], default='txt',
                        help='Download format - only applies to basic downloader (default: txt)')
    parser.add_argument('--download-delay', type=float, default=1.0,
                        help='Delay between downloads in seconds (default: 1.0, recommend 3-5 for selenium)')
    parser.add_argument('--headless', action='store_true',
                        help='Run selenium in headless mode (no visible browser window)')
    
    # AI/Whimperizer Options
    parser.add_argument('--provider', choices=['openai', 'anthropic', 'google'],
                        help='AI provider (default: from config)')
    parser.add_argument('--groups', nargs='+', metavar='GROUP',
                        help='Process specific groups (e.g., zaltz-1a zaltz-1b)')
    parser.add_argument('--list-groups', action='store_true',
                        help='List available groups and exit')
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='Configuration file (default: config.yaml)')
    
    # PDF Generation Options
    parser.add_argument('--pdf-style', choices=['notebook', 'blank'], default='notebook',
                        help='PDF page style (default: notebook)')
    parser.add_argument('--pdf-font', type=str,
                        help='PDF font name (auto-detects Wimpy Kid fonts)')
    parser.add_argument('--pdf-background', type=str,
                        help='PDF background template')
    parser.add_argument('--resources-dir', type=str, default='resources',
                        help='Resources directory (default: resources)')
    
    # General Options
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Handle list-groups
    if args.list_groups:
        cmd = ['python', 'whimperizer.py', '--list-groups']
        if args.config != 'config.yaml':
            cmd.extend(['--config', args.config])
        subprocess.run(cmd)
        return
    
    # Create output directories
    Path(args.download_dir).mkdir(exist_ok=True)
    Path(args.whimper_dir).mkdir(exist_ok=True)
    Path(args.pdf_dir).mkdir(exist_ok=True)
    Path(args.audio_dir).mkdir(exist_ok=True)
    
    success = True
    
    # Step 1: Download Content
    if not args.skip_download:
        print("📥 Step 1: Downloading content...")
        
        downloader = 'bulk_downloader.py' if args.downloader == 'basic' else 'selenium_downloader.py'
        cmd = [
            'python', downloader,
            '--input', args.urls,
            '--output-dir', args.download_dir,
            '--delay', str(args.download_delay)
        ]
        
        # Only basic downloader supports format selection
        if args.downloader == 'basic':
            cmd.extend(['--format', args.download_format])
        
        if args.downloader == 'selenium' and args.headless:
            cmd.append('--headless')
        
        if args.dry_run:
            print(f"Would run: {' '.join(cmd)}")
        else:
            success = run_command(cmd, "Downloading content", args.verbose)
            if not success:
                print("❌ Download failed")
                sys.exit(1)
    else:
        print("⏭️  Skipping download (using existing content)")
    
    # Step 2: AI Transformation
    if not args.skip_whimperize and success:
        print("\n🤖 Step 2: AI transformation...")
        
        cmd = ['python', 'whimperizer.py']
        
        if args.config != 'config.yaml':
            cmd.extend(['--config', args.config])
        
        if args.provider:
            cmd.extend(['--provider', args.provider])
        
        if args.groups:
            cmd.extend(['--groups'] + args.groups)
        
        if args.verbose:
            cmd.append('--verbose')
        
        if args.log_level:
            cmd.extend(['--log-level', args.log_level])
        
        if args.dry_run:
            print(f"Would run: {' '.join(cmd)}")
        else:
            success = run_command(cmd, "AI transformation", args.verbose)
            if not success:
                print("❌ AI transformation failed")
                sys.exit(1)
    else:
        print("⏭️  Skipping whimperize (using existing content)")
    
    # Step 3: PDF Generation
    if not args.skip_pdf and not args.audio_only and success:
        print("\n📚 Step 3: Generating PDFs...")
        
        # Find whimperized files
        whimper_files = list(Path(args.whimper_dir).glob('*whimperized*.md'))
        whimper_files.extend(list(Path(args.whimper_dir).glob('*whimperized*.txt')))
        
        if not whimper_files:
            print(f"❌ No whimperized files found in {args.whimper_dir}")
            sys.exit(1)
        
        if args.groups:
            # Filter files for specific groups
            filtered_files = []
            for group in args.groups:
                group_files = [f for f in whimper_files if group in f.name]
                filtered_files.extend(group_files)
            whimper_files = filtered_files
        
        if not whimper_files:
            print(f"❌ No whimperized files found for groups: {args.groups}")
            sys.exit(1)
        
        print(f"Found {len(whimper_files)} whimperized files")
        
        # Generate PDFs
        for whimper_file in whimper_files:
            # Create output PDF name
            pdf_name = whimper_file.stem.replace('-whimperized', '') + '.pdf'
            pdf_path = Path(args.pdf_dir) / pdf_name
            
            cmd = [
                'python', 'wimpy_pdf_generator.py',
                '--input', str(whimper_file),
                '--output', str(pdf_path),
                '--style', args.pdf_style,
                '--resources', args.resources_dir
            ]
            
            if args.pdf_font:
                cmd.extend(['--font', args.pdf_font])
            
            if args.pdf_background:
                cmd.extend(['--background', args.pdf_background])
            
            # Note: PDF generation doesn't support --verbose flag
            # if args.verbose:
            #     cmd.append('--verbose')
            
            if args.dry_run:
                print(f"Would run: {' '.join(cmd)}")
            else:
                success = run_command(cmd, f"Generating PDF: {pdf_name}", args.verbose)
                if not success:
                    print(f"❌ PDF generation failed for {whimper_file}")
                    # Continue with other files
                else:
                    print(f"✅ Generated: {pdf_path}")
    else:
        print("⏭️  Skipping PDF generation")
    
    # Step 4: Audio Generation
    if not args.skip_audio and success:
        print("\n🎵 Step 4: Generating Audiobooks...")
        
        # Find whimperized files
        whimper_files = list(Path(args.whimper_dir).glob('*whimperized*.md'))
        whimper_files.extend(list(Path(args.whimper_dir).glob('*whimperized*.txt')))
        
        if not whimper_files:
            print(f"❌ No whimperized files found in {args.whimper_dir}")
            if args.audio_only:
                sys.exit(1)
        else:
            if args.groups:
                # Filter files for specific groups
                filtered_files = []
                for group in args.groups:
                    group_files = [f for f in whimper_files if group in f.name]
                    filtered_files.extend(group_files)
                whimper_files = filtered_files
            
            if not whimper_files:
                print(f"❌ No whimperized files found for groups: {args.groups}")
                if args.audio_only:
                    sys.exit(1)
            else:
                print(f"Found {len(whimper_files)} whimperized files for audio generation")
                
                if args.dry_run:
                    print("Would generate audiobooks for:")
                    for whimper_file in whimper_files:
                        title = whimper_file.stem.replace('-whimperized', '').replace('_', ' ')
                        print(f"  - {title}")
                else:
                    audio_success = generate_audiobooks(whimper_files, args.audio_dir, args.verbose)
                    if not audio_success:
                        print("⚠️  Some audiobooks failed to generate, but continuing...")
    else:
        print("⏭️  Skipping audiobook generation")
    
    # Summary
    print(f"\n{'🎉 Pipeline completed!' if success else '❌ Pipeline completed with errors'}")
    
    if not args.dry_run:
        print(f"\nOutput locations:")
        print(f"  📁 Downloaded content: {args.download_dir}")
        print(f"  📝 Whimperized content: {args.whimper_dir}")
        if not args.audio_only:
            print(f"  📚 PDFs: {args.pdf_dir}")
        if not args.skip_audio:
            print(f"  🎵 Audiobooks: {args.audio_dir}")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 