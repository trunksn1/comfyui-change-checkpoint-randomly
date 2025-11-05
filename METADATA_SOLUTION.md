# Solution: Getting Checkpoint Info in Image Metadata

## The Problem You Discovered

✅ **Checkpoints ARE rotating** (you see different console messages, different styles)
✅ **Node IS working correctly**
❌ **BUT image metadata shows the same info for all images**

This happens because ComfyUI captures workflow metadata at the **start** of the batch, not per-image.

## The Solution: Custom Save Node

I created a **"Save Image (with Checkpoint Info)"** node that embeds the checkpoint name directly into each image's PNG metadata as it's saved.

## Setup (3 Steps)

### Step 1: Update the Node

```bash
cd C:\StableDiffusion\ComfyUI\custom_nodes\comfyui-change-checkpoint-randomly
git pull
```

Restart ComfyUI.

### Step 2: Replace SaveImage Node

**Old workflow:**
```
[Checkpoint Rotation (Batch)]
  └─→ model/clip/vae → ... → [SaveImage]
```

**New workflow:**
```
[Checkpoint Rotation (Batch)]
  ├─→ model/clip/vae → ... → [VAE Decode]
  │                              └─→ images
  └─→ checkpoint_name ───────────────┘
                                      │
                        [Save Image (with Checkpoint Info)]
                          ├─ images: (from VAE Decode)
                          ├─ checkpoint_name: (from Checkpoint Rotation)
                          └─ filename_prefix: "my_images"
```

### Step 3: Connect Checkpoint Name

1. Find the **checkpoint_name** output on your Checkpoint Rotation node
2. Connect it to the **checkpoint_name** input on Save Image (with Checkpoint Info)
3. Done!

## What You Get

### In PNG Metadata

Each image now has these fields embedded:

```
checkpoint: Illustrious\JANKUV5NSFWTrainedNoobai_v40.safetensors
model: Illustrious\JANKUV5NSFWTrainedNoobai_v40.safetensors
checkpoint_info: Image #4 (raw counter: 143)
                 Checkpoint 2/34
                 File: JANKUV5NSFWTrainedNoobai_v40.safetensors
                 Image 1/4 with this checkpoint
                 Next change at image #8
```

### How to View It

**Windows:**
- Right-click image → Properties → Details tab
- Look for "checkpoint" and "model" fields

**ExifTool:**
```bash
exiftool image.png | grep -i checkpoint
```

**Python:**
```python
from PIL import Image
img = Image.open("image.png")
print(img.info.get("checkpoint"))
```

## Bonus: Checkpoint in Filename

Want the checkpoint name in the filename too?

### Use the Checkpoint to Filename Node

```
[Checkpoint Rotation (Batch)]
  └─→ checkpoint_name
         │
    [Checkpoint to Filename]
      ├─ checkpoint_name: (from rotation)
      ├─ prefix: "batch"
      └─ include_path: False
         │
         └─→ filename_prefix
                │
         [Save Image (with Checkpoint Info)]
           ├─ filename_prefix: (from Checkpoint to Filename)
           └─ ...
```

### Result

Files named like:
```
batch_JANKUV5NSFWTrainedNoobai_v40_00001.png
batch_JANKUV5NSFWTrainedNoobai_v40_00002.png
batch_JANKUV5NSFWTrainedNoobai_v40_00003.png
batch_JANKUV5NSFWTrainedNoobai_v40_00004.png
batch_bismuthIllustrious_v60_00005.png  ← Checkpoint changed!
batch_bismuthIllustrious_v60_00006.png
```

You can instantly see which checkpoint was used just from the filename!

## Complete Workflow

Here's the full setup:

```
[Primitive INT]
  control_after_generate: increment
    └─→ counter

[Checkpoint Rotation (Batch)]
  ├─ counter: (from Primitive)
  ├─ subfolder: "Illustrious"
  ├─ change_every: 4
  └─ reset_on_next: False
    ├─→ model ──→ [KSampler] batch_size: 20
    ├─→ clip ───→ [CLIP Text Encode]
    ├─→ vae ────→ [VAE Decode]
    ├─→ checkpoint_name ──┐
    └─→ info ─────────────┤
                          │
              [Save Image (with Checkpoint Info)]
                ├─ images: (from VAE Decode)
                ├─ checkpoint_name: (from Checkpoint Rotation)
                ├─ checkpoint_info: (from Checkpoint Rotation 'info' output)
                └─ filename_prefix: "my_batch"
```

## Why This Works

**Standard SaveImage:**
- Reads workflow data once at batch start
- All images get same metadata

**Save Image (with Checkpoint Info):**
- Executes once per image (because checkpoint_name input changes)
- Embeds current checkpoint into EACH image's PNG metadata
- Each image gets correct, unique metadata ✅

## Verifying It Works

1. Generate a batch of 20 images
2. Look at the filenames - should see checkpoint names if you used Checkpoint to Filename
3. Check PNG metadata of different images - should show different checkpoints
4. Console should still show checkpoint changes

**Before:**
```
Image 1: checkpoint = "checkpoint_A" ❌ (wrong)
Image 5: checkpoint = "checkpoint_A" ❌ (wrong, should be B)
Image 9: checkpoint = "checkpoint_A" ❌ (wrong, should be C)
```

**After:**
```
Image 1: checkpoint = "checkpoint_A" ✅
Image 5: checkpoint = "checkpoint_B" ✅
Image 9: checkpoint = "checkpoint_C" ✅
```

## Alternative: Just Use Filename

If you don't need metadata and just want to know which checkpoint was used:

1. Use "Checkpoint to Filename" node
2. Keep using standard SaveImage
3. Checkpoint name is in the filename

Simpler, but metadata won't be embedded.

## Summary

**Problem:** Standard SaveImage captures metadata once, all images get same info
**Solution:** Custom Save node that embeds checkpoint name per-image
**Result:** Each PNG has correct checkpoint in its metadata

**Update, connect checkpoint_name, done!** ✅
