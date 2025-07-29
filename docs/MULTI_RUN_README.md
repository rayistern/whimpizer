# Multi-Run Whimperizer System

Generate multiple AI outputs and consolidate them into one final product.

## 📋 Simple Summary

**What's New:**
- `pipeline.py` now has `--runs N` flag (auto-consolidates when N > 1)
- `multi_pipeline.py` same as above + 2 extra flags (`--consolidate-only`, `--skip-consolidate`)
- `multi_runner.py` runs `whimperizer.py` N times with different models
- `consolidator.py` takes multiple whimperized files and AI-combines them

**What You Actually Get:**
- Run whimperizer multiple times with different models
- AI picks best parts from all runs and combines them
- Each tool can run independently

## 🎯 What Each Step Does

1. **Multi-Run**: Calls `whimperizer.py` multiple times with different models
2. **Consolidation**: AI reads all outputs and combines the best parts
3. **PDF**: Makes PDF from consolidated result (or individual runs if consolidation fails)

## 🚀 Quick Start

### Basic Multi-Run Pipeline
```bash
# Run whimperizer 3 times, consolidate, and generate PDF
cd src
python multi_pipeline.py --runs 3 --groups zaltz-1a
```

### Using Original Pipeline with Multi-Run
```bash
# Original pipeline now supports --runs flag (auto-consolidates)
cd src
python pipeline.py --runs 3 --groups zaltz-1a
```

### Independent Consolidation
```bash
# Only run consolidation on existing whimperized files
cd src
python consolidator.py --groups zaltz-1a
```

## 📋 Pipeline Flow

```
Download Files (once)
    ↓
Run Whimperizer (n times) → Multiple outputs
    ↓
Consolidate (once) → Best combined output
    ↓
Generate PDF (once)
```

## ⚙️ Configuration

Add to your `config/config.yaml`:

```yaml
# Multi-run configuration
multi_run:
  # Models for different runs
  run_models:
    run_2_model:
      provider: "openai"
      model: "gpt-4o-mini"
      temperature: 0.8
    run_3_model:
      provider: "anthropic"
      model: "claude-3-sonnet-20240229"
      temperature: 0.7
    run_4_model:
      provider: "openai"
      model: "gpt-4.1-mini"
      temperature: 0.6
  
  # Consolidation settings
  consolidation:
    provider: "openai"
    model: "gpt-4.1-mini"
    temperature: 0.7
    max_tokens: 8000
```

## 🛠️ What Each Tool Actually Does

### 1. `multi_pipeline.py` - Pipeline with 2 Extra Options
Same as `pipeline.py` but adds `--consolidate-only` and `--skip-consolidate` flags.

```bash
# Same as pipeline.py:
python multi_pipeline.py --runs 3 --groups zaltz-1a

# Only these are unique:
python multi_pipeline.py --consolidate-only --groups zaltz-1a     # Skip everything, only consolidate
python multi_pipeline.py --runs 3 --skip-consolidate --groups zaltz-1a  # Multi-run but no consolidation
```

### 2. `multi_runner.py` - Calls Whimperizer Multiple Times
Literally just runs `python whimperizer.py` N times with different model configs.

```bash
# Runs whimperizer.py 3 times (possibly with different models)
python multi_runner.py --runs 3 --groups zaltz-1a
```

### 3. `consolidator.py` - AI Combination Tool
Takes multiple whimperized files and asks AI to combine the best parts.

```bash
# Different ways to specify input files:
python consolidator.py --groups zaltz-1a                          # Auto-find files for group
python consolidator.py --files \
  "../output/whimperized_content/zaltz-1a-iterative-20250729_120000.md" \
  "../output/whimperized_content/zaltz-1a-iterative-20250729_130000.md"  # Specific files (full paths!)
python consolidator.py --whimper-dir ../output/whimperized_content # All groups in directory

# Test first with dry-run
python consolidator.py --groups zaltz-1a --dry-run --verbose
```

### 4. `pipeline.py` - Original Pipeline + Multi-Run
Original pipeline that now auto-consolidates when `--runs > 1`.

```bash
# Single run (same as before):
python pipeline.py --groups zaltz-1a             

# Multi-run (calls multi_runner.py + consolidator.py automatically):
python pipeline.py --runs 3 --groups zaltz-1a    
```

## 📁 File Naming Convention

The system uses a priority-based naming system:

- `zaltz-1a-whimperized-normal-20250724_123456.md` (single run)
- `zaltz-1a-whimperized-iterative-gpt-4-1-20250724_123456.md` (multi-run)
- `zaltz-1a-whimperized-consolidated-20250724_123456.md` (best combined)

**PDF Generation Priority**: consolidated > iterative > normal, newest timestamp wins

## 🎨 Consolidation Prompt

The system uses this prompt for consolidation:

> "Please take all these examples and compare them against each other; take the best, MOST whimperized pieces from them all and combine it into one GREAT final product."

Focus areas:
- Most vivid and childlike descriptions
- Best Wimpy Kid-style humor and voice
- Most engaging storytelling elements
- Clearest language for children
- Most creative and imaginative elements

## 🔧 How Model Selection Works

**Multi-Runner Model Priority:**
1. **Run 1**: Uses default model from config
2. **Run 2**: Uses `run_2_model` if configured, otherwise default
3. **Run 3**: Uses `run_3_model` if configured, otherwise default
4. **Run N**: Uses `run_N_model` if configured, otherwise default

**Each run can have different:**
- Provider (OpenAI, Anthropic, Google)
- Model (gpt-4, claude-3, etc.)
- Temperature (for output variety)

### Running Tools Independently
```bash
# Just run whimperizer multiple times (no consolidation, no PDFs):
python multi_runner.py --runs 3 --groups zaltz-1a

# Just consolidate existing files (no new whimperizer runs):
python consolidator.py --groups zaltz-1a

# Multi-run but skip consolidation (keep individual outputs):
python multi_pipeline.py --runs 3 --skip-consolidate --groups zaltz-1a
```

### How Consolidator Finds Files
```bash
# Auto-find: Search directory for all files matching group names
python consolidator.py --groups zaltz-1a zaltz-1b

# Auto-find: Process all groups found in directory  
python consolidator.py --whimper-dir ../output/whimperized_content

# Manual: Specify exact files to consolidate
python consolidator.py --files file1.md file2.md file3.md

# Manual + custom output location
python consolidator.py --files file1.md file2.md --output-dir ../output/custom
```

### Dry Run Mode
```bash
# See what would happen without executing
python multi_pipeline.py --runs 3 --groups zaltz-1a --dry-run
python consolidator.py --groups zaltz-1a --dry-run
```

## 🚦 What Happens When Things Fail

**If individual whimperizer runs fail:**
- Multi-runner continues with remaining runs
- Consolidation uses whatever runs succeeded
- PDFs generated from available outputs

**If consolidation fails:**
- Pipeline continues to PDF generation
- PDFs made from individual run outputs instead of consolidated version

**For debugging:**
- Each tool can be run separately
- Use `--verbose` for detailed output
- Use `--dry-run` to see what would happen

## 🔧 Troubleshooting

**Common Issues:**
- **"Files not found"**: Use full paths with `--files` option, check `../output/whimperized_content/`
- **Unicode encoding errors**: Fixed in latest version (Windows compatibility)
- **Git merge conflicts**: All single-run workflows preserved and work the same
- **No consolidation happening**: Need at least 2 files; check files exist with same group name
- **Wrong file selected**: System picks by priority (consolidated > iterative > normal) then newest timestamp

**Performance Tips:**
- Start with `--runs 2` to test, then increase
- Use `--dry-run` to verify before running
- Different models/temperatures give more variety to consolidate
- Consolidation quality depends on input variety - more different approaches = better results

## 💡 Practical Notes

- Start with 2-3 runs to test
- Different models/temperatures give more variety to consolidate
- Check consolidated outputs - AI combination isn't always perfect
- You can re-run just consolidation on existing files anytime

## 🔗 Compatibility

- Uses existing config file (`config.yaml`)
- Works with existing groups and provider settings  
- Single-run workflows unchanged (`python pipeline.py --groups zaltz-1a` still works exactly the same)
- Multi-run is purely additive