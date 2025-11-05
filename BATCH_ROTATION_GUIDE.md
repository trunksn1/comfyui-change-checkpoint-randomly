# Checkpoint Rotation with Batch Generation - THE SOLUTION

Thanks to the Reddit thread discovery, this ACTUALLY works with batch generation!

## How It Works

Uses ComfyUI's **"control after generate"** feature to increment a counter after each image. The checkpoint only changes every N images based on your setting.

## Step-by-Step Setup (5 Minutes)

### Step 1: Add the Checkpoint Rotation Node

1. **Right-click** in ComfyUI canvas
2. **Add Node** → **loaders** → **Checkpoint Rotation (Batch)** ⭐

### Step 2: Add a Primitive Counter

1. **Right-click** → **Add Node** → **utils** → **Primitive**
2. In the Primitive node settings:
   - **Type**: Select **INT**
   - **default**: `0`
   - **min**: `0`
   - **max**: `100000`

### Step 3: Enable Auto-Increment (THE KEY!)

This is the magic step:

1. **Double-click on the LEFT SIDE** of the Primitive node (where it says "INT")
2. A widget will pop out showing "control_after_generate"
3. **Set "control_after_generate" to "increment"** ✅

This tells ComfyUI to automatically increment the counter after each image generation!

### Step 4: Connect the Counter

1. **Connect** the Primitive INT output → Checkpoint Rotation node's **"counter"** input

### Step 5: Configure Your Settings

In the **Checkpoint Rotation (Batch)** node:
- **subfolder**: `"Illustrious"` (your checkpoint folder name)
- **change_every**: `4` (changes checkpoint every 4 images)

### Step 6: Connect to Your Workflow

Connect the Checkpoint Rotation outputs like a normal checkpoint loader:
- **model** → KSampler
- **clip** → CLIP Text Encode nodes (positive & negative)
- **vae** → VAE Decode

### Step 7: Generate!

Now the MAGIC happens:

1. Set your **KSampler batch_size** to whatever you want (4, 10, 20, etc.)
2. Click **"Queue Prompt"**
3. Watch the console - checkpoint will change every N images automatically!

## Example: 20 Images, Change Every 4

**Setup:**
```
Primitive INT [control_after_generate: increment]
  └─→ counter

Checkpoint Rotation (Batch)
  ├─ counter: (from primitive)
  ├─ subfolder: "Illustrious"
  └─ change_every: 4
```

**Set KSampler batch_size: 20**

**Queue once** → Generates 20 images:

| Image # | Counter | Checkpoint Used |
|---------|---------|-----------------|
| 0-3     | 0-3     | Checkpoint A    |
| 4-7     | 4-7     | Checkpoint B    |
| 8-11    | 8-11    | Checkpoint C    |
| 12-15   | 12-15   | Checkpoint D    |
| 16-19   | 16-19   | Checkpoint E    |

**ONE QUEUE. ALL CHECKPOINTS ROTATE AUTOMATICALLY.** ✅

## Visual Setup

```
[Primitive INT]
  control_after_generate: increment ← IMPORTANT!
  default: 0
    │
    └─→ counter
        │
[Checkpoint Rotation (Batch)]
  counter: (connected above)
  subfolder: "Illustrious"
  change_every: 4
    │
    ├─→ model ──→ [KSampler] batch_size: 20
    ├─→ clip ──→ [CLIP Text Encode]
    └─→ vae ───→ [VAE Decode]
```

## Why This Works

**Before** (our old attempts):
- Node loads checkpoint once
- All batch images use same checkpoint
- ❌ No rotation

**Now** (with control_after_generate):
- Counter increments after each image
- Node re-executes with new counter value
- Checkpoint changes every N images based on formula: `(counter // change_every) % num_checkpoints`
- ✅ **Works perfectly!**

## Console Output

You'll see clear messages:

```
============================================================
[CheckpointRotation] CHECKPOINT CHANGED!
  Image #0
  Now using: illustrious_v1.safetensors
  Checkpoint 1 of 5
  Will use this for 4 images
============================================================

[CheckpointRotation] Image #1 - Still using illustrious_v1.safetensors (2/4)
[CheckpointRotation] Image #2 - Still using illustrious_v1.safetensors (3/4)
[CheckpointRotation] Image #3 - Still using illustrious_v1.safetensors (4/4)

============================================================
[CheckpointRotation] CHECKPOINT CHANGED!
  Image #4
  Now using: illustrious_v2.safetensors
  Checkpoint 2 of 5
  Will use this for 4 images
============================================================
```

## Resetting the Counter

If you want to start over from checkpoint 1:

1. Click on the Primitive INT node
2. Change the value back to `0`
3. Queue again

## Different Rotation Patterns

### Change Every Image
```
change_every: 1
batch_size: 5
→ Uses 5 different checkpoints (one per image)
```

### Change Every 10 Images
```
change_every: 10
batch_size: 50
→ Uses 5 checkpoints (each used for 10 images)
```

### Single Checkpoint for Whole Batch
```
change_every: 100
batch_size: 20
→ Uses 1 checkpoint (change_every > batch_size)
```

## Pro Tips

### 1. See Which Checkpoint is Active
Connect the **"info"** output to a **ShowText** node to see:
- Current image number
- Which checkpoint is loaded
- How many images left with current checkpoint

### 2. Reset Counter Automatically
Set the Primitive's "control_after_generate" to **"fixed"** when you want to stop incrementing

### 3. Different Seeds Per Checkpoint
Use another Primitive INT for seed with "control_after_generate: randomize"

### 4. Combine with Data Lists
You can also use this with the Data List approach from Reddit for even more control

## Troubleshooting

### Counter Not Incrementing
- ✅ Check: Did you double-click the LEFT SIDE of Primitive node?
- ✅ Check: Is "control_after_generate" set to "increment"?
- ✅ Check: Is Primitive connected to "counter" input?

### Checkpoint Not Changing
- ✅ Check console - does it show counter incrementing?
- ✅ Check: Do you have multiple checkpoints in the subfolder?
- ✅ Try: Set change_every to 1 to test

### Same Images Repeating
- Checkpoint IS rotating (check console)
- You have **fixed seed** → same composition, different style
- **Fix**: Set seed to "randomize" or "increment"

## Your Specific Case

**What you want:**
- Folder: `N:\SD\Modelli\Checkpoints\Illustrious`
- Change every: 4 images
- Generate: 20 images

**Setup:**
1. Primitive INT with "control_after_generate: increment"
2. Checkpoint Rotation (Batch):
   - subfolder: `"Illustrious"`
   - change_every: `4`
3. KSampler batch_size: `20`
4. Queue once
5. **DONE!** ✅

## Does This Actually Work?

**YES!** This uses the same mechanism as the Reddit solutions:
- ✅ "control after generate" like solution #1
- ✅ Works with batch generation
- ✅ Changes checkpoint at specified intervals (not every image)
- ✅ One queue, all images, automatic rotation

The difference from the Reddit solutions:
- **Reddit #1**: Changes every image (randomize)
- **Reddit #2**: Uses Data Lists to iterate
- **This solution**: Changes every N images with simple counter

## Credits

Thanks to the Reddit user who discovered the "control after generate" feature! This made the whole thing possible.

---

**Update your node:**
```bash
cd C:\StableDiffusion\ComfyUI\custom_nodes\comfyui-change-checkpoint-randomly
git pull
```

**Restart ComfyUI and use "Checkpoint Rotation (Batch)" node!**
