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

# Consolidate existing files
python consolidator.py --groups zaltz-1a

# Consolidate specific files
python consolidator.py --files file1.md file2.md file3.md
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
1. **consolidated** files (from consolidator)
2. **iterative** files (from multi-run)  
3. **normal** files (from single run)

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

## When Things Fail

- **Multi-runner fails**: Continues with successful runs
- **Consolidation fails**: Makes PDFs from individual runs instead
- **Want to debug**: Run each tool separately with `--verbose`