# Quick Start Guide

Get up and running with Checkpoint Rotation in 5 minutes!

## Prerequisites

- ComfyUI installed and working
- At least 2 checkpoints in your `models/checkpoints/` folder
- Basic familiarity with ComfyUI workflows

## Installation

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/trunksn1/comfyui-change-checkpoint-randomly.git
```

Restart ComfyUI. You should see:
```
[ComfyUI] Checkpoint Rotation Node loaded successfully!
```

## Basic Workflow (5 Steps)

### Step 1: Add Batch Index Counter

Right-click in ComfyUI → Add Node → **utils** → **Batch Index Counter**

Settings:
- `action`: **increment**
- Leave other settings as default

### Step 2: Add Checkpoint Rotation Loader

Right-click → Add Node → **loaders** → **Checkpoint Rotation Loader**

Settings:
- `subfolder`: Leave empty `""` (uses all checkpoints)
- `change_interval`: `4` (changes every 4 images)
- `rotation_mode`: **sequential**
- `seed`: `0`

Connect:
- Batch Index Counter's `batch_index` → Checkpoint Rotation's `batch_index`

### Step 3: Add Text Prompts

Add two **CLIP Text Encode** nodes:

**Positive Prompt**:
```
beautiful landscape, sunset, highly detailed
```

**Negative Prompt**:
```
blurry, low quality
```

Connect:
- Checkpoint Rotation's `clip` → both CLIP Text Encode nodes

### Step 4: Add Sampler

Add **Empty Latent Image**:
- Width: `512`
- Height: `512`
- Batch: `1` ← **Important!**

Add **KSampler**:
- Steps: `20`
- CFG: `7.5`

Connect:
- Checkpoint Rotation's `model` → KSampler
- Positive prompt → KSampler's `positive`
- Negative prompt → KSampler's `negative`
- Empty Latent Image → KSampler

### Step 5: Decode and Save

Add **VAE Decode**:
- Connect Checkpoint Rotation's `vae` → VAE Decode
- Connect KSampler's output → VAE Decode

Add **Save Image**:
- Connect VAE Decode's output → Save Image

## Running the Workflow

### Manual Mode (Testing)

1. Queue the prompt once
2. Image generates with first checkpoint
3. Change Batch Index Counter's `set_value` to 1, action to "set"
4. Queue again
5. Repeat, incrementing batch index each time

### Loop Mode (Automated)

If you have loop nodes installed:

1. Wrap entire workflow in a Loop node
2. Set loop count to 20 (for 20 images)
3. Batch Index Counter will auto-increment
4. Queue once, generates all 20 images with rotating checkpoints

**Result**:
- Images 0-3: Checkpoint A
- Images 4-7: Checkpoint B
- Images 8-11: Checkpoint C
- Images 12-15: Checkpoint D
- Images 16-19: Checkpoint E

## Tips for Best Results

### Use Specific Subfolders

Instead of using all checkpoints:

```
subfolder: "sdxl"           # Only SDXL models
subfolder: "sd15/anime"     # Only anime SD1.5 models
subfolder: "realistic"      # Only realistic models
```

### Filter by Name

```
checkpoint_filter: "turbo"    # Only checkpoints with "turbo" in name
checkpoint_filter: "anime"    # Only anime checkpoints
```

### Random Mode for Variety

```
rotation_mode: "random"
seed: 12345
```

Same seed = same sequence (reproducible)
Different seed = different sequence (variety)

## Troubleshooting

### "No checkpoints found"

**Fix**:
```
subfolder: ""  # Leave empty to use root folder
```

Or check your checkpoint folder path in ComfyUI settings.

### Checkpoint not changing

**Fix**:
1. Verify batch_index is incrementing (check counter output)
2. Set KSampler batch_size to 1
3. Use loop or manually increment batch_index

### Import errors

**Fix**: Restart ComfyUI completely

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [examples/example_workflow.json](examples/example_workflow.json)
- Experiment with different rotation modes
- Try filtering checkpoints by name
- Combine with other custom nodes

## Example Scenarios

### Scenario 1: Style Variety

Generate portraits with different style checkpoints:
- Checkpoint A: Realistic
- Checkpoint B: Anime
- Checkpoint C: Oil painting
- Checkpoint D: Watercolor

**Setup**:
```
subfolder: "portrait-styles"
change_interval: 3
rotation_mode: sequential
```

### Scenario 2: Quality Comparison

Test same prompt across different versions:
- Checkpoint A: Model v1.0
- Checkpoint B: Model v1.5
- Checkpoint C: Model v2.0

**Setup**:
```
subfolder: "model-versions"
change_interval: 1
rotation_mode: sequential
seed: fixed
```

Use same seed in KSampler for fair comparison!

### Scenario 3: Random Exploration

Discover interesting combinations:
```
subfolder: "all-models"
change_interval: 5
rotation_mode: random
seed: (random)
```

Generate hundreds of images with diverse checkpoints!

## Common Patterns

### Pattern 1: A/B Testing

Compare two checkpoints:
```
subfolder: "test"  (contains only 2 checkpoints)
change_interval: 10
rotation_mode: sequential
```

Generate 20 images: 10 with each checkpoint

### Pattern 2: Progressive Refinement

Start with fast, end with quality:
```
Checkpoints ordered: turbo → fast → standard → detailed
rotation_mode: sequential
change_interval: matches your quality goals
```

### Pattern 3: Theme Variations

Different themes for same subject:
```
Checkpoints: cyberpunk, fantasy, scifi, historical
rotation_mode: sequential or shuffle
change_interval: 5
```

## Performance Tips

1. **Cache Warming**: First run scans checkpoints (may be slow), subsequent runs use cache
2. **Subfolder Usage**: Smaller subfolders = faster scanning
3. **Batch Size**: Always use `1` for KSampler when rotating
4. **Memory**: Only one checkpoint loaded at a time (memory efficient!)

## Getting Help

- Check console for error messages
- Verify checkpoint files are valid
- Test with default ComfyUI checkpoint loader first
- Ask in ComfyUI Discord with screenshot

---

**You're ready to go!** Start with the basic workflow above, then explore advanced features in the [README](README.md).

Happy generating! 🎨
