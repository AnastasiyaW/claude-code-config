# Project Rules

## Stack

Python {{version}} + {{framework}} + {{accelerator}}

## Commands

```bash
# Environment
uv sync  # or: pip install -r requirements.txt

# Train
{{train_command}}

# Evaluate
{{eval_command}}

# Inference
{{inference_command}}

# Test
pytest tests/ -x -v
```

## File Structure

```
src/
  models/        # Model architectures
  data/          # Datasets, dataloaders, transforms
  training/      # Training loops, losses, optimizers
  eval/          # Evaluation metrics, visualization
  utils/         # Shared utilities
configs/         # YAML/JSON experiment configs
scripts/         # One-off scripts (data prep, export)
notebooks/       # Exploration only, not production code
```

## Style Guide

```python
# Type hints on all function signatures
# Docstrings on public functions (Google style)
# Config via dataclass or pydantic, not loose dicts

# Reproducibility: seed everything
def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

# Logging: use structured logging, not print()
import logging
logger = logging.getLogger(__name__)
```

## Experiment Tracking

```python
# All experiments logged to {{tracking_tool}}
# Config saved alongside checkpoints
# Never overwrite a checkpoint - use versioned names
# wandb/mlflow run name = git hash + config hash
```

## GPU Usage

```python
# Always check GPU availability before assuming CUDA
# Use mixed precision (AMP) by default
# Monitor VRAM with torch.cuda.memory_summary()
# Gradient accumulation for large effective batch sizes
```

## Red Lines

1. Never train on test data - validate data splits before training
2. Never overwrite checkpoints without versioning
3. Never hardcode paths - use configs or environment variables
4. Never commit large files (models, datasets) - use git-lfs or external storage
5. Never run training without logging - if it's not logged, it didn't happen
6. Never change random seed mid-experiment for "better results"

## Supply Chain Defense

```toml
# ~/.config/uv/uv.toml
exclude-newer = "7 days"
```
