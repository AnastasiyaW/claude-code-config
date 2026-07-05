# OpenScience ML Domain Evaluation

Source checked: https://github.com/synthetic-sciences/openscience
Local commit: `531467c`
Date: 2026-07-06

## Decision

Adopt a compact local router skill, not the full OpenScience skill collection.

Reason: the repository has useful ML research material, but importing 250+ skills
would add routing noise and context bloat. The useful part for our work is the
operational loop: dataset quality, benchmark rigor, experiment tracking, model
explainability, and inference deployment choices.

## Accepted Into Our Workflow

- `ml-training/training-data-pipeline`: data provenance, JSONL format, quality
  validation, deduplication, and split discipline.
- `ml-training/ml-benchmark-evaluation`: train/val/test discipline, baseline
  verification, leakage checks, metric formula checks, and multi-seed reporting.
- `other/hugging-face-trackio`: metrics must be retrievable by CLI/JSON, not only
  visible in a UI.
- `coding/shap`: SHAP/explainability as a model-debugging and leakage/bias tool.
- `coding/scikit-learn`: pipeline-first classical baselines for tabular/classifier
  tasks.
- `ml-inference/vllm` and `ml-inference/gguf`: vLLM for GPU throughput; GGUF or
  llama.cpp for local, Apple, CPU, and compact inference.
- `ml-training/unsloth`: conditional option for single-GPU LoRA/QLoRA, not a
  default for all training.

## Rejected Or Deferred

- Full OpenScience runtime: not adopted yet. Its README states the agent is not
  sandboxed; run it in a VM/container if evaluating the workbench itself.
- Bio/chem/physics specialist skills: not adopted for default workflow because
  they do not map to the current retouch, datasets, classifier, and GPU-training
  domains.
- Large fine-tuning framework skills wholesale: deferred. Existing local skills
  already cover Hugging Face, diffusion, RunPod, and training workflows; broad
  duplication would reduce routing quality.

## Verification

- Added deterministic inventory script: `scripts/openscience_skill_inventory.py`.
- Added unit test: `scripts/test_openscience_skill_inventory.py`.
- Added compact skill: `skills/ai-ml/ml-research-lab/SKILL.md`.
- Verified on the real OpenScience checkout: 292 skills inventoried.

