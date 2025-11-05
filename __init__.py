"""
ComfyUI Checkpoint Rotation Node

A custom node for ComfyUI that enables automatic checkpoint rotation during batch generation.
Allows users to switch between different model checkpoints based on generation count.

Author: Claude AI Assistant
Version: 1.0.0
"""

import os
import sys
import traceback

# Version info
__version__ = "1.0.0"
__author__ = "Claude AI Assistant"

# Add this directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Initialize empty mappings in case of import failure
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = "./web"

try:
    # Import node classes using relative imports to avoid conflict with ComfyUI's 'nodes' module
    from .nodes.checkpoint_rotation import CheckpointRotationNode
    from .nodes.batch_counter import BatchIndexCounter, SimpleCounter
    from .nodes.simple_rotation import SimpleCheckpointRotation
    from .nodes.rotation_with_counter import CheckpointRotationWithCounter
    from .nodes.simple_rotation_direct import CheckpointRotationSimple

    # Node class mappings for ComfyUI
    NODE_CLASS_MAPPINGS = {
        "CheckpointRotationSimple": CheckpointRotationSimple,  # ⭐ TRY THIS IF BATCH NOT WORKING
        "CheckpointRotationWithCounter": CheckpointRotationWithCounter,
        "SimpleCheckpointRotation": SimpleCheckpointRotation,
        "CheckpointRotation": CheckpointRotationNode,
        "BatchIndexCounter": BatchIndexCounter,
        "SimpleCounter": SimpleCounter,
    }

    # Display names for nodes in ComfyUI interface
    NODE_DISPLAY_NAME_MAPPINGS = {
        "CheckpointRotationSimple": "Checkpoint Rotation (Debug)",  # ⭐ DEBUG VERSION
        "CheckpointRotationWithCounter": "Checkpoint Rotation (Batch)",
        "SimpleCheckpointRotation": "Simple Checkpoint Rotation",
        "CheckpointRotation": "Checkpoint Rotation Loader (Advanced)",
        "BatchIndexCounter": "Batch Index Counter",
        "SimpleCounter": "Simple Counter",
    }

    # Print success message
    print("\033[92m[ComfyUI] Checkpoint Rotation Node loaded successfully!\033[0m")
    print(f"  ⭐ Checkpoint Rotation (Debug) - Try this if batch version not working")
    print(f"  - Checkpoint Rotation (Batch)")
    print(f"  - Simple Checkpoint Rotation")
    print(f"  Version: {__version__}")

except Exception as e:
    print("\033[91m[ComfyUI] ERROR: Failed to load Checkpoint Rotation Node!\033[0m")
    print(f"  Error: {str(e)}")
    print(f"  Location: {current_dir}")
    print("\033[91m  Full traceback:\033[0m")
    traceback.print_exc()
    print("\033[93m  Please report this error with the traceback above.\033[0m")

# Export for ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
