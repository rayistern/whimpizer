#!/usr/bin/env python3
"""
Complete Whimperizer Pipeline
Orchestrates the full process: Download -> AI Transform -> PDF Generation
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from typing import List, Optional

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
    
    # Multi-run files are optional but checked when needed
    multi_run_files = [
        'multi_runner.py',
        'consolidator.py'
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing required files: {', '.join(missing)}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Complete Whimperizer Pipeline: Download -> AI Transform -> PDF Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (run from src/ directory):
  # Basic pipeline (uses selenium by default for better success rate)
  python pipeline.py --groups zaltz-1a
  
  # Multi-run pipeline (runs whimperizer multiple times and consolidates)
  python pipeline.py --runs 3 --groups zaltz-1a
  
  # Specify AI model by editing ../config/config.yaml first, then:
  python pipeline.py --provider openai --groups zaltz-1a
  
  # Full pipeline with recommended settings
  python pipeline.py --provider anthropic --groups zaltz-1a --headless --download-delay 3.0 --pdf-style notebook --verbose
  
  # If downloads are blocked, try different approaches:
  python pipeline.py --groups zaltz-1a --download-delay 5.0 --headless
  python pipeline.py --groups zaltz-1a --downloader basic --download-format csv
   
  # Use different input file
  python pipeline.py --urls ../data/urls.txt --groups zaltz-1a
   
  # Skip steps if you have existing content
  python pipeline.py --skip-download --provider anthropic --groups zaltz-1a
  python pipeline.py --skip-download --skip-whimperize --groups zaltz-1a  # PDFs only
   
  # Process multiple groups
  python pipeline.py --groups zaltz-1a zaltz-1b --provider openai
   
  # Custom directories
  python pipeline.py --groups zaltz-1a --download-dir ../content --whimper-dir ../stories --pdf-dir ../books
  
  # Available AI models (edit ../config/config.yaml first):
  # OpenAI: gpt-4o, gpt-4-turbo, o1-preview, o1-mini
  # Anthropic: claude-3-sonnet-20240229, claude-3-opus-20240229  
  # Google: gemini-pro
        """
    )
    
    # Input/Output Options
    parser.add_argument('--urls', '-u', type=str, default='../data/urls.csv',
                        help='Input URLs file (default: ../data/urls.csv)')
    parser.add_argument('--download-dir', type=str, default='../output/downloaded_content',
                        help='Downloaded content directory (default: ../output/downloaded_content)')
    parser.add_argument('--whimper-dir', type=str, default='../output/whimperized_content', 
                        help='Whimperized content directory (default: ../output/whimperized_content)')
    parser.add_argument('--pdf-dir', type=str, default='../output/pdfs',
                        help='PDF output directory (default: ../output/pdfs)')
    
    # Pipeline Control
    parser.add_argument('--skip-download', action='store_true',
                        help='Skip download step (use existing downloaded content)')
    parser.add_argument('--skip-whimperize', action='store_true',
                        help='Skip whimperize step (use existing whimperized content)')
    parser.add_argument('--skip-pdf', action='store_true',
                        help='Skip PDF generation step')
    
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
    parser.add_argument('--config', type=str, default='../config/config.yaml',
                        help='Configuration file (default: ../config/config.yaml)')
    
    # PDF Generation Options
    parser.add_argument('--pdf-style', choices=['notebook', 'blank'], default='notebook',
                        help='PDF page style (default: notebook)')
    parser.add_argument('--pdf-font', type=str,
                        help='PDF font name (auto-detects Wimpy Kid fonts)')
    parser.add_argument('--pdf-background', type=str,
                        help='PDF background template')
    parser.add_argument('--resources-dir', type=str, default='../resources',
                        help='Resources directory (default: ../resources)')
    
    # Multi-run Options
    parser.add_argument('--runs', type=int, default=1,
                        help='Number of whimperizer runs (default: 1, auto-consolidates when > 1)')
    
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
        if args.config != '../config/config.yaml':
            cmd.extend(['--config', args.config])
        subprocess.run(cmd)
        return
    
    # Create output directories
    Path(args.download_dir).mkdir(exist_ok=True)
    Path(args.whimper_dir).mkdir(exist_ok=True)
    Path(args.pdf_dir).mkdir(exist_ok=True)
    
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
        if args.runs > 1:
            print(f"\n🤖 Step 2: AI multi-run transformation ({args.runs} runs)...")
            
            # Multi-run step
            cmd = ['python', 'multi_runner.py', '--runs', str(args.runs)]
            
            if args.config != '../config/config.yaml':
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
                success = run_command(cmd, "Multi-run AI transformation", args.verbose)
                if not success:
                    print("❌ Multi-run AI transformation failed")
                    sys.exit(1)
            
            # Consolidation step
            print(f"\n🔄 Step 2b: Consolidating {args.runs} runs...")
            
            cmd = ['python', 'consolidator.py']
            
            if args.config != '../config/config.yaml':
                cmd.extend(['--config', args.config])
            
            if args.groups:
                cmd.extend(['--groups'] + args.groups)
            
            if args.verbose:
                cmd.append('--verbose')
            
            if args.dry_run:
                print(f"Would run: {' '.join(cmd)}")
            else:
                consolidation_success = run_command(cmd, "Consolidation", args.verbose)
                if not consolidation_success:
                    print("⚠️ Consolidation failed, will use individual runs for PDFs")
        else:
            print("\n🤖 Step 2: AI transformation...")
            
            cmd = ['python', 'whimperizer.py']
            
            if args.config != '../config/config.yaml':
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
    if not args.skip_pdf and success:
        print("\n📚 Step 3: Generating PDFs...")
        
        # Find whimperized files with smart selection between normal and iterative versions
        def find_best_whimperized_files(whimper_dir, target_groups=None):
            """Find the best whimperized file for each group (consolidated > iterative > normal, newest timestamp)"""
            all_files = list(Path(whimper_dir).glob('*whimperized*.md'))
            all_files.extend(list(Path(whimper_dir).glob('*whimperized*.txt')))
            
            # Group files by group key (everything before '-whimperized')
            groups = {}
            for file_path in all_files:
                # Extract group key from filename - handle both old and new formats:
                # Old: zaltz-2a-whimperized-iterative-timestamp.md
                # New: zaltz-2a-16to21-whimperized-iterative-timestamp.md
                name_parts = file_path.stem.split('-whimperized-')
                if len(name_parts) >= 2:
                    full_prefix = name_parts[0]  # e.g., "zaltz-2a" or "zaltz-2a-16to21"
                    mode_and_timestamp = name_parts[1]  # e.g., "iterative-20250724_020623"
                    
                    # Extract actual group key (first two dash-separated parts)
                    prefix_parts = full_prefix.split('-')
                    if len(prefix_parts) >= 2:
                        group_key = f"{prefix_parts[0]}-{prefix_parts[1]}"  # e.g., "zaltz-2a"
                    else:
                        group_key = full_prefix  # fallback for unexpected formats
                    
                    if target_groups and group_key not in target_groups:
                        continue
                        
                    if group_key not in groups:
                        groups[group_key] = {'consolidated': [], 'iterative': [], 'normal': []}
                    
                    if mode_and_timestamp.startswith('consolidated-'):
                        groups[group_key]['consolidated'].append(file_path)
                    elif mode_and_timestamp.startswith('iterative-'):
                        groups[group_key]['iterative'].append(file_path)
                    elif mode_and_timestamp.startswith('normal-'):
                        groups[group_key]['normal'].append(file_path)
            
            # Select best file for each group (consolidated > iterative > normal, newest timestamp)
            best_files = []
            for group_key, versions in groups.items():
                if versions['consolidated']:  # List has files
                    # Pick the newest consolidated file by timestamp
                    sorted_files = sorted(versions['consolidated'], 
                                        key=lambda f: f.stem.split('-')[-1], reverse=True)
                    chosen_file = sorted_files[0]
                    mode = 'consolidated'
                elif versions['iterative']:  # List has files
                    # Pick the newest iterative file by timestamp
                    sorted_files = sorted(versions['iterative'], 
                                        key=lambda f: f.stem.split('-')[-1], reverse=True)
                    chosen_file = sorted_files[0]
                    mode = 'iterative'
                elif versions['normal']:  # List has files
                    # Pick the newest normal file by timestamp
                    sorted_files = sorted(versions['normal'], 
                                        key=lambda f: f.stem.split('-')[-1], reverse=True)
                    chosen_file = sorted_files[0]
                    mode = 'normal'
                else:
                    continue
                
                best_files.append((chosen_file, mode))
                print(f"📄 Group {group_key}: Using {mode} version")
            
            return best_files
        
        best_files = find_best_whimperized_files(args.whimper_dir, args.groups)
        
        if not best_files:
            print(f"❌ No whimperized files found in {args.whimper_dir}")
            if args.groups:
                print(f"   For groups: {args.groups}")
            sys.exit(1)
        
        print(f"Found {len(best_files)} optimal whimperized files")
        
        # Generate PDFs
        for whimper_file, mode in best_files:
            # Create output PDF name - extract group key and timestamp from filename
            # Handle both old and new formats with line numbers
            full_prefix = whimper_file.stem.split('-whimperized-')[0]  # e.g., "zaltz-2a" or "zaltz-2a-16to21"
            prefix_parts = full_prefix.split('-')
            if len(prefix_parts) >= 2:
                base_name = f"{prefix_parts[0]}-{prefix_parts[1]}"  # e.g., "zaltz-2a"
            else:
                base_name = full_prefix  # fallback
            
            # Extract timestamp and model name from whimperized filename
            # New format: zaltz-2a-16to21-whimperized-iterative-gpt-4-1-20250724_164521.md
            # Old format: zaltz-2a-16to21-whimperized-iterative-20250724_164521.md
            filename_parts = whimper_file.stem.split('-whimperized-')
            if len(filename_parts) >= 2:
                mode_and_rest = filename_parts[1]  # e.g., "iterative-gpt-4-1-20250724_164521"
                rest_parts = mode_and_rest.split('-')
                
                # Find timestamp (looks like YYYYMMDD_HHMMSS)
                timestamp_idx = -1
                model_name = ""
                for i, part in enumerate(rest_parts):
                    if len(part) == 15 and '_' in part and part.replace('_', '').replace('-', '').isdigit():
                        timestamp_idx = i
                        timestamp = part
                        # Everything between mode and timestamp is model name
                        if i > 1:  # Skip mode part
                            model_name = '-'.join(rest_parts[1:i])
                        break
                
                if timestamp_idx > 0 and model_name:
                    pdf_name = f"{base_name}-{model_name}-{timestamp}.pdf"
                elif timestamp_idx > 0:
                    pdf_name = f"{base_name}-{timestamp}.pdf"
                else:
                    # Fallback: use current timestamp
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_name = f"{base_name}-{timestamp}.pdf"
            else:
                # Fallback: use current timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_name = f"{base_name}-{timestamp}.pdf"
            
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
                success = run_command(cmd, f"Generating PDF: {pdf_name} (from {mode} version)", args.verbose)
                if not success:
                    print(f"❌ PDF generation failed for {whimper_file.name} ({mode} version)")
                    # Continue with other files
                else:
                    print(f"✅ Generated: {pdf_path} (from {mode} version)")
    else:
        print("⏭️  Skipping PDF generation")
    
    # Summary
    print(f"\n{'🎉 Pipeline completed!' if success else '❌ Pipeline completed with errors'}")
    
    if not args.dry_run:
        print(f"\nOutput locations:")
        print(f"  📁 Downloaded content: {args.download_dir}")
        print(f"  📝 Whimperized content: {args.whimper_dir}")
        print(f"  📚 PDFs: {args.pdf_dir}")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 