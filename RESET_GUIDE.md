# How to Reset the Counter

## The Problem

When using "control_after_generate: increment" on a Primitive INT, the counter maintains **persistent state**. Even if you change the displayed value to 0, it continues counting from where it left off internally.

**Example:**
- You generate 139 images (counter reaches 139)
- You set Primitive value to 0
- You queue again
- **Counter is still 139!** (Not 0)

## Solution 1: Use the Built-in Reset (NEW!) ⭐

I added a **"reset_on_next"** toggle to fix this:

### Steps:
1. In **Checkpoint Rotation (Batch)** node
2. Enable **"reset_on_next"** checkbox ✅
3. Queue your next batch
4. **Important**: After generation, **disable "reset_on_next"** again

### What happens:
- When reset_on_next is enabled, the node captures the current counter value as an "offset"
- All future counter values are normalized: `normalized_counter = counter - offset`
- Your images now start from "Image #0" again
- Checkpoints rotate properly from the beginning

### Console output:
```
[CheckpointRotation] ⚠️ RESET ACTIVATED!
  Counter offset set to 139
  Next images will start from checkpoint 1
  Remember to DISABLE 'reset_on_next' after this generation!
```

### Metadata:
```
Image #0 (raw counter: 139)
Checkpoint 1/34
File: JANKUV5NSFWTrainedNoobai_v40.safetensors
Image 1/4 with this checkpoint
Next change at image #4
```

Now you see:
- **Image #0** (normalized) instead of #139
- **Image 1/4** (correct position in cycle)
- **Raw counter: 139** (for debugging)

## Solution 2: Delete and Recreate Primitive

If you don't want to use reset_on_next:

1. **Delete** the Primitive INT node
2. **Add a new** Primitive INT node
3. Set to `0`
4. Set "control_after_generate" to "increment"
5. **Reconnect** to Checkpoint Rotation node

Fresh node = fresh state.

## Solution 3: Toggle control_after_generate

1. Double-click left side of Primitive
2. Change "control_after_generate" from "increment" to **"fixed"**
3. Set value to `0`
4. Queue once (just to let it settle)
5. Change back to **"increment"**

## Solution 4: Restart ComfyUI

Nuclear option - restart ComfyUI completely. All widget states reset.

## Best Practice

**Use reset_on_next toggle:**
- ✅ No need to delete nodes
- ✅ No need to reconnect wires
- ✅ Works immediately
- ✅ Preserves your workflow setup

**When to reset:**
- Starting a new batch series
- Testing different checkpoints
- When you see weird Image # numbers
- When checkpoint cycle is wrong

**Remember to disable reset_on_next after using it!** Otherwise it will keep resetting on every generation.

## Understanding the Metadata

**Normal operation:**
```
Image #8 (raw counter: 8)
Checkpoint 3/34
Image 1/4 with this checkpoint
```

**After many generations without reset:**
```
Image #139 (raw counter: 139)
Checkpoint 1/34
Image 4/4 with this checkpoint  ← Wrong! Should be 1/4
```
→ This means you need to reset!

**After reset_on_next:**
```
Image #0 (raw counter: 139)
Checkpoint 1/34
Image 1/4 with this checkpoint  ← Correct!
```

## Why Does This Happen?

ComfyUI's "control_after_generate" widgets maintain **internal state** that persists across:
- Queue operations
- Value changes
- Workflow saves/loads

The only way to truly reset is:
1. Delete/recreate the widget
2. Restart ComfyUI
3. Use the built-in offset mechanism (reset_on_next)

The offset mechanism is cleanest because it doesn't fight against ComfyUI's state management - it works with it.
