#!/usr/bin/env python3
"""
Multi-Run Pipeline for Whimperizer
Complete pipeline: Download → Multi-Run AI Transform → Consolidate → PDF Generation
"""

import os
import sys
import argparse
import subprocess
import logging
import time
from pathlib import Path
from typing import List, Optional

def setup_logging(verbose: bool = False):
    """Setup logging for multi-pipeline"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def run_command(cmd: List[str], description: str, verbose: bool = False) -> bool:
    """Run a command and handle errors"""
    logger = logging.getLogger(__name__)
    
    if verbose:
        logger.info(f"\n🔄 {description}")
        logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=not verbose, text=True, check=True)
        if verbose and result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error in {description}:")
        logger.error(f"Command: {' '.join(cmd)}")
        logger.error(f"Exit code: {e.returncode}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        if e.stdout:
            logger.error(f"Output: {e.stdout}")
        return False

def check_dependencies():
    """Check if required Python files exist"""
    required_files = [
        'bulk_downloader.py',
        'multi_runner.py',
        'consolidator.py',
        'wimpy_pdf_generator.py'
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        logging.getLogger(__name__).error(f"❌ Missing required files: {', '.join(missing)}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Run Pipeline for Whimperizer: Download → Multi-Run AI Transform → Consolidate → PDF Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (run from src/ directory):
  # Basic multi-run pipeline with 3 runs
  python multi_pipeline.py --runs 3 --groups zaltz-1a
  
  # Multi-run with specific provider for first run
  python multi_pipeline.py --runs 3 --provider openai --groups zaltz-1a --verbose
  
  # Skip download, run 2 times, consolidate, and generate PDFs
  python multi_pipeline.py --skip-download --runs 2 --groups zaltz-1a
  
  # Run consolidation only (independent mode)
  python multi_pipeline.py --consolidate-only --groups zaltz-1a
  
  # Full pipeline with custom settings
  python multi_pipeline.py --runs 4 --groups zaltz-1a --download-delay 3.0 --pdf-style notebook --verbose
        """
    )
    
    # Multi-run specific options
    parser.add_argument('--runs', '-r', type=int, default=1,
                        help='Number of times to run whimperizer (default: 1 - standard single run)')
    parser.add_argument('--consolidate-only', action='store_true',
                        help='Only run consolidation step (skip download and whimperize)')
    parser.add_argument('--skip-consolidate', action='store_true',
                        help='Skip consolidation step (useful for single runs)')
    
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
                        help='Downloader to use (default: selenium)')
    parser.add_argument('--download-format', choices=['json', 'csv', 'txt'], default='txt',
                        help='Download format - only for basic downloader (default: txt)')
    parser.add_argument('--download-delay', type=float, default=1.0,
                        help='Delay between downloads in seconds (default: 1.0)')
    parser.add_argument('--headless', action='store_true',
                        help='Run selenium in headless mode')
    
    # AI/Whimperizer Options
    parser.add_argument('--provider', choices=['openai', 'anthropic', 'google'],
                        help='AI provider for first run (default: from config)')
    parser.add_argument('--groups', nargs='+', metavar='GROUP',
                        help='Process specific groups (e.g., zaltz-1a zaltz-1b)')
    parser.add_argument('--config', type=str, default='../config/config.yaml',
                        help='Configuration file (default: ../config/config.yaml)')
    
    # PDF Generation Options
    parser.add_argument('--pdf-style', choices=['notebook', 'blank'], default='notebook',
                        help='PDF page style (default: notebook)')
    parser.add_argument('--pdf-font', type=str,
                        help='PDF font name (auto-detects Wimpy Kid fonts)')
    parser.add_argument('--resources-dir', type=str, default='../resources',
                        help='Resources directory (default: ../resources)')
    
    # General Options
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    logger = setup_logging(args.verbose)
    
    # Validate arguments
    if args.consolidate_only and args.skip_consolidate:
        logger.error("Cannot use both --consolidate-only and --skip-consolidate")
        sys.exit(1)
    
    if args.consolidate_only:
        logger.info("🎯 Running in consolidation-only mode")
    elif args.runs == 1 and not args.skip_consolidate:
        logger.info("📝 Single run mode - consolidation will be skipped automatically")
        args.skip_consolidate = True
    elif args.runs > 1:
        logger.info(f"🔄 Multi-run mode: {args.runs} runs with consolidation")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create output directories
    Path(args.download_dir).mkdir(exist_ok=True)
    Path(args.whimper_dir).mkdir(exist_ok=True)
    Path(args.pdf_dir).mkdir(exist_ok=True)
    
    success = True
    
    # Step 1: Download Content (unless consolidate-only or skip-download)
    if not args.consolidate_only and not args.skip_download:
        logger.info("📥 Step 1: Downloading content...")
        
        downloader = 'bulk_downloader.py' if args.downloader == 'basic' else 'selenium_downloader.py'
        cmd = [
            'python', downloader,
            '--input', args.urls,
            '--output-dir', args.download_dir,
            '--delay', str(args.download_delay)
        ]
        
        if args.downloader == 'basic':
            cmd.extend(['--format', args.download_format])
        
        if args.downloader == 'selenium' and args.headless:
            cmd.append('--headless')
        
        if args.dry_run:
            logger.info(f"Would run: {' '.join(cmd)}")
        else:
            success = run_command(cmd, "Downloading content", args.verbose)
            if not success:
                logger.error("❌ Download failed")
                sys.exit(1)
    elif not args.consolidate_only:
        logger.info("⏭️  Skipping download (using existing content)")
    
    # Step 2: Multi-Run AI Transformation (unless consolidate-only or skip-whimperize)
    if not args.consolidate_only and not args.skip_whimperize and success:
        if args.runs > 1:
            logger.info(f"\n🤖 Step 2: Multi-run AI transformation ({args.runs} runs)...")
            
            cmd = [
                'python', 'multi_runner.py',
                '--runs', str(args.runs),
                '--config', args.config
            ]
            
            if args.groups:
                cmd.extend(['--groups'] + args.groups)
            
            if args.verbose:
                cmd.append('--verbose')
            
            if args.dry_run:
                cmd.append('--dry-run')
            
            if args.dry_run:
                logger.info(f"Would run: {' '.join(cmd)}")
            else:
                success = run_command(cmd, f"Multi-run AI transformation ({args.runs} runs)", args.verbose)
                if not success:
                    logger.error("❌ Multi-run AI transformation failed")
                    sys.exit(1)
        else:
            # Single run - use original whimperizer
            logger.info("\n🤖 Step 2: AI transformation (single run)...")
            
            cmd = ['python', 'whimperizer.py', '--config', args.config]
            
            if args.provider:
                cmd.extend(['--provider', args.provider])
            
            if args.groups:
                cmd.extend(['--groups'] + args.groups)
            
            if args.verbose:
                cmd.append('--verbose')
            
            if args.dry_run:
                logger.info(f"Would run: {' '.join(cmd)}")
            else:
                success = run_command(cmd, "AI transformation", args.verbose)
                if not success:
                    logger.error("❌ AI transformation failed")
                    sys.exit(1)
    elif not args.consolidate_only:
        logger.info("⏭️  Skipping whimperize (using existing content)")
    
    # Step 3: Consolidation (if multi-run and not skipped)
    if not args.skip_consolidate and (args.consolidate_only or args.runs > 1) and success:
        logger.info("\n🔗 Step 3: Consolidating multiple outputs...")
        
        cmd = [
            'python', 'consolidator.py',
            '--whimper-dir', args.whimper_dir,
            '--output-dir', args.whimper_dir,
            '--config', args.config
        ]
        
        if args.groups:
            cmd.extend(['--groups'] + args.groups)
        
        if args.verbose:
            cmd.append('--verbose')
        
        if args.dry_run:
            cmd.append('--dry-run')
        
        if args.dry_run:
            logger.info(f"Would run: {' '.join(cmd)}")
        else:
            success = run_command(cmd, "Consolidating outputs", args.verbose)
            if not success:
                logger.error("❌ Consolidation failed")
                # Continue - we might still have individual runs to make PDFs from
    elif args.runs > 1:
        logger.info("⏭️  Skipping consolidation")
    
    # Step 4: PDF Generation (unless consolidate-only or skip-pdf)
    if not args.consolidate_only and not args.skip_pdf and success:
        logger.info("\n📚 Step 4: Generating PDFs...")
        
        # Import the PDF generation logic from original pipeline
        from pathlib import Path
        
        def find_best_whimperized_files(whimper_dir, target_groups=None):
            """Find the best whimperized file for each group (consolidated > iterative > normal)"""
            all_files = list(Path(whimper_dir).glob('*whimperized*.md'))
            all_files.extend(list(Path(whimper_dir).glob('*whimperized*.txt')))
            
            # Group files by group key
            groups = {}
            for file_path in all_files:
                name_parts = file_path.stem.split('-whimperized-')
                if len(name_parts) >= 2:
                    full_prefix = name_parts[0]
                    mode_and_timestamp = name_parts[1]
                    
                    prefix_parts = full_prefix.split('-')
                    if len(prefix_parts) >= 2:
                        group_key = f"{prefix_parts[0]}-{prefix_parts[1]}"
                    else:
                        group_key = full_prefix
                    
                    if target_groups and group_key not in target_groups:
                        continue
                        
                    if group_key not in groups:
                        groups[group_key] = {}
                    
                    if mode_and_timestamp.startswith('consolidated-'):
                        groups[group_key]['consolidated'] = file_path
                    elif mode_and_timestamp.startswith('iterative-'):
                        groups[group_key]['iterative'] = file_path
                    elif mode_and_timestamp.startswith('normal-'):
                        groups[group_key]['normal'] = file_path
            
            # Select best file for each group (consolidated > iterative > normal)
            best_files = []
            for group_key, versions in groups.items():
                if 'consolidated' in versions:
                    chosen_file = versions['consolidated']
                    mode = 'consolidated'
                elif 'iterative' in versions:
                    chosen_file = versions['iterative']
                    mode = 'iterative'
                elif 'normal' in versions:
                    chosen_file = versions['normal']
                    mode = 'normal'
                else:
                    continue
                
                best_files.append((chosen_file, mode))
                logger.info(f"📄 Group {group_key}: Using {mode} version")
            
            return best_files
        
        best_files = find_best_whimperized_files(args.whimper_dir, args.groups)
        
        if not best_files:
            logger.error(f"❌ No whimperized files found in {args.whimper_dir}")
            if args.groups:
                logger.error(f"   For groups: {args.groups}")
            sys.exit(1)
        
        logger.info(f"Found {len(best_files)} whimperized files to convert")
        
        # Generate PDFs
        for whimper_file, mode in best_files:
            # Create output PDF name
            full_prefix = whimper_file.stem.split('-whimperized-')[0]
            prefix_parts = full_prefix.split('-')
            if len(prefix_parts) >= 2:
                base_name = f"{prefix_parts[0]}-{prefix_parts[1]}"
            else:
                base_name = full_prefix
            
            # Extract timestamp and model name
            filename_parts = whimper_file.stem.split('-whimperized-')
            if len(filename_parts) >= 2:
                mode_and_rest = filename_parts[1]
                rest_parts = mode_and_rest.split('-')
                
                # Find timestamp
                timestamp_idx = -1
                model_name = ""
                for i, part in enumerate(rest_parts):
                    if len(part) == 15 and '_' in part and part.replace('_', '').replace('-', '').isdigit():
                        timestamp_idx = i
                        timestamp = part
                        if i > 1:
                            model_name = '-'.join(rest_parts[1:i])
                        break
                
                if timestamp_idx > 0 and model_name:
                    pdf_name = f"{base_name}-{model_name}-{timestamp}.pdf"
                elif timestamp_idx > 0:
                    pdf_name = f"{base_name}-{mode}-{timestamp}.pdf"
                else:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_name = f"{base_name}-{mode}-{timestamp}.pdf"
            else:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_name = f"{base_name}-{mode}-{timestamp}.pdf"
            
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
            
            if args.dry_run:
                logger.info(f"Would run: {' '.join(cmd)}")
            else:
                pdf_success = run_command(cmd, f"Generating PDF: {pdf_name} (from {mode} version)", args.verbose)
                if pdf_success:
                    logger.info(f"✅ Generated: {pdf_path} (from {mode} version)")
                else:
                    logger.error(f"❌ PDF generation failed for {whimper_file.name} ({mode} version)")
    elif not args.consolidate_only:
        logger.info("⏭️  Skipping PDF generation")
    
    # Summary
    if args.consolidate_only:
        logger.info(f"\n{'🎉 Consolidation completed!' if success else '❌ Consolidation completed with errors'}")
    else:
        logger.info(f"\n{'🎉 Multi-run pipeline completed!' if success else '❌ Multi-run pipeline completed with errors'}")
    
    if not args.dry_run and not args.consolidate_only:
        logger.info(f"\nOutput locations:")
        logger.info(f"  📁 Downloaded content: {args.download_dir}")
        logger.info(f"  📝 Whimperized content: {args.whimper_dir}")
        logger.info(f"  📚 PDFs: {args.pdf_dir}")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())