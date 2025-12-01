# Investigation: Image Saver Metadata Not Receiving Checkpoint Name

## Problem Statement
When connecting `checkpoint_name` output from Checkpoint Rotation Loader to `modelname` input of Image Saver Metadata node, the checkpoint name is not being populated correctly in the image metadata.

## Current State

### What Our Node Outputs (checkpoint_rotation.py:169)
```python
# Get basename for output (for metadata and display compatibility)
checkpoint_name = os.path.basename(selected_checkpoint)
```

Currently outputting: Just the filename, e.g., `model.safetensors`

### Previous State (before my fix)
```python
checkpoint_name = CheckpointUtils.get_checkpoint_name_for_comfyui(
    selected_checkpoint,
    base_path
)
```

Was outputting: Relative path with forward slashes, e.g., `subfolder/model.safetensors`

## How Image Saver Metadata Processes modelname

### Entry Point (nodes.py:131-149)
```python
def get_metadata(
    self,
    modelname: str = "",  # <-- Our checkpoint_name connects here
    ...
) -> tuple[Metadata, str, str]:
    metadata = ImageSaverMetadata.make_metadata(modelname, ...)
    return (metadata, metadata.final_hashes, metadata.a111_params)
```

### Processing Flow (nodes.py:154-161)

1. **Multiple model handling** (line 155):
```python
modelname, additional_hashes = ImageSaver.get_multiple_models(modelname, additional_hashes)
```

2. **Get checkpoint path** (line 157):
```python
ckpt_path = full_checkpoint_path_for(modelname)
```
This is the CRITICAL function - it needs to FIND the checkpoint file.

3. **Calculate hash** (line 158-161):
```python
if ckpt_path:
    modelhash = get_sha256(ckpt_path)[:10]
else:
    modelhash = ""
```

### The Critical Function: full_checkpoint_path_for (utils.py:76-91)

```python
def full_checkpoint_path_for(model_name: str) -> str:
    if not model_name:
        return ''

    supported_extensions = set(folder_paths.supported_pt_extensions) | {".gguf"}

    # Try to find in checkpoints folder
    matching_checkpoint = get_file_path_match("checkpoints", model_name, supported_extensions)
    if matching_checkpoint is not None:
        return folder_paths.get_full_path("checkpoints", matching_checkpoint)

    # Try to find in diffusion_models folder
    matching_model = get_file_path_match("diffusion_models", model_name, supported_extensions)
    if matching_model:
        return folder_paths.get_full_path("diffusion_models", matching_model)

    print(f'Could not find full path to checkpoint "{model_name}"')
    return ''
```

### The Matching Logic: get_file_path_match (utils.py:117-131)

This function tries to match the provided name to actual files in the folder:

```python
def get_file_path_match(folder_name: str, file_name: str, supported_extensions: Optional[Collection[str]] = None) -> Optional[str]:
    supported_extensions_fallback = supported_extensions if supported_extensions is not None else folder_paths.supported_pt_extensions
    file_path = Path(file_name)

    # If filename doesn't have extension
    if file_path.suffix.lower() not in supported_extensions_fallback:
        # Try to match without extension
        matching_file_path = next((p for p in get_file_path_iterator(folder_name, supported_extensions) if p.with_suffix('') == file_path), None)
        # Fallback: try to match stem
        matching_file_path = (matching_file_path if matching_file_path is not None else
            next((p for p in get_file_path_iterator(folder_name, supported_extensions) if p.stem == file_path.name), None))
    else:
        # If filename has extension, try exact match
        matching_file_path = next((p for p in get_file_path_iterator(folder_name, supported_extensions) if p == file_path), None)
        # Fallback: try to match name
        matching_file_path = (matching_file_path if matching_file_path is not None else
            next((p for p in get_file_path_iterator(folder_name, supported_extensions) if p.name == file_path.name), None))

    return str(matching_file_path) if matching_file_path is not None else None
```

## Questions to Answer

1. **What format does `full_checkpoint_path_for` expect?**
   - Just filename? (e.g., `model.safetensors`)
   - Relative path? (e.g., `subfolder/model.safetensors`)
   - Does it matter if extension is included?

2. **What does get_file_path_iterator return?**
   - It uses `folder_paths.get_filename_list("checkpoints")`
   - Need to check what format ComfyUI stores these in

3. **Test Cases:**
   - Checkpoint in root: `model.safetensors`
   - Checkpoint in subfolder: `subfolder/model.safetensors`
   - Does it work with or without extension?

4. **Why might it be failing?**
   - Path separator issue? (Windows `\` vs `/`)
   - Extension issue? (with vs without `.safetensors`)
   - Path matching logic can't find the file?

## Hypothesis

**Theory 1:** The basename-only approach fails for checkpoints in subfolders
- We're sending: `model.safetensors`
- But if there are multiple models with the same name in different folders, it might pick the wrong one or fail to find it

**Theory 2:** The relative path approach works but there's a path separator issue
- We're sending: `subfolder/model.safetensors` (forward slash)
- Windows might need: `subfolder\model.safetensors` (backslash)
- But utils.py:119 uses `Path(file_name)` which should normalize this

**Theory 3:** Extension handling
- Maybe it expects name WITHOUT extension?
- Line 122-123: checks if suffix is in supported extensions
- If yes, does exact path match
- If no, tries to match without extension

## Gemini's Analysis Results

### Key Findings from Gemini (gemini-2.5-pro)

**CORRECT FORMAT:** Relative path with extension and forward slashes
Example: `subfolder/model.safetensors`

### Detailed Analysis of Matching Logic

**Case 1: Basename Only (`model.safetensors`)**
1. Enters `else` block (has valid extension)
2. First check: `p == file_path` - FAILS for subfolders
3. Second check: `p.name == file_path.name` - MATCHES but is AMBIGUOUS
4. **Problem:** If multiple files share the same name in different folders (e.g., `sd15/model.safetensors` and `sdxl/model.safetensors`), it returns whichever the iterator finds first - potentially the WRONG model!

**Case 2: Relative Path (`subfolder/model.safetensors`)**
1. Enters `else` block (has valid extension)
2. First check: `p == file_path` - DIRECT MATCH ✅
3. Unambiguous and precise

### Answers to Questions

1. **Format:** Use relative path from checkpoints directory with forward slashes
2. **Basename in subfolders:** Works but is ambiguous and dangerous
3. **Extension:** YES, include it for specificity
4. **Path separators:** Forward slashes work on all OS thanks to pathlib.Path

## The Real Issue

**MY FIX WAS WRONG!** I switched from relative path to basename, which made things worse.

The correct approach was already there in the original code:
```python
checkpoint_name = CheckpointUtils.get_checkpoint_name_for_comfyui(
    selected_checkpoint,
    base_path
)
```

This function (utils/checkpoint_utils.py:172-191) already returns the relative path with forward slashes!

```python
def get_checkpoint_name_for_comfyui(checkpoint_path: str, base_path: str) -> str:
    try:
        # Get relative path from base checkpoints directory
        rel_path = os.path.relpath(checkpoint_path, base_path)
        # Normalize to forward slashes for ComfyUI compatibility (works on all platforms)
        rel_path = rel_path.replace(os.sep, '/')
        return rel_path
    except ValueError:
        # If relative path fails, just return basename
        return os.path.basename(checkpoint_path)
```

## Root Cause Hypothesis

If the original code was correct, why wasn't it working? Possible reasons:

1. **User didn't reload ComfyUI** after an earlier change
2. **The checkpoint_name was correct but something else is wrong** - need to verify actual output
3. **The base_path being passed is incorrect** - need to check what PathUtils.get_checkpoints_base_path() returns
4. **There's a different issue entirely** - maybe the metadata isn't being written to the image for another reason

## Solution Implemented

### Changes Made (checkpoint_rotation.py)

1. **REVERTED incorrect basename fix**
   - Removed: `checkpoint_name = os.path.basename(selected_checkpoint)`
   - Restored: `checkpoint_name = CheckpointUtils.get_checkpoint_name_for_comfyui(...)`

2. **Added debug logging**
   - Now prints: `[CheckpointRotation] Output checkpoint_name for metadata: 'subfolder/model.safetensors'`
   - This helps verify the exact value being passed to Image Saver Metadata

### Expected Behavior

The node now outputs checkpoint_name in the correct format:
- **Root checkpoint:** `model.safetensors`
- **Subfolder checkpoint:** `subfolder/model.safetensors`
- **Nested subfolder:** `folder1/folder2/model.safetensors`

This format is:
- ✅ Unambiguous (no collision with same-named files in different folders)
- ✅ Compatible with Image Saver Metadata's `full_checkpoint_path_for` function
- ✅ Cross-platform (forward slashes work on Windows via pathlib)
- ✅ Includes extension for specificity

### Verification Steps for User

1. **Restart ComfyUI** (required for code changes to take effect)
2. **Run your workflow** and check the console output
3. **Look for this log line:**
   ```
   [CheckpointRotation] Output checkpoint_name for metadata: 'your_checkpoint.safetensors'
   ```
4. **Verify the image metadata** contains the model name
5. **If still not working,** provide the console output for further debugging
