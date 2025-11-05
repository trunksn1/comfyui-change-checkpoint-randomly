# Simple Checkpoint Rotation - THE TRUTH

## What You Need to Know

**THE REALITY**: ComfyUI doesn't support changing checkpoints mid-batch automatically. When you click "Queue Prompt," it loads ONE checkpoint and uses it for ALL images in that run.

**TO ROTATE CHECKPOINTS**: You must queue the prompt multiple times (once per image).

## The Simple Way (2 Settings Only!)

Use the **"Simple Checkpoint Rotation"** node:

### Settings:
1. **subfolder**: `"Illustrious"` (or whatever folder you want)
2. **change_every**: `4` (checkpoint changes every 4 images)

That's it. Two settings.

## How to Actually Generate 20 Images with Rotation

You have 3 options:

### Option 1: Queue Multiple Times (Manual)

**This is what you need to do:**

1. Set up your workflow with "Simple Checkpoint Rotation" node
2. Click "Queue Prompt" button
3. Wait for it to generate 1 image
4. Click "Queue Prompt" again
5. Wait for it to generate 1 image
6. Repeat 20 times

Yes, 20 separate clicks. Yes, it's annoying. But this is how ComfyUI works.

**Result**:
- Clicks 1-4: Checkpoint A
- Clicks 5-8: Checkpoint B
- Clicks 9-12: Checkpoint C
- Etc.

### Option 2: Use ComfyUI's Queue

**Better way:**

1. Set up workflow
2. Click "Queue Prompt"
3. **Immediately** click "Queue Prompt" again (before the first finishes)
4. Keep clicking 20 times rapidly
5. ComfyUI queues all 20 - they generate one after another automatically

Each queued prompt = 1 image generation = counter increments = checkpoint rotates.

### Option 3: Use Extra Queue Setting

In ComfyUI interface:
1. Look for the queue/batch controls
2. There's usually a "Queue Size" or "Batch Count" setting
3. Set it to 20
4. Click Queue once
5. It queues 20 separate generations

This is the easiest automated way without extra nodes.

## Why It Doesn't Work Like You Expect

ComfyUI's execution model:
```
Queue Prompt → Load all nodes → Execute workflow once → Done
```

The checkpoint loader node runs ONCE per queue, not once per batch image.

To run it 20 times, you need 20 queue executions, not 1 queue with batch_size=20.

## Your Specific Case

**What you want**:
- Folder: `N:\SD\Modelli\Checkpoints\Illustrious`
- Change every 4 images
- Generate 20 images total

**Setup**:
1. Add "Simple Checkpoint Rotation" node
   - subfolder: `"Illustrious"`
   - change_every: `4`
   - auto_increment: `True` ✅

2. Connect like normal checkpoint loader:
   - model → KSampler
   - clip → CLIP Text Encode
   - vae → VAE Decode

3. **Set KSampler batch_size to 1** (not 20!)

4. Queue the prompt 20 times (use Option 2 above)

## What About the Seed?

If you set a **fixed seed in KSampler**, you'll get the **same noise pattern** for each image, but with **different checkpoints**, so images will be **similar but different** (different styles/quality from different models).

If you want **completely different images**, set seed to **"randomize"** or **"increment"** in KSampler.

## The "Auto Increment" Setting

- **True** (default): Counter goes up automatically (0, 1, 2, 3...)
- **False**: You control it manually with "manual_index" input

Leave it on **True** unless you know what you're doing.

## Testing If It Works

**Quick test** (see if checkpoints actually change):

1. Add "Simple Checkpoint Rotation"
   - subfolder: `"Illustrious"`
   - change_every: `1` (change EVERY image)

2. Queue prompt
3. Look at console - it shows which checkpoint loaded
4. Queue prompt again
5. Look at console - should show DIFFERENT checkpoint

If checkpoint changes → ✅ Working!
If checkpoint stays same → ❌ Something wrong

## What the Other Nodes Are For

You saw multiple nodes because the original implementation was over-engineered:

- **Simple Checkpoint Rotation**: USE THIS. Has built-in counter. Simple.
- **Checkpoint Rotation Loader (Advanced)**: Complex, requires separate counter node. Ignore.
- **Batch Index Counter**: Helper for advanced node. Ignore.
- **Simple Counter**: Helper for advanced node. Ignore.

Just use **"Simple Checkpoint Rotation"** and forget the rest exist.

## Common Issues

### "Same image over and over"
- ✅ Checkpoints ARE rotating (check console)
- ❌ You set fixed seed = same composition, different style
- **Fix**: Use randomize/increment seed

### "Checkpoint not changing"
- ❌ You're using batch_size > 1 in one queue
- ❌ You're not queuing multiple times
- **Fix**: Queue 20 separate times, batch_size = 1

### "Too slow - clicking 20 times"
- Use Option 2 or 3 above
- Or get a loop node extension (search ComfyUI Manager for "loop" or "iteration")
- Or use ComfyUI API with a script

## Can This Be Fully Automatic?

**Short answer**: Not without extra extensions.

**Long answer**: You need either:
1. A loop/iteration node extension (like ComfyUI-Impact-Pack)
2. ComfyUI API + Python script to queue programmatically
3. My node + manual queuing (simplest, but most clicking)

ComfyUI itself doesn't have built-in "generate N images with this workflow" button that works with dynamic checkpoint loading.

## Bottom Line

**This node works**, but ComfyUI's architecture requires you to queue the prompt multiple times for checkpoint rotation. It's not fully automatic "set and forget" - you need to manually queue or use external tools.

If this doesn't meet your needs, you might want:
- A batch processing script outside ComfyUI
- A different tool that supports mid-batch model switching
- Loop node extensions that can iterate workflows

But for manual checkpoint rotation, this is as simple as it gets: 2 settings, queue multiple times.

---

**Is this frustrating?** Yes.
**Is it possible?** Yes, with manual queuing.
**Can it be automatic?** Only with loop extensions or API scripting.
