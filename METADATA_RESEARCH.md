# ComfyUI Per-Image Metadata Research

## Executive Summary

After extensive research into ComfyUI-Impact-Pack's ImpactWildcardProcessor and ComfyUI's metadata system, I've discovered that **true per-image metadata updates during batch processing are NOT possible in ComfyUI** due to architectural limitations.

The key finding: **ImpactWildcardProcessor doesn't actually update metadata per-image during batch generation**. It operates at the workflow level BEFORE batch generation begins.

## The Fundamental Limitation

### How ComfyUI Batch Processing Works

1. **Workflow Execution is Single-Pass**: When you queue a workflow, ComfyUI executes each node once
2. **Batch = Tensor with Multiple Images**: A batch is represented as a single tensor with shape `[B, H, W, C]` where B is batch size
3. **Metadata is Set Once**: The `prompt` and `extra_pnginfo` parameters are passed once per node execution, not per image
4. **All Images in Batch Share Same Metadata**: When saving a batch, all images get identical workflow/prompt metadata

### What This Means

```python
# When you do this in ComfyUI:
batch_size = 5
images = ksampler(model, seed, steps, ...)  # Generates 5 images at once

# All 5 images will have:
# - Same seed (incremented internally by KSampler)
# - Same checkpoint
# - Same prompt
# - Same extra_pnginfo
```

## How ImpactWildcardProcessor Actually Works

### The Reality

**ImpactWildcardProcessor does NOT modify metadata during batch processing.** Instead:

1. **Pre-Processing**: It processes wildcards BEFORE generation starts
2. **Single Resolution**: Wildcards like `{cat|dog|bird}` are resolved to ONE value (e.g., "cat")
3. **Applied to Entire Batch**: That single value is used for all images in the batch
4. **Browser-Level Operation**: The node operates at the browser/workflow level, not during execution

### What Impact Pack Documentation Says

From ComfyUI-Impact-Pack documentation:

> "ImpactWildcardProcessor is a functionality that operates at the browser level. When running the queue prompt, ImpactWildcardProcessor generates the text."

Key parameters:
- **"Populate" mode**: Generates a NEW dynamic prompt each time you queue (but still same for entire batch)
- **"Fixed" mode**: Uses the same prompt from the textbox
- **Metadata Storage**: "When an image is generated with the 'fixed' mode, the prompt used for that particular generation is stored in the metadata"

### The Actual Use Case

ImpactWildcardProcessor is designed for:
```
Queue 1: Generate batch with "blue cat" → All images have "blue cat"
Queue 2: Generate batch with "red dog" → All images have "red dog"
Queue 3: Generate batch with "green bird" → All images have "green bird"
```

NOT for:
```
Single batch:
  Image 1: "blue cat"
  Image 2: "red dog"
  Image 3: "green bird"
```

## How ComfyUI Metadata System Works

### The Save Image Architecture

From ComfyUI's `nodes.py` - SaveImage class:

```python
class SaveImage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
            },
            "hidden": {
                "prompt": "PROMPT",           # ← Entire workflow
                "extra_pnginfo": "EXTRA_PNGINFO"  # ← Extra metadata dict
            },
        }

    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        results = []

        for (batch_number, image) in enumerate(images):
            # Convert tensor to PIL Image
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            # Create metadata ONCE (same for all images)
            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            # Save with SAME metadata
            img.save(filepath, pnginfo=metadata, compress_level=self.compress_level)

            results.append({
                "filename": filename,
                "subfolder": subfolder,
                "type": self.type
            })

        return {"ui": {"images": results}}
```

### Key Observations

1. **Metadata Created Once**: `PngInfo()` is created in the loop, but populated with the SAME `prompt` and `extra_pnginfo` values
2. **No Per-Image Variation**: The hidden inputs (`prompt`, `extra_pnginfo`) are passed once per execution
3. **Cannot Modify Dynamically**: You cannot modify these during the loop without custom logic

## Solutions and Workarounds

### ✅ Solution 1: Your Current Implementation (SaveImageWithCheckpoint)

**Status**: This is CORRECT and the best approach!

```python
class SaveImageWithCheckpoint:
    def save_images(self, images, checkpoint_name, ...):
        for (batch_number, image) in enumerate(images):
            metadata = PngInfo()

            # Standard workflow metadata (same for all)
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            # ✅ ADD CUSTOM METADATA per image
            if checkpoint_name:
                metadata.add_text("checkpoint", checkpoint_name)
                metadata.add_text("model", checkpoint_name)

            img.save(filepath, pnginfo=metadata, compress_level=self.compress_level)
```

**Why This Works**:
- You create a NEW `PngInfo()` object for each image
- You add the same workflow data to each
- You ADD custom checkpoint data on top
- Each image gets its own PNG file with unique metadata

**The Limitation**:
This only works if your `checkpoint_name` input changes per execution. If you generate a batch of 5 images in one execution, they'll all get the SAME checkpoint_name because it's passed once.

### ❌ Solution 2: Batch Processing (Won't Work)

```python
# This WON'T give you different checkpoints per image:
Checkpoint Rotation Node → Load checkpoint_1
↓
KSampler (batch_size=5) → Generates 5 images with checkpoint_1
↓
Save → All 5 images have checkpoint_1 metadata
```

**Why It Doesn't Work**: The checkpoint is loaded ONCE, then used for the entire batch.

### ✅ Solution 3: Loop-Based Generation (The Real Solution)

To get different checkpoints per image, you need to:

```
Loop iteration 1:
  Load checkpoint_1 → Generate image_1 → Save with checkpoint_1 metadata

Loop iteration 2:
  Load checkpoint_2 → Generate image_2 → Save with checkpoint_2 metadata

Loop iteration 3:
  Load checkpoint_3 → Generate image_3 → Save with checkpoint_3 metadata
```

**Implementation Options**:

#### Option A: External Loop (Multiple Queue Executions)
- Queue workflow multiple times with different checkpoints
- Each execution generates 1 image with correct metadata
- Simple but requires external automation

#### Option B: ComfyUI Loop Nodes
Use custom nodes like:
- `ComfyUI-Loop` (Hullabalo)
- `ComfyUI-Loop-image`
- `comfyui-easy-use` (has loop nodes)

Example flow:
```
Loop Controller →
  ↓
  Checkpoint Rotation (uses loop index) →
  Load Checkpoint →
  KSampler (batch_size=1) →
  SaveImageWithCheckpoint (gets correct checkpoint name)
  ↓
Loop Back
```

#### Option C: Custom Node with Internal Loop

Create a node that:
1. Takes a list of checkpoints
2. Internally loops through them
3. Generates one image per checkpoint
4. Returns all images with correct metadata

```python
class CheckpointRotationWithGeneration:
    def generate_images(self, checkpoints, prompt, steps, ...):
        all_images = []
        all_metadata = []

        for checkpoint in checkpoints:
            # Load checkpoint
            model, clip, vae = load_checkpoint(checkpoint)

            # Generate single image
            image = ksampler(model, prompt, steps, cfg, sampler, scheduler, ...)

            # Store with metadata
            all_images.append(image)
            all_metadata.append({"checkpoint": checkpoint})

        # Combine images into batch
        batch = torch.cat(all_images, dim=0)

        return (batch, all_metadata)
```

### ✅ Solution 4: Split Batch + Individual Processing

```
Generate Batch (5 images with checkpoint_1)
↓
Batch to Image List (split into 5 individual images)
↓
Image 1 → Process individually → Save
Image 2 → Process individually → Save
Image 3 → Process individually → Save
...
```

**Problem**: All images were still generated with the same checkpoint, so metadata would be correct but images are all from checkpoint_1.

## How Other Extensions Handle This

### ComfyUI-SaveImageWithMetaData

From nkchocoai's extension:

```python
def save_images(images: list[torch.Tensor], ..., metadata: Metadata):
    for image in images:
        # Builds A1111-format parameter string
        a111_params = f"Steps: {steps}, Sampler: {name}, CFG scale: {cfg}, Seed: {seed}, ..."

        # Saves with custom metadata per image
        save_image(img, filepath, metadata.a111_params, prompt, extra_pnginfo)
```

**Key Insight**: They build metadata from node inputs, but those inputs are STILL the same for the entire batch. They just format it differently.

### ComfyUI-Prompt-Reader (Prompt Saver)

This extension's "Prompt Saver" node:
- Receives metadata inputs
- Embeds them in A1111 format
- But still has the same limitation: metadata is per-execution, not per-image in batch

## The Architecture Constraint

### Why ComfyUI Can't Do Per-Image Batch Metadata

```
┌─────────────────────────────────────────────┐
│ ComfyUI Execution Model                     │
├─────────────────────────────────────────────┤
│                                             │
│  Queue Workflow →                           │
│    ↓                                        │
│  Execute Each Node Once                     │
│    ↓                                        │
│  Node receives inputs (including metadata)  │
│    ↓                                        │
│  Node processes (may generate batch)        │
│    ↓                                        │
│  Node returns outputs                       │
│    ↓                                        │
│  Next Node executes...                      │
│                                             │
│  [All metadata is passed once per node]    │
└─────────────────────────────────────────────┘
```

**The fundamental issue**:
- Nodes execute once
- Batches are processed as a unit
- Metadata is provided once per execution
- No mechanism to vary metadata per item in batch

### What Would Be Needed

To support per-image metadata in batches, ComfyUI would need:

1. **Metadata Arrays**: Pass arrays of metadata (one per batch item)
   ```python
   metadata_per_image = [
       {"checkpoint": "model1.safetensors"},
       {"checkpoint": "model2.safetensors"},
       {"checkpoint": "model3.safetensors"},
   ]
   ```

2. **Batch-Aware Save Nodes**: Nodes that iterate with index-aware metadata
   ```python
   for i, image in enumerate(images):
       metadata = metadata_per_image[i]
       save_with_metadata(image, metadata)
   ```

3. **Execution System Changes**: Core changes to how ComfyUI passes hidden inputs

**This doesn't exist in ComfyUI core**, and would require major architectural changes.

## Recommendations for Your Checkpoint Rotation Node

### What You Should Do

Your current implementation is **already correct**! The issue is not with the metadata saving, but with the workflow design.

#### Current Status ✅

`SaveImageWithCheckpoint` correctly:
1. Creates individual `PngInfo()` for each image
2. Adds workflow metadata (prompt, extra_pnginfo)
3. Adds custom checkpoint metadata
4. Saves each image with its metadata

#### What Users Need to Understand

**For per-image checkpoint metadata, you CANNOT use batch generation**. Instead:

**Recommended Workflow**:
```
┌─────────────────────────────────────────┐
│ Loop Start (iterations = N)             │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ CheckpointRotationWithCounter           │
│ - Uses loop index as batch_index        │
│ - Returns checkpoint_name               │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Load Checkpoint                         │
│ - Loads the selected checkpoint         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ KSampler                                │
│ - batch_size = 1 (single image)         │
│ - control_after_generate = "increment"  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ SaveImageWithCheckpoint                 │
│ - checkpoint_name = from rotation node  │
│ - Saves with correct metadata           │
└─────────────────────────────────────────┘
              ↓
        Loop Back
```

#### Documentation to Add

Add to your README:

```markdown
## Important: Batch Generation Limitation

⚠️ **You cannot use traditional batch generation** (batch_size > 1) with checkpoint rotation
if you want correct per-image checkpoint metadata.

### Why?

ComfyUI generates all images in a batch using the SAME checkpoint. Even though our
SaveImageWithCheckpoint node can add different metadata to each image, all images
would be generated with the same model.

### Solution: Use Loop-Based Generation

Instead of generating a batch of 5 images at once:
- Use a loop node to iterate 5 times
- Each iteration: load different checkpoint → generate 1 image → save with metadata
- Result: 5 images, each with correct checkpoint metadata AND generated with different models

### Recommended Loop Nodes

- ComfyUI-Loop by Hullabalo
- ComfyUI-easy-use (has loop functionality)
- Or queue your workflow multiple times with different parameters
```

## Alternative Approach: Post-Processing Metadata

If you want to keep batch generation, you could:

1. Generate batch with checkpoint A
2. Track which image uses which checkpoint (external state)
3. After generation, modify saved PNG files to update metadata

This would require:
```python
def update_saved_image_metadata(image_path, new_checkpoint):
    """Modify PNG metadata after file is saved"""
    img = Image.open(image_path)

    # Read existing metadata
    metadata = PngInfo()
    if img.info:
        for k, v in img.info.items():
            if k != "checkpoint":  # Skip old checkpoint
                metadata.add_text(k, v)

    # Add new checkpoint metadata
    metadata.add_text("checkpoint", new_checkpoint)

    # Re-save with updated metadata
    img.save(image_path, pnginfo=metadata)
```

But this is hacky and defeats the purpose of having a clean node-based solution.

## Conclusion

### The Truth About ImpactWildcardProcessor

ImpactWildcardProcessor **does NOT** provide per-image metadata updates during batch generation. It:
- Processes wildcards BEFORE generation
- Resolves ONE value per queue
- That value applies to ALL images in the batch
- Metadata is stored showing which resolved value was used

### The Truth About Per-Image Metadata

ComfyUI's architecture **does NOT support** varying metadata per image within a single batch because:
- Nodes execute once per workflow run
- Hidden inputs (prompt, extra_pnginfo) are passed once
- Batches are processed as atomic units
- No mechanism exists to pass per-image metadata arrays

### Your Solution is Correct

Your `SaveImageWithCheckpoint` node is **the right approach** for adding custom metadata. The only requirement is:
- **Don't use batch generation** if you want different checkpoints per image
- **Use loop-based generation** instead
- Each loop iteration loads a different checkpoint and generates one image

### The Key Mechanism

The mechanism for per-image metadata is:
```python
for each_image in batch:
    metadata = PngInfo()
    # Add standard metadata (same for all)
    metadata.add_text("prompt", json.dumps(prompt))
    # Add custom metadata (can be different per image)
    metadata.add_text("your_custom_field", your_custom_value)
    save_image(image, metadata)
```

But remember: `your_custom_value` must come from your node's inputs, which are provided once per execution. So for truly different values, you need different executions (loops).

## References

### Source Code Examples

1. **ComfyUI SaveImage**: `https://github.com/comfyanonymous/ComfyUI/blob/master/nodes.py`
   - Shows standard metadata handling
   - Creates PngInfo per image but uses same prompt/extra_pnginfo

2. **ComfyUI-SaveImageWithMetaData**: `https://github.com/nkchocoai/ComfyUI-SaveImageWithMetaData`
   - Shows custom metadata extraction from KSampler
   - Still limited to same metadata per batch

3. **ComfyUI-Impact-Pack**: `https://github.com/ltdrdata/ComfyUI-Impact-Pack`
   - ImpactWildcardProcessor in `modules/impact/wildcards.py`
   - Operates at pre-processing level, not during generation

### Documentation

1. **ComfyUI Custom Node Docs**: `https://docs.comfy.org/custom-nodes/walkthrough`
   - Hidden inputs: PROMPT, EXTRA_PNGINFO, UNIQUE_ID
   - How to access workflow data

2. **ComfyUI Hidden Inputs**: `https://docs.comfy.org/custom-nodes/backend/more_on_inputs`
   - EXTRA_PNGINFO: "dictionary that will be copied into the metadata of any .png files saved"
   - PROMPT: "complete prompt sent by the client to the server"

3. **Impact Pack Tutorial**: `https://github.com/ltdrdata/ComfyUI-extension-tutorials/blob/Main/ComfyUI-Impact-Pack/tutorial/ImpactWildcard.md`
   - Wildcard syntax and usage
   - How populate vs fixed mode works

---

**Created**: 2025-11-05
**Research by**: Claude (Anthropic)
**For**: ComfyUI Checkpoint Rotation Node Project
