"""
Alternative checkpoint rotation using direct checkpoint index control.
This should work more reliably with control_after_generate.
"""

import os
import sys
from typing import Dict, Tuple, Optional, Any, List

# Use relative imports
try:
    from ..utils.path_utils import PathUtils
    from ..utils.checkpoint_utils import CheckpointUtils
except ImportError:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from utils.path_utils import PathUtils
    from utils.checkpoint_utils import CheckpointUtils


class CheckpointRotationSimple:
    """
    Simplified checkpoint rotation that takes a direct checkpoint index.

    Setup:
    1. Add this node
    2. Set subfolder
    3. Add a Primitive INT for checkpoint_index
    4. Double-click LEFT side of primitive
    5. Set control_after_generate to "increment"
    6. Connect primitive to checkpoint_index input

    This forces the checkpoint to change based on the index value.
    For "change every N images", use increment step = 1 and this formula:
    actual_checkpoint = (index // N) % num_checkpoints
    """

    def __init__(self):
        self.checkpoint_cache = {}
        self.checkpoint_list_cache = {}

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """Define input parameters."""
        return {
            "required": {
                "checkpoint_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100000,
                    "step": 1,
                    "tooltip": "Connect Primitive INT with control_after_generate: increment"
                }),
                "subfolder": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Checkpoint subfolder (leave empty for root)"
                }),
                "change_every": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 1000,
                    "step": 1,
                    "tooltip": "Change checkpoint every N images"
                }),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "checkpoint_name", "debug_info")

    FUNCTION = "load_checkpoint"

    CATEGORY = "loaders"

    def load_checkpoint(
        self,
        checkpoint_index: int,
        subfolder: str,
        change_every: int
    ) -> Tuple:
        """Load checkpoint based on index."""

        # Debug output to see if node is executing
        print(f"\n[CheckpointRotation] >>> NODE EXECUTING with index={checkpoint_index}")

        try:
            # Get base path
            base_path = PathUtils.get_checkpoints_base_path()

            # Validate subfolder
            is_valid, result = PathUtils.validate_subfolder(base_path, subfolder)
            if not is_valid:
                error_msg = f"Subfolder error: {result}"
                print(f"[CheckpointRotation] {error_msg}")
                return self._return_error(error_msg)

            checkpoint_folder = result

            # Get checkpoint list
            cache_key = subfolder if subfolder else "root"
            if cache_key not in self.checkpoint_list_cache:
                checkpoints = CheckpointUtils.scan_checkpoint_folder(checkpoint_folder, recursive=True)
                if not checkpoints:
                    error_msg = f"No checkpoints found in: {subfolder or 'root folder'}"
                    print(f"[CheckpointRotation] {error_msg}")
                    return self._return_error(error_msg)
                self.checkpoint_list_cache[cache_key] = checkpoints
                print(f"[CheckpointRotation] Found {len(checkpoints)} checkpoints in {subfolder or 'root'}")

            checkpoints = self.checkpoint_list_cache[cache_key]

            # Calculate which checkpoint based on formula
            actual_index = (checkpoint_index // change_every) % len(checkpoints)
            selected_checkpoint = checkpoints[actual_index]

            # Get name for ComfyUI
            checkpoint_name = CheckpointUtils.get_checkpoint_name_for_comfyui(
                selected_checkpoint,
                base_path
            )

            # Load checkpoint
            print(f"[CheckpointRotation] Loading: {checkpoint_name}")
            model, clip, vae = self._load_checkpoint(checkpoint_name)

            # Create debug info
            images_in_cycle = (checkpoint_index % change_every) + 1
            debug_info = (
                f"RAW INDEX: {checkpoint_index}\n"
                f"CHANGE EVERY: {change_every}\n"
                f"ACTUAL CHECKPOINT INDEX: {actual_index}\n"
                f"TOTAL CHECKPOINTS: {len(checkpoints)}\n"
                f"IMAGE IN CYCLE: {images_in_cycle}/{change_every}\n"
                f"FILE: {os.path.basename(selected_checkpoint)}\n"
                f"NODE EXECUTED: YES"
            )

            print(f"[CheckpointRotation] Image #{checkpoint_index} -> Checkpoint {actual_index+1}/{len(checkpoints)} ({images_in_cycle}/{change_every})")

            return (model, clip, vae, checkpoint_name, debug_info)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[CheckpointRotation] {error_msg}")
            import traceback
            traceback.print_exc()
            return self._return_error(error_msg)

    def _load_checkpoint(self, checkpoint_name: str) -> Tuple:
        """Load checkpoint using ComfyUI's loader."""
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
        return (None, None, None, "ERROR", f"ERROR: {error_message}")

    @classmethod
    def IS_CHANGED(cls, checkpoint_index, **kwargs):
        """
        This is critical - return a value that changes when input changes.
        ComfyUI uses this to determine if node needs re-execution.
        """
        # Return float to ensure it's seen as changed
        return float(checkpoint_index)
