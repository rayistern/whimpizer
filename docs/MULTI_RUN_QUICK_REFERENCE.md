# Multi-Run Quick Reference

## What's New

4 new capabilities added to whimperizer:

| Tool | What It Does | When To Use |
|------|-------------|-------------|
| `pipeline.py --runs N` | Original pipeline + auto-consolidation when N>1 | Quick multi-run with familiar interface |
| `multi_pipeline.py` | Same as above + `--consolidate-only` & `--skip-consolidate` | When you need those 2 extra options |
| `multi_runner.py` | Runs `whimperizer.py` N times with different models | Standalone multi-run (no consolidation/PDFs) |
| `consolidator.py` | AI combines multiple whimperized files | Standalone consolidation of existing files |

## Basic Usage

```bash
# Multi-run with auto-consolidation (easiest)
python pipeline.py --runs 3 --groups zaltz-1a

# Multi-run standalone (no consolidation)
python multi_runner.py --runs 3 --groups zaltz-1a

# Consolidate all files for a group (EASIEST!)
python consolidator.py --groups zaltz-1a

# Multiple groups at once
python consolidator.py --groups zaltz-1a zaltz-1b zaltz-2a

# All groups automatically
python consolidator.py --whimper-dir ../output/whimperized_content

# Consolidate specific files (FULL PATHS REQUIRED)
python consolidator.py --files \
  "../output/whimperized_content/zaltz-1a-iterative-20250729_120000.md" \
  "../output/whimperized_content/zaltz-1a-iterative-20250729_130000.md"

# Test consolidation first (recommended!)
python consolidator.py --groups zaltz-1a --dry-run --verbose
```

## Pipeline Differences

**`pipeline.py --runs 3`**:
- Download → Multi-run → Auto-consolidate → PDF
- Can't skip consolidation

**`multi_pipeline.py --runs 3`**:
- Download → Multi-run → Auto-consolidate → PDF
- Can skip consolidation (`--skip-consolidate`)
- Can do consolidation-only (`--consolidate-only`)

## Model Configuration

Add to `config/config.yaml`:

```yaml
multi_run:
  run_models:
    run_2_model:
      provider: "openai"
      model: "gpt-4o-mini"
      temperature: 0.8
    run_3_model:
      provider: "anthropic"
      model: "claude-3-sonnet-20240229"
  consolidation:
    provider: "openai"
    model: "gpt-4.1-mini"
```

**Model Selection Logic:**
- Run 1: Default model
- Run 2: `run_2_model` if configured, else default  
- Run 3: `run_3_model` if configured, else default
- etc.

## File Priority for PDFs

PDF generation picks the best available file:
1. **🥇 consolidated** files (from consolidator) - *AI-combined best parts*
2. **🥈 iterative** files (from multi-run) - *Multiple model outputs*  
3. **🥉 normal** files (from single run) - *Single model output*

**Within each type:** Newest timestamp wins (e.g., `20250729_153000` beats `20250729_120000`)

## Common Workflows

```bash
# Quick test (2 runs)
python pipeline.py --runs 2 --groups zaltz-1a

# Full multi-run
python pipeline.py --runs 4 --groups zaltz-1a --verbose

# Experiment with consolidation only
python consolidator.py --files run1.md run2.md run3.md

# Multi-run but keep individual outputs
python multi_pipeline.py --runs 3 --skip-consolidate --groups zaltz-1a

# Consolidate existing files from different times
python consolidator.py --files \
    zaltz-1a-whimperized-iterative-20250724_120000.md \
    zaltz-1a-whimperized-iterative-20250724_130000.md \
    zaltz-1a-whimperized-iterative-20250724_140000.md
```

## Groups Flag - The Easy Way! 

**The `--groups` flag automatically finds ALL files for a group:**

```bash
# Single group (finds ALL zaltz-1a files automatically)
python consolidator.py --groups zaltz-1a --verbose
# Found: normal, iterative, consolidated - everything!

# Multiple groups at once
python consolidator.py --groups zaltz-1a zaltz-1b zaltz-2a

# See what it would do first
python consolidator.py --groups zaltz-1a --dry-run
# Shows: "📁 zaltz-1a: 5 files" - auto-discovered!
```

**Why use `--groups` instead of `--files`?**
- ✅ **No file paths needed** - automatically finds everything
- ✅ **Gets all versions** - normal, iterative, consolidated  
- ✅ **Multiple groups** - process several at once
- ✅ **Less typing** - `--groups zaltz-1a` vs long file paths

## Advanced Workflows

```bash
# Consolidate files from different sessions (manual method)
python consolidator.py --files \
    ../output/whimperized_content/zaltz-1a-iterative-gpt-4-20250729_120000.md \
    ../output/whimperized_content/zaltz-1a-iterative-claude-20250729_130000.md \
    ../output/whimperized_content/zaltz-1a-normal-20250729_140000.md

# Multi-run with custom output directory
python consolidator.py --groups zaltz-1a --output-dir ../output/custom_consolidated

# Process all groups in directory automatically
python consolidator.py --whimper-dir ../output/whimperized_content

# Multi-run with only specific AI provider
python pipeline.py --runs 3 --provider openai --groups zaltz-1a
```

## File Naming Patterns

**Understanding file types:**
- `zaltz-1a-whimperized-normal-20250729_123456.md` (single run)
- `zaltz-1a-whimperized-iterative-gpt-4-1-20250729_123456.md` (multi-run with model)
- `zaltz-1a-whimperized-consolidated-20250729_123456.md` (AI-consolidated best)

**Pipeline automatically picks:** consolidated > iterative > normal, newest timestamp

## When Things Fail

- **Multi-runner fails**: Continues with successful runs
- **Consolidation fails**: Makes PDFs from individual runs instead
- **Want to debug**: Run each tool separately with `--verbose`
- **Files not found**: Use full paths with `--files`, check `../output/whimperized_content/`
- **Git merge issues**: All single-run workflows still work the same