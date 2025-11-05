"""
Simplified checkpoint rotation node with built-in counter.
"""

import os
import sys
from typing import Dict, Tuple, Optional, Any

# Use relative imports to avoid conflicts with ComfyUI's built-in modules
try:
    from ..utils.path_utils import PathUtils
    from ..utils.checkpoint_utils import CheckpointUtils
except ImportError:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from utils.path_utils import PathUtils
    from utils.checkpoint_utils import CheckpointUtils


class SimpleCheckpointRotation:
    """
    Simplified checkpoint rotation with built-in counter.
    Just set folder and interval - that's it.
    """

    # Class variable to track state across executions
    _counter = 0
    _checkpoint_cache = {}

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """Define input parameters."""
        return {
            "required": {
                "subfolder": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Checkpoint subfolder (leave empty for all checkpoints)"
                }),
                "change_every": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 1000,
                    "tooltip": "Change checkpoint every N images"
                }),
                "auto_increment": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Automatically increment counter (turn OFF for manual control)"
                }),
            },
            "optional": {
                "manual_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100000,
                    "tooltip": "Manual index (only used if auto_increment is OFF)"
                }),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "info")

    FUNCTION = "load_checkpoint"

    CATEGORY = "loaders"

    OUTPUT_NODE = False

    def load_checkpoint(
        self,
        subfolder: str,
        change_every: int,
        auto_increment: bool = True,
        manual_index: int = 0
    ) -> Tuple:
        """Load checkpoint with rotation."""
        try:
            # Determine current index
            if auto_increment:
                current_index = self._counter
                self._counter += 1
            else:
                current_index = manual_index

            # Get base checkpoints directory
            base_path = PathUtils.get_checkpoints_base_path()

            # Validate and get full path to subfolder
            is_valid, result = PathUtils.validate_subfolder(base_path, subfolder)
            if not is_valid:
                error_msg = f"Subfolder error: {result}"
                print(f"[SimpleCheckpointRotation] {error_msg}")
                return self._return_error(error_msg)

            checkpoint_folder = result

            # Discover checkpoints (with caching)
            cache_key = subfolder if subfolder else "root"
            if cache_key not in self._checkpoint_cache:
                checkpoints = CheckpointUtils.scan_checkpoint_folder(checkpoint_folder, recursive=True)
                if not checkpoints:
                    error_msg = f"No checkpoints found in: {subfolder or 'root folder'}"
                    print(f"[SimpleCheckpointRotation] {error_msg}")
                    return self._return_error(error_msg)
                self._checkpoint_cache[cache_key] = checkpoints
            else:
                checkpoints = self._checkpoint_cache[cache_key]

            # Select checkpoint based on rotation logic
            checkpoint_rotation_index = (current_index // change_every) % len(checkpoints)
            selected_checkpoint = checkpoints[checkpoint_rotation_index]

            # Get checkpoint name for ComfyUI
            checkpoint_name = CheckpointUtils.get_checkpoint_name_for_comfyui(
                selected_checkpoint,
                base_path
            )

            # Load the checkpoint
            model, clip, vae = self._load_checkpoint(checkpoint_name)

            # Generate info
            checkpoint_num = checkpoint_rotation_index + 1
            total_checkpoints = len(checkpoints)
            info = (
                f"Image #{current_index}\n"
                f"Checkpoint {checkpoint_num}/{total_checkpoints}: {os.path.basename(selected_checkpoint)}\n"
                f"Changes every {change_every} images\n"
                f"Mode: {'Auto' if auto_increment else 'Manual'}"
            )

            print(f"[SimpleCheckpointRotation] Image #{current_index} - Using checkpoint {checkpoint_num}/{total_checkpoints}: {os.path.basename(selected_checkpoint)}")

            return (model, clip, vae, info)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[SimpleCheckpointRotation] {error_msg}")
            import traceback
            traceback.print_exc()
            return self._return_error(error_msg)

    def _load_checkpoint(self, checkpoint_name: str) -> Tuple:
        """Load a checkpoint using ComfyUI's checkpoint loader."""
        try:
            import comfy.sd
            import folder_paths

            checkpoint_path = folder_paths.get_full_path("checkpoints", checkpoint_name)
            out = comfy.sd.load_checkpoint_guess_config(
                checkpoint_path,
                output_vae=True,
                output_clip=True,
                embedding_directory=folder_paths.get_folder_paths("embeddings")
            )
            return (out[0], out[1], out[2])

        except Exception as e:
            raise Exception(f"Failed to load checkpoint '{checkpoint_name}': {e}")

    def _return_error(self, error_message: str) -> Tuple:
        """Return error state."""
        return (None, None, None, f"ERROR: {error_message}")

    @classmethod
    def reset_counter(cls):
        """Reset the counter to 0."""
        cls._counter = 0
        print("[SimpleCheckpointRotation] Counter reset to 0")

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Force re-execution every time."""
        # Return counter value so node always re-executes
        return float(cls._counter)
