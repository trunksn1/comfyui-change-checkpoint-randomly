# Key Findings and Recommendations

## Executive Summary

After researching ComfyUI-Impact-Pack's ImpactWildcardProcessor and ComfyUI's metadata system, I've discovered that:

1. **ImpactWildcardProcessor does NOT update metadata per-image during batch generation**
2. **Your current approach has a fundamental architectural limitation**
3. **There is a solution, but it requires a different workflow design**

## Critical Discovery: The Batch Generation Problem

### Your Current Implementation Issue

Your `CheckpointRotationWithCounter` node with `control_after_generate: increment` has a **fundamental flaw**:

```
What you think happens:
┌────────────────────────────────────────────────────────┐
│ Batch generation with batch_size=4, change_every=2    │
├────────────────────────────────────────────────────────┤
│ Image 1: counter=0 → Load checkpoint_1 → Generate     │
│ Image 2: counter=1 → Load checkpoint_1 → Generate     │
│ Image 3: counter=2 → Load checkpoint_2 → Generate  ✓  │
│ Image 4: counter=3 → Load checkpoint_2 → Generate  ✓  │
└────────────────────────────────────────────────────────┘

What actually happens:
┌────────────────────────────────────────────────────────┐
│ Batch generation with batch_size=4, change_every=2    │
├────────────────────────────────────────────────────────┤
│ CheckpointRotationWithCounter runs ONCE               │
│   - counter=0                                          │
│   - Loads checkpoint_1                                 │
│   - Returns model, clip, vae                           │
│                                                        │
│ KSampler runs ONCE                                     │
│   - Receives model from checkpoint_1                   │
│   - Generates ALL 4 images with checkpoint_1           │
│   - counter increments AFTER each image                │
│   - But checkpoint loader doesn't re-execute! ✗        │
│                                                        │
│ Result: All 4 images use checkpoint_1                  │
└────────────────────────────────────────────────────────┘
```

### Why This Doesn't Work

**ComfyUI's Execution Model**:
1. Each node executes **ONCE** per workflow queue
2. `control_after_generate: increment` only modifies the primitive value
3. **It does NOT cause upstream nodes to re-execute**
4. The counter increments, but your checkpoint loader doesn't see those changes until the next queue

**The Result**:
- All images in a batch are generated with the SAME checkpoint
- Even though your `SaveImageWithCheckpoint` adds checkpoint metadata correctly
- The metadata says "checkpoint_1" for all images because they all actually used checkpoint_1

## How ImpactWildcardProcessor Actually Works

### The Reality

ImpactWildcardProcessor **does NOT** solve the per-image metadata problem. Here's what it actually does:

**Behavior**:
```python
# Wildcard text: "A {cat|dog|bird} in the park"

# Populate mode (default):
Queue 1: Resolves to "A cat in the park" → All images in this queue get "cat"
Queue 2: Resolves to "A dog in the park" → All images in this queue get "dog"
Queue 3: Resolves to "A bird in the park" → All images in this queue get "bird"

# Fixed mode:
Uses whatever is in the second textbox for ALL images
```

**Key Point**: It operates at the **workflow level**, not the **image level**. One resolution per queue, not per image.

### From Impact Pack Documentation

> "ImpactWildcardProcessor is a functionality that operates at the browser level. When running the queue prompt, ImpactWildcardProcessor generates the text."

Translation: It processes wildcards BEFORE ComfyUI starts generating images, not during.

## The Solution: Loop-Based Generation

### Why Loops Are Necessary

To get different checkpoints per image, you need:

```
Execution 1:
  CheckpointRotation(counter=0) → checkpoint_1
  KSampler(batch_size=1) → image_1
  Save → image_1 with checkpoint_1 metadata

Execution 2:
  CheckpointRotation(counter=1) → checkpoint_1
  KSampler(batch_size=1) → image_2
  Save → image_2 with checkpoint_1 metadata

Execution 3:
  CheckpointRotation(counter=2) → checkpoint_2
  KSampler(batch_size=1) → image_3
  Save → image_3 with checkpoint_2 metadata

Execution 4:
  CheckpointRotation(counter=3) → checkpoint_2
  KSampler(batch_size=1) → image_4
  Save → image_4 with checkpoint_2 metadata
```

Each image requires its own **execution cycle**, not just its own slot in a batch.

### Implementation Options

#### Option 1: External Loop (Queue Multiple Times)

**Simplest approach**:
1. Set up your workflow with `CheckpointRotationWithCounter`
2. Queue it multiple times
3. Between each queue, the counter increments
4. Each execution uses the correct checkpoint

**Pros**:
- Works with your current implementation
- Simple to understand
- No additional nodes needed

**Cons**:
- Manual process (or need external automation)
- Must queue N times for N images
- Slower (re-loads checkpoint each time)

#### Option 2: Use Loop Nodes

**Use existing loop nodes**:
- **ComfyUI-Loop** by Hullabalo: https://github.com/Hullabalo/ComfyUI-Loop
- **ComfyUI-easy-use**: Has loop functionality built-in
- **ComfyUI-node-iterator**: https://github.com/timelinedr/comfyui-node-iterator

**Workflow**:
```
Loop Start (N iterations)
  ↓
  CheckpointRotationWithCounter (gets loop index)
  ↓
  Load Checkpoint (from rotation node)
  ↓
  CLIP Text Encode
  ↓
  KSampler (batch_size=1, control_after_generate: increment)
  ↓
  SaveImageWithCheckpoint (checkpoint_name from rotation node)
  ↓
Loop Back
```

**Pros**:
- Automatic iteration
- Each iteration = new execution cycle
- Checkpoint loader re-executes each time
- Metadata will be correct

**Cons**:
- Requires installing loop node extension
- Slightly more complex workflow
- May need to learn new node

#### Option 3: API-Based Generation

**Use ComfyUI API**:
```python
import requests
import json

def generate_with_rotation(num_images, change_every):
    for i in range(num_images):
        # Load workflow
        with open("workflow.json") as f:
            workflow = json.load(f)

        # Update counter in workflow
        workflow["nodes"]["checkpoint_rotation"]["counter"] = i

        # Queue workflow
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json={"prompt": workflow}
        )

        # Wait for completion...
        # Check results...

generate_with_rotation(20, 4)
```

**Pros**:
- Full control over execution
- Can automate complex scenarios
- Works with current implementation

**Cons**:
- Requires Python scripting
- More complex setup
- Not pure ComfyUI workflow

## Recommended Implementation

### What You Should Do

I recommend **Option 2 (Loop Nodes)** as the best balance of functionality and usability.

### Step-by-Step Guide

1. **Install a Loop Node Extension**
   ```bash
   cd ComfyUI/custom_nodes/
   git clone https://github.com/Hullabalo/ComfyUI-Loop
   ```

2. **Update Your README with This Workflow**

   ```markdown
   ## ⚠️ IMPORTANT: How to Use Checkpoint Rotation

   ### The Problem with Batch Generation

   You **CANNOT** use `batch_size > 1` in KSampler with checkpoint rotation if you want:
   - Different checkpoints per image
   - Correct checkpoint metadata per image

   **Why?** ComfyUI executes each node ONCE per queue. All images in a batch are
   generated with the SAME checkpoint, even if the counter increments between images.

   ### The Correct Way: Loop-Based Generation

   To generate multiple images with different checkpoints, use a loop:

   **Required**: Install ComfyUI-Loop extension
   ```bash
   cd ComfyUI/custom_nodes/
   git clone https://github.com/Hullabalo/ComfyUI-Loop
   ```

   **Workflow Setup**:
   ```
   1. Add "Loop Start" node
      - Set iterations = number of images you want

   2. Add "Checkpoint Rotation (Batch)" node
      - subfolder = your checkpoint folder
      - change_every = how many images per checkpoint
      - counter: Connect to Loop Start's "iteration" output

   3. Add "CLIP Text Encode" nodes (positive and negative)
      - Connect CLIP from checkpoint rotation

   4. Add "KSampler"
      - Connect model from checkpoint rotation
      - Set batch_size = 1 (must be 1!)
      - Set control_after_generate = "increment"

   5. Add "Save Image (with Checkpoint Info)" node
      - Connect images from VAE Decode
      - Connect checkpoint_name from rotation node

   6. Add "Loop End" node
      - Connect image output to loop back
   ```

   **Example for 20 Images with Change Every 4**:
   - Loop iterations: 20
   - change_every: 4
   - Result: Checkpoint changes at images 0, 4, 8, 12, 16
   - Each image gets correct checkpoint metadata

   ### Alternative: Queue Multiple Times

   If you don't want to use loops:
   1. Set up workflow normally
   2. Set queue count to number of images you want
   3. Each queue generates 1 image with correct checkpoint
   ```

3. **Add This Warning to Your Node Description**

   Update `CheckpointRotationWithCounter` docstring:

   ```python
   """
   Checkpoint rotation that works with loop-based generation.

   ⚠️ IMPORTANT: This node requires LOOP-BASED generation, not batch generation.

   Why? ComfyUI executes nodes once per queue. If you use batch_size > 1,
   all images will be generated with the SAME checkpoint, even though the
   counter increments. The checkpoint loader doesn't re-execute during batch.

   Correct usage:
   1. Install ComfyUI-Loop extension
   2. Use Loop Start/End nodes
   3. Set KSampler batch_size = 1
   4. Loop N times for N images
   5. Each loop iteration loads a different checkpoint

   Alternative:
   - Queue your workflow multiple times
   - Each queue generates 1 image with correct checkpoint
   ```

4. **Consider Creating a Helper Node**

   You could create a `CheckpointRotationLoop` node that:
   - Combines checkpoint rotation with internal looping
   - Takes total_images and change_every as inputs
   - Internally manages the loop
   - Returns all images at once with correct metadata

   This would make it easier for users who don't want to set up loops manually.

## What Impact Pack Does Right

Even though ImpactWildcardProcessor doesn't solve your specific problem, it does some things well:

### 1. Clear Documentation

From their tutorial:
> "If the mode is set to 'populate', a dynamic prompt is generated with each execution"

They clearly state "each execution", not "each image".

### 2. Two-Textbox Design

- First textbox: Input with wildcards
- Second textbox: Resolved output
- Users can see what was actually used

**You could adopt this**:
```
Input: subfolder, change_every, counter
Display: "Currently using: model_name.safetensors"
```

### 3. Metadata Storage

They save the resolved prompt in metadata so users can see what was actually used.

**You already do this** with `SaveImageWithCheckpoint`!

## Metadata Mechanism Explained

### How to Add Custom Metadata (You're Already Doing This Right!)

```python
# Your SaveImageWithCheckpoint implementation - THIS IS CORRECT! ✓

for (batch_number, image) in enumerate(images):
    # Create NEW PngInfo for each image
    metadata = PngInfo()

    # Add standard workflow metadata (same for all images in batch)
    if prompt is not None:
        metadata.add_text("prompt", json.dumps(prompt))
    if extra_pnginfo is not None:
        for x in extra_pnginfo:
            metadata.add_text(x, json.dumps(extra_pnginfo[x]))

    # ✓ Add your custom metadata (this part is perfect!)
    if checkpoint_name:
        metadata.add_text("checkpoint", checkpoint_name)
        metadata.add_text("model", checkpoint_name)

    # Save with metadata
    img.save(filepath, pnginfo=metadata, compress_level=self.compress_level)
```

**Why this works**:
- You create a fresh `PngInfo()` for each image
- You add the same workflow data to each (that's fine)
- You add custom checkpoint data
- Each PNG file gets its own metadata

**The only limitation**:
Your `checkpoint_name` input is the same for all images in the batch because it's passed once per execution. So this node works perfectly when used with loops (one image per execution).

### What You Can't Do

```python
# This is NOT possible in ComfyUI's architecture:
def save_images(self, images, checkpoint_names_array):  # ✗ Can't pass array
    for i, image in enumerate(images):
        checkpoint = checkpoint_names_array[i]  # ✗ No per-image inputs
        ...
```

ComfyUI doesn't support passing arrays of metadata (one per batch item). All inputs are provided once per execution.

## Summary of Recommendations

### 1. Update Documentation (High Priority)

Add clear warnings about batch generation limitations:
- Can't use `batch_size > 1` for per-image checkpoint rotation
- Must use loops or multiple queues
- Explain why (node execution model)

### 2. Recommend Loop-Based Workflows (High Priority)

Provide example workflows using:
- ComfyUI-Loop extension
- Your CheckpointRotationWithCounter
- Your SaveImageWithCheckpoint
- KSampler with batch_size=1

### 3. Consider a Combined Node (Medium Priority)

Create `CheckpointRotationWithLoop` that:
- Takes total_images, change_every, subfolder
- Internally manages looping
- Returns all images with correct metadata
- Simpler for users (no external loop extension needed)

### 4. Add Visual Feedback (Low Priority)

Add to your rotation node:
```python
RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING")
RETURN_NAMES = ("model", "clip", "vae", "checkpoint_name", "visual_info")

# Return formatted info string
visual_info = f"""
╔══════════════════════════════════════╗
║ Checkpoint Rotation Status           ║
╠══════════════════════════════════════╣
║ Current: {checkpoint_basename}       ║
║ Index:   {checkpoint_num}/{total}    ║
║ Images:  {images_count}/{change_every}║
║ Next:    Image #{next_change}        ║
╚══════════════════════════════════════╝
"""
```

### 5. Your Current Code is Good! (Validation)

Your `SaveImageWithCheckpoint` implementation is **correct** and follows ComfyUI best practices:
- Proper hidden inputs (prompt, extra_pnginfo)
- Creates PngInfo per image
- Adds custom metadata correctly
- Returns proper ui dictionary

The issue was never with your code, but with the workflow design (batch vs loop).

## Testing Checklist

To verify everything works:

- [ ] Install ComfyUI-Loop extension
- [ ] Create workflow with Loop Start/End
- [ ] Add CheckpointRotationWithCounter with loop index as counter
- [ ] Set KSampler batch_size = 1
- [ ] Set loop iterations = 8, change_every = 2
- [ ] Generate and verify:
  - Images 0-1 have checkpoint A metadata
  - Images 2-3 have checkpoint B metadata
  - Images 4-5 have checkpoint C metadata
  - Images 6-7 have checkpoint D metadata
- [ ] Verify each image was actually generated with the correct checkpoint (visual inspection)

## References

1. **METADATA_RESEARCH.md** - Full technical analysis of ComfyUI metadata system
2. **ComfyUI-Loop**: https://github.com/Hullabalo/ComfyUI-Loop
3. **ComfyUI-Impact-Pack**: https://github.com/ltdrdata/ComfyUI-Impact-Pack
4. **ComfyUI SaveImage source**: https://github.com/comfyanonymous/ComfyUI/blob/master/nodes.py

## Conclusion

Your implementation is solid! The issue was with the workflow design, not your code.

**Key Takeaways**:
1. ✅ `SaveImageWithCheckpoint` is implemented correctly
2. ✅ `CheckpointRotationWithCounter` logic is correct
3. ✗ Batch generation (`batch_size > 1`) won't work for per-image checkpoint rotation
4. ✓ Loop-based generation (multiple executions) is the solution
5. ✓ Each loop iteration loads a different checkpoint and generates one image

Update your documentation to guide users toward loop-based workflows, and your node will work perfectly!

---

**Created**: 2025-11-05
**For**: ComfyUI Checkpoint Rotation Node Project
