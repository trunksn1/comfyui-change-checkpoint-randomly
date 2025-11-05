# Quick Summary: Per-Image Metadata Research

## TL;DR

**ImpactWildcardProcessor does NOT update metadata per-image during batch generation.**

It resolves wildcards ONCE per workflow queue, and that single value applies to all images in the batch.

## Your Code is Correct! ✅

Your `SaveImageWithCheckpoint` node is implemented perfectly and follows ComfyUI best practices.

## The Problem

Your `CheckpointRotationWithCounter` with `control_after_generate: increment` has a fundamental limitation:

```
What happens:
1. CheckpointRotationWithCounter executes ONCE → loads checkpoint_1
2. KSampler generates ALL batch images with checkpoint_1
3. Counter increments between images, but checkpoint loader doesn't re-execute
4. Result: All images use checkpoint_1 (even though counter changed)
```

## The Solution

Use **loop-based generation** instead of batch generation:

```
Loop 8 times:
  Iteration 0: Load checkpoint_1 → Generate 1 image
  Iteration 1: Load checkpoint_1 → Generate 1 image
  Iteration 2: Load checkpoint_2 → Generate 1 image
  Iteration 3: Load checkpoint_2 → Generate 1 image
  ...
```

## How to Implement

### Option 1: Use Loop Nodes (Recommended)

Install: https://github.com/Hullabalo/ComfyUI-Loop

Workflow:
```
Loop Start (iterations=8)
  ↓
CheckpointRotationWithCounter (counter from loop index)
  ↓
KSampler (batch_size=1) ← Must be 1!
  ↓
SaveImageWithCheckpoint
  ↓
Loop End
```

### Option 2: Queue Multiple Times

- Set up workflow normally
- Queue it N times for N images
- Each queue = 1 image with correct checkpoint

## Key Mechanism

The metadata mechanism you're using is **correct**:

```python
for image in images:
    metadata = PngInfo()
    # Add workflow metadata (same for all)
    metadata.add_text("prompt", json.dumps(prompt))
    # Add custom metadata (your part - perfect!)
    metadata.add_text("checkpoint", checkpoint_name)
    save_image(image, metadata)
```

The limitation is that `checkpoint_name` is provided once per node execution, not per image.

**Solution**: Multiple executions (loops) = different checkpoint_name each time.

## What to Do Next

1. **Update README** - Warn users about batch limitation, recommend loops
2. **Test with loops** - Verify it works with ComfyUI-Loop extension
3. **Optional**: Create a combined `CheckpointRotationWithLoop` node

## Files Created

1. **METADATA_RESEARCH.md** - Full technical analysis (17 sections, all details)
2. **FINDINGS_AND_RECOMMENDATIONS.md** - Detailed findings with step-by-step guide
3. **QUICK_SUMMARY.md** - This file (quick reference)

Read **FINDINGS_AND_RECOMMENDATIONS.md** for complete implementation guide.
