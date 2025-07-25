# Multi-Run Whimperizer System

The multi-run system allows you to generate multiple AI outputs and consolidate them into the best possible final product.

## 🎯 What It Does

1. **Multi-Run Generation**: Runs the whimperizer multiple times with different AI models
2. **Smart Consolidation**: Uses AI to combine the best pieces from all runs into one great final product
3. **Flexible Usage**: Can run independently or as part of the full pipeline

## 🚀 Quick Start

### Basic Multi-Run Pipeline
```bash
# Run whimperizer 3 times, consolidate, and generate PDF
cd src
python multi_pipeline.py --runs 3 --groups zaltz-1a
```

### Using Original Pipeline with Multi-Run
```bash
# Original pipeline now supports --runs flag
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

## 🛠️ Available Tools

### 1. `multi_pipeline.py` - Complete Multi-Run Pipeline
Full pipeline with multi-run support and all advanced features.

```bash
# Examples
python multi_pipeline.py --runs 3 --groups zaltz-1a --verbose
python multi_pipeline.py --consolidate-only --groups zaltz-1a
python multi_pipeline.py --runs 4 --skip-download --groups zaltz-1a
```

### 2. `multi_runner.py` - Multi-Run Engine
Runs whimperizer multiple times with different models.

```bash
# Examples
python multi_runner.py --runs 3 --groups zaltz-1a
python multi_runner.py --runs 2 --config ../config/config.yaml --verbose
```

### 3. `consolidator.py` - AI Consolidation
Combines multiple outputs into one best version.

```bash
# Examples
python consolidator.py --groups zaltz-1a
python consolidator.py --whimper-dir ../output/whimperized_content --verbose
```

### 4. `pipeline.py` - Enhanced Original Pipeline
Original pipeline now supports basic multi-run via `--runs` flag.

```bash
# Examples
python pipeline.py --runs 3 --groups zaltz-1a    # Multi-run mode
python pipeline.py --groups zaltz-1a             # Single run mode
```

## 📁 File Naming Convention

The system uses a priority-based naming system:

- `zaltz-1a-whimperized-normal-20250724_123456.md` (single run)
- `zaltz-1a-whimperized-iterative-gpt-4-1-20250724_123456.md` (multi-run)
- `zaltz-1a-whimperized-consolidated-20250724_123456.md` (best combined)

**PDF Generation Priority**: consolidated > iterative > normal

## 🎨 Consolidation Prompt

The system uses this prompt for consolidation:

> "Please take all these examples and compare them against each other; take the best, MOST whimperized pieces from them all and combine it into one GREAT final product."

Focus areas:
- Most vivid and childlike descriptions
- Best Wimpy Kid-style humor and voice
- Most engaging storytelling elements
- Clearest language for children
- Most creative and imaginative elements

## 🔧 Advanced Usage

### Model Fallback System
- If `run_3_model` isn't configured but you request 3 runs, run 3 uses the default model
- Each run can use different providers (OpenAI, Anthropic, Google)
- Different temperature settings for variety

### Independent Operations
```bash
# Run only multi-runner (no consolidation or PDFs)
python multi_runner.py --runs 3 --groups zaltz-1a

# Run only consolidation (assumes existing multi-run files)
python consolidator.py --groups zaltz-1a

# Run full pipeline but skip consolidation
python multi_pipeline.py --runs 3 --skip-consolidate --groups zaltz-1a
```

### Dry Run Mode
```bash
# See what would happen without executing
python multi_pipeline.py --runs 3 --groups zaltz-1a --dry-run
python consolidator.py --groups zaltz-1a --dry-run
```

## 🚦 Error Handling

- If individual runs fail, the system continues with successful runs
- If consolidation fails, PDFs are generated from individual runs
- Each component can be run independently for debugging
- Comprehensive logging for troubleshooting

## 💡 Tips

1. **Start Small**: Try 2-3 runs first to test the system
2. **Model Diversity**: Use different providers/models for variety
3. **Temperature Variation**: Different temperatures can produce diverse outputs
4. **Review Results**: Check consolidated outputs to ensure quality
5. **Independent Testing**: Test consolidation separately on existing files

## 🔗 Integration

The multi-run system integrates seamlessly with the existing whimperizer:
- Uses same configuration file structure
- Compatible with existing group/provider settings
- Preserves all original functionality
- No changes to existing single-run workflows