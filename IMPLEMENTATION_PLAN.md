# ComfyUI Checkpoint Rotation Node - Implementation Plan

## Overview

This document outlines the detailed implementation plan for a custom ComfyUI node that enables automatic checkpoint rotation during batch image generation. The node will allow users to specify how many images should be generated before switching to a different checkpoint from a selected subfolder.

### Use Case Example
- **Batch Count**: 20 images
- **Change Interval**: 4 images
- **Result**: The workflow will use 5 different checkpoints (changing every 4 images)

---

## Feature Requirements

### Core Functionality
1. **Checkpoint Folder Selection**: Allow users to select a subfolder within the ComfyUI models directory
2. **Interval Configuration**: User-defined number specifying when to change checkpoints
3. **Automatic Rotation**: Rotate through available checkpoints in the selected folder
4. **Batch Processing**: Handle batch operations correctly with checkpoint switching

### User Interface Requirements
- Dropdown/input for subfolder selection
- Numeric input for image count before checkpoint change
- Display current checkpoint being used (optional but helpful)
- Seed handling for reproducibility

---

## Technical Architecture

### ComfyUI Node Structure

A custom ComfyUI node consists of:
1. **Node Class**: Main class defining inputs, outputs, and execution logic
2. **Node Mappings**: Registration with ComfyUI's node system
3. **Category**: Organization within ComfyUI's node menu

### Key Components

#### 1. Node Class: `CheckpointRotationNode`

**Inputs:**
- `subfolder` (STRING): Path to checkpoint subfolder relative to models/checkpoints/
- `change_interval` (INT): Number of images to generate before changing checkpoint
- `current_batch_index` (INT): Current position in batch (for tracking)
- `seed` (INT): Seed for randomization (optional for random vs sequential rotation)
- `rotation_mode` (COMBO): ["sequential", "random"] - How to select next checkpoint

**Outputs:**
- `checkpoint_name` (STRING): Name of the checkpoint to use
- `checkpoint_path` (STRING): Full path to the checkpoint file
- `model` (MODEL): Loaded checkpoint model
- `vae` (VAE): VAE from checkpoint
- `clip` (CLIP): CLIP from checkpoint

**Internal State:**
- Track which checkpoint is currently active
- Maintain list of available checkpoints
- Keep rotation counter

#### 2. Helper Functions

**Checkpoint Discovery:**
```python
def get_checkpoints_from_subfolder(subfolder):
    """
    Scan the specified subfolder for checkpoint files
    Returns list of checkpoint files (.safetensors, .ckpt, .pt)
    """
```

**Checkpoint Selection:**
```python
def select_checkpoint(checkpoint_list, batch_index, interval, mode):
    """
    Determine which checkpoint to use based on:
    - Current batch index
    - Change interval
    - Rotation mode (sequential/random)
    """
```

**Checkpoint Loading:**
```python
def load_checkpoint(checkpoint_path):
    """
    Load the specified checkpoint and return model, vae, clip
    Uses ComfyUI's existing checkpoint loader infrastructure
    """
```

---

## Implementation Plan

### Phase 1: Project Setup and Structure

**Step 1.1: Create Project Structure**
```
comfyui-change-checkpoint-randomly/
├── __init__.py              # Node registration
├── nodes/
│   ├── __init__.py
│   └── checkpoint_rotation.py   # Main node implementation
├── utils/
│   ├── __init__.py
│   ├── checkpoint_utils.py      # Checkpoint discovery and loading
│   └── path_utils.py            # Path handling utilities
├── README.md                # User documentation
├── LICENSE
├── requirements.txt         # Dependencies (if any)
└── examples/
    └── example_workflow.json    # Example ComfyUI workflow
```

**Step 1.2: Initialize Python Package**
- Create `__init__.py` files for proper Python package structure
- Set up node registration with ComfyUI's `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`

---

### Phase 2: Utility Functions Implementation

**Step 2.1: Path Utilities (`utils/path_utils.py`)**
```python
class PathUtils:
    @staticmethod
    def get_checkpoints_base_path():
        """Get the base ComfyUI checkpoints directory"""
        # Use ComfyUI's folder_paths module

    @staticmethod
    def list_subfolders(base_path):
        """List all subfolders in checkpoints directory"""

    @staticmethod
    def validate_subfolder(subfolder):
        """Ensure subfolder exists and is valid"""
```

**Step 2.2: Checkpoint Utilities (`utils/checkpoint_utils.py`)**
```python
class CheckpointUtils:
    SUPPORTED_EXTENSIONS = ['.safetensors', '.ckpt', '.pt', '.pth']

    @staticmethod
    def scan_checkpoint_folder(folder_path):
        """
        Recursively scan folder for checkpoint files
        Returns: List of checkpoint file paths
        """

    @staticmethod
    def filter_checkpoints(checkpoint_list, pattern=None):
        """Filter checkpoints by name pattern if needed"""

    @staticmethod
    def get_checkpoint_info(checkpoint_path):
        """Get metadata about checkpoint (size, modified date, etc.)"""
```

---

### Phase 3: Core Node Implementation

**Step 3.1: Base Node Class (`nodes/checkpoint_rotation.py`)**

```python
import folder_paths
from nodes import CheckpointLoaderSimple

class CheckpointRotationNode:
    """
    A custom node that rotates through checkpoints in a subfolder
    based on batch generation count.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "subfolder": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "change_interval": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000,
                    "step": 1
                }),
                "batch_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 10000,
                    "step": 1
                }),
                "rotation_mode": (["sequential", "random", "shuffle"],),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff
                }),
            },
            "optional": {
                "checkpoint_filter": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "checkpoint_name")

    FUNCTION = "load_checkpoint_rotated"
    CATEGORY = "loaders/checkpoint"

    def __init__(self):
        self.checkpoint_cache = {}
        self.checkpoint_list = []
        self.current_checkpoint = None

    def load_checkpoint_rotated(self, subfolder, change_interval,
                                 batch_index, rotation_mode, seed,
                                 checkpoint_filter=""):
        """
        Main execution function
        1. Scan subfolder for checkpoints
        2. Determine which checkpoint to use based on batch_index
        3. Load and return the checkpoint
        """
        pass  # Implementation here
```

**Step 3.2: Checkpoint Discovery Logic**

```python
def discover_checkpoints(self, subfolder, checkpoint_filter):
    """
    Discover all checkpoints in the specified subfolder
    Cache the results to avoid repeated file system scans
    """
    cache_key = f"{subfolder}:{checkpoint_filter}"

    if cache_key in self.checkpoint_cache:
        return self.checkpoint_cache[cache_key]

    # Scan folder
    # Filter by pattern if provided
    # Cache results
    # Return list
```

**Step 3.3: Checkpoint Selection Logic**

```python
def select_checkpoint_by_index(self, checkpoint_list, batch_index,
                                interval, mode, seed):
    """
    Determine which checkpoint to use based on:
    - batch_index: Current position in generation sequence
    - interval: How many images before changing
    - mode: sequential, random, or shuffle
    - seed: For reproducible random selection
    """

    # Calculate checkpoint index
    checkpoint_rotation_index = (batch_index // interval) % len(checkpoint_list)

    if mode == "sequential":
        selected_checkpoint = checkpoint_list[checkpoint_rotation_index]

    elif mode == "random":
        # Use seed + rotation_index for reproducible randomness
        import random
        random.seed(seed + checkpoint_rotation_index)
        selected_checkpoint = random.choice(checkpoint_list)

    elif mode == "shuffle":
        # Shuffle list once, then iterate sequentially
        import random
        random.seed(seed)
        shuffled_list = checkpoint_list.copy()
        random.shuffle(shuffled_list)
        selected_checkpoint = shuffled_list[checkpoint_rotation_index]

    return selected_checkpoint
```

**Step 3.4: Checkpoint Loading Integration**

```python
def load_checkpoint_model(self, checkpoint_path):
    """
    Use ComfyUI's existing checkpoint loading infrastructure
    """
    # Import ComfyUI's checkpoint loader
    # Load the model, clip, vae
    # Return loaded components
```

---

### Phase 4: Advanced Features

**Step 4.1: Batch Index Automation**

Create a helper node that automatically increments batch_index:

```python
class BatchIndexCounter:
    """
    Automatically tracks and increments batch index
    Can be reset or set to specific value
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "reset": ("BOOLEAN", {"default": False}),
                "increment": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "initial_value": ("INT", {"default": 0}),
            }
        }
```

**Step 4.2: Checkpoint Preview Node**

```python
class CheckpointListPreview:
    """
    Preview which checkpoints will be used in rotation
    Useful for debugging and planning
    """

    def preview_rotation_sequence(self, subfolder, total_images,
                                   interval, mode, seed):
        """
        Returns a list showing which checkpoint will be used
        for each batch of images
        """
```

---

### Phase 5: Integration with ComfyUI

**Step 5.1: Node Registration (`__init__.py`)**

```python
from .nodes.checkpoint_rotation import CheckpointRotationNode
from .nodes.batch_counter import BatchIndexCounter
from .nodes.preview import CheckpointListPreview

NODE_CLASS_MAPPINGS = {
    "CheckpointRotation": CheckpointRotationNode,
    "BatchIndexCounter": BatchIndexCounter,
    "CheckpointListPreview": CheckpointListPreview,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CheckpointRotation": "Checkpoint Rotation Loader",
    "BatchIndexCounter": "Batch Index Counter",
    "CheckpointListPreview": "Checkpoint Rotation Preview",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
```

**Step 5.2: ComfyUI Integration Points**

1. **folder_paths**: Use ComfyUI's `folder_paths` module to get checkpoint directories
2. **CheckpointLoaderSimple**: Extend or utilize existing checkpoint loading
3. **Execution Model**: Ensure compatibility with ComfyUI's execution graph

---

## Workflow Integration

### Example Workflow Structure

```
[BatchIndexCounter]
    ↓ (batch_index)
[CheckpointRotation]
    ↓ (model, clip, vae)
[KSampler] (batch_size: 20)
    ↓
[VAEDecode]
    ↓
[SaveImage]
```

### Batch Processing Considerations

**Challenge**: ComfyUI's KSampler generates all images in a batch using the same checkpoint.

**Solution Options:**

1. **Loop-based Approach** (Recommended):
   - Use a loop/iteration node (if available in ComfyUI)
   - Generate images in smaller batches matching the interval
   - Increment batch_index between iterations

2. **Queue-based Approach**:
   - Generate workflow JSON programmatically
   - Queue multiple prompts with different batch_index values
   - Each prompt uses appropriate checkpoint

3. **Custom Sampler Node** (Advanced):
   - Create a custom sampler that can change models mid-batch
   - More complex but provides seamless integration

---

## Edge Cases and Error Handling

### Edge Cases to Handle

1. **Empty Subfolder**:
   - Error: No checkpoints found in subfolder
   - Action: Display clear error message, list available subfolders

2. **Invalid Subfolder Path**:
   - Error: Subfolder doesn't exist
   - Action: Validate path, suggest corrections

3. **Single Checkpoint**:
   - Scenario: Only one checkpoint in folder
   - Action: Use that checkpoint for all generations (no rotation needed)

4. **Interval Larger Than Batch**:
   - Scenario: change_interval=100, batch_size=20
   - Action: Same checkpoint used for entire batch (working as expected)

5. **Checkpoint Load Failure**:
   - Error: Corrupted or incompatible checkpoint
   - Action: Skip to next checkpoint, log error

6. **File System Changes**:
   - Scenario: Checkpoints added/removed during execution
   - Action: Cache invalidation strategy needed

### Error Handling Strategy

```python
class CheckpointRotationError(Exception):
    """Base exception for checkpoint rotation errors"""
    pass

class NoCheckpointsFoundError(CheckpointRotationError):
    """Raised when no checkpoints found in subfolder"""
    pass

class InvalidSubfolderError(CheckpointRotationError):
    """Raised when subfolder path is invalid"""
    pass
```

---

## Testing Strategy

### Unit Tests

**Test Suite 1: Path Utilities**
- Test checkpoint directory discovery
- Test subfolder validation
- Test path construction

**Test Suite 2: Checkpoint Discovery**
- Test scanning with various file extensions
- Test filtering by pattern
- Test empty folders
- Test nested subfolders

**Test Suite 3: Selection Logic**
- Test sequential rotation
- Test random rotation with seed
- Test shuffle rotation
- Test boundary conditions (index 0, max)

**Test Suite 4: Integration**
- Test full node execution
- Test caching behavior
- Test error handling

### Manual Testing Scenarios

1. **Basic Rotation**:
   - 20 images, change every 4
   - Verify 5 different checkpoints used

2. **Sequential Mode**:
   - Verify deterministic order
   - Same order on repeated runs

3. **Random Mode**:
   - Verify same seed produces same sequence
   - Different seeds produce different sequences

4. **Edge Cases**:
   - Test with 1 checkpoint
   - Test with 100+ checkpoints
   - Test with very large batch sizes

---

## Performance Considerations

### Optimization Strategies

1. **Caching**:
   - Cache checkpoint file lists (invalidate periodically)
   - Cache loaded models if memory permits
   - Cache validation results

2. **Lazy Loading**:
   - Only load checkpoint when needed
   - Unload previous checkpoint to free memory

3. **Parallel Processing**:
   - If multiple checkpoints needed simultaneously
   - Load next checkpoint while generating current batch

4. **File System**:
   - Minimize directory scans
   - Use efficient file listing methods
   - Consider implementing file watcher for changes

---

## Documentation Requirements

### User Documentation (README.md)

1. **Installation Instructions**:
   - How to install the custom node
   - ComfyUI version requirements
   - Dependencies

2. **Usage Guide**:
   - Step-by-step setup
   - Parameter explanations
   - Example workflows

3. **Troubleshooting**:
   - Common issues and solutions
   - FAQ

4. **Advanced Usage**:
   - Combining with other nodes
   - Scripting and automation

### Developer Documentation

1. **Code Comments**: Inline documentation for complex logic
2. **API Documentation**: Document all public methods
3. **Architecture Diagram**: Visual representation of node flow

---

## Implementation Timeline

### Phase 1: Foundation (Days 1-2)
- Set up project structure
- Implement utility functions
- Create basic node skeleton

### Phase 2: Core Functionality (Days 3-4)
- Implement checkpoint discovery
- Implement selection logic
- Integrate with ComfyUI checkpoint loading

### Phase 3: Testing (Day 5)
- Unit tests
- Integration tests
- Manual testing with real workflows

### Phase 4: Polish (Day 6)
- Error handling
- Edge case coverage
- Performance optimization

### Phase 5: Documentation (Day 7)
- User documentation
- Example workflows
- Code cleanup and comments

---

## Future Enhancements

### Version 2.0 Features

1. **Weighted Rotation**:
   - Allow users to specify probability weights for each checkpoint
   - Some checkpoints used more frequently than others

2. **Conditional Rotation**:
   - Change checkpoint based on generation quality metrics
   - Skip checkpoints that produce poor results

3. **Multi-Folder Support**:
   - Rotate through checkpoints from multiple subfolders
   - Mix and match from different categories

4. **Checkpoint Metadata**:
   - Display checkpoint info (model type, training data, etc.)
   - Filter by metadata tags

5. **History Tracking**:
   - Keep log of which checkpoint generated which image
   - Save rotation history for reproducibility

6. **UI Enhancements**:
   - Visual checkpoint selector
   - Thumbnail previews
   - Drag-and-drop ordering

---

## Technical Dependencies

### Required ComfyUI Modules
- `folder_paths`: For checkpoint directory management
- `nodes.CheckpointLoaderSimple`: For checkpoint loading
- `comfy.sd`: For model loading

### Python Standard Library
- `os`, `pathlib`: File system operations
- `random`: Random selection
- `json`: Configuration and caching
- `typing`: Type hints

### Optional Dependencies
- `watchdog`: File system monitoring
- `pillow`: Checkpoint preview generation

---

## Security Considerations

1. **Path Traversal**: Validate subfolder paths to prevent directory traversal attacks
2. **File Type Validation**: Only allow whitelisted checkpoint file extensions
3. **Resource Limits**: Prevent loading excessively large files
4. **Sandbox Execution**: Ensure node runs with appropriate permissions

---

## Conclusion

This implementation plan provides a comprehensive roadmap for creating a checkpoint rotation node for ComfyUI. The modular design allows for incremental development and testing, while the planned features ensure practical usability.

### Key Success Criteria

1. ✅ Users can select checkpoint subfolders easily
2. ✅ Rotation happens automatically based on batch index
3. ✅ Multiple rotation modes available (sequential, random, shuffle)
4. ✅ Reproducible results with seed control
5. ✅ Robust error handling
6. ✅ Clear documentation and examples
7. ✅ Good performance with large checkpoint collections

### Next Steps

1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Iterate based on testing feedback

---

**Document Version**: 1.0
**Last Updated**: 2025-11-05
**Author**: Claude AI Assistant
