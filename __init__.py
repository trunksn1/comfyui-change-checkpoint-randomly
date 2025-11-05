"""
ComfyUI Checkpoint Rotation Node

A custom node for ComfyUI that enables automatic checkpoint rotation during batch generation.
Allows users to switch between different model checkpoints based on generation count.

Author: Claude AI Assistant
Version: 1.0.0
"""

import os
import sys

# Add this directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import node classes
from nodes.checkpoint_rotation import CheckpointRotationNode
from nodes.batch_counter import BatchIndexCounter, SimpleCounter

# Web directory for custom UI (if needed in future)
WEB_DIRECTORY = "./web"

# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "CheckpointRotation": CheckpointRotationNode,
    "BatchIndexCounter": BatchIndexCounter,
    "SimpleCounter": SimpleCounter,
}

# Display names for nodes in ComfyUI interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "CheckpointRotation": "Checkpoint Rotation Loader",
    "BatchIndexCounter": "Batch Index Counter",
    "SimpleCounter": "Simple Counter",
}

# Export for ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

# Version info
__version__ = "1.0.0"
__author__ = "Claude AI Assistant"

# Print initialization message
print("\033[92m[ComfyUI] Checkpoint Rotation Node loaded successfully!\033[0m")
print(f"  - Checkpoint Rotation Loader")
print(f"  - Batch Index Counter")
print(f"  - Simple Counter")
print(f"  Version: {__version__}")
