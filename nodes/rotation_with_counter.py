"""
Checkpoint rotation node that works with ComfyUI's batch generation.
Uses a counter input that can be controlled with "control after generate".
"""

import os
import sys
from typing import Dict, Tuple, Optional, Any

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


class CheckpointRotationWithCounter:
    """
    Checkpoint rotation that works with batch generation.

    How to use:
    1. Add this node
    2. Set subfolder and change_every
    3. Right-click the 'counter' input -> Convert to input
    4. Add a Primitive INT node
    5. Connect Primitive INT to counter input
    6. IMPORTANT: Double-click the LEFT SIDE of the Primitive node
    7. Set "control_after_generate" to "increment"
    8. Now when you generate with batch_size > 1, counter increments after each image
    9. Checkpoint changes every N images based on change_every setting
    """

    def __init__(self):
        self.checkpoint_cache = {}
        self.last_checkpoint = None
        self.counter_offset = 0  # Track offset for reset functionality

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """Define input parameters."""
        return {
            "required": {
                "counter": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100000,
                    "step": 1,
                    "tooltip": "Connect a Primitive INT with 'control_after_generate: increment'"
                }),
                "subfolder": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Checkpoint subfolder name (leave empty for root)"
                }),
                "change_every": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 1000,
                    "step": 1,
                    "tooltip": "Change checkpoint every N images"
                }),
                "reset_on_next": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Enable this to reset counter to 0 on next generation, then disable it"
                }),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "info")

    FUNCTION = "load_checkpoint"

    CATEGORY = "loaders"

    def load_checkpoint(
        self,
        counter: int,
        subfolder: str,
        change_every: int,
        reset_on_next: bool = False
    ) -> Tuple:
        """Load checkpoint based on counter value."""
        try:
            # Handle reset functionality
            if reset_on_next:
                # User wants to reset - store current counter as offset
                self.counter_offset = counter
                print(f"\n[CheckpointRotation] ⚠️ RESET ACTIVATED!")
                print(f"  Counter offset set to {counter}")
                print(f"  Next images will start from checkpoint 1")
                print(f"  Remember to DISABLE 'reset_on_next' after this generation!\n")

            # Apply offset to normalize counter
            normalized_counter = counter - self.counter_offset
            # Get base checkpoints directory
            base_path = PathUtils.get_checkpoints_base_path()

            # Validate subfolder
            is_valid, result = PathUtils.validate_subfolder(base_path, subfolder)
            if not is_valid:
                error_msg = f"Subfolder error: {result}"
                print(f"[CheckpointRotation] {error_msg}")
                return self._return_error(error_msg)

            checkpoint_folder = result

            # Discover checkpoints (with caching)
            cache_key = subfolder if subfolder else "root"
            if cache_key not in self.checkpoint_cache:
                checkpoints = CheckpointUtils.scan_checkpoint_folder(checkpoint_folder, recursive=True)
                if not checkpoints:
                    error_msg = f"No checkpoints found in: {subfolder or 'root folder'}"
                    print(f"[CheckpointRotation] {error_msg}")
                    return self._return_error(error_msg)
                self.checkpoint_cache[cache_key] = checkpoints
            else:
                checkpoints = self.checkpoint_cache[cache_key]

            # Calculate which checkpoint to use
            # This is the KEY: checkpoint only changes when counter crosses a multiple of change_every
            checkpoint_index = (normalized_counter // change_every) % len(checkpoints)
            selected_checkpoint = checkpoints[checkpoint_index]

            # Get checkpoint name for ComfyUI
            checkpoint_name = CheckpointUtils.get_checkpoint_name_for_comfyui(
                selected_checkpoint,
                base_path
            )

            # Load the checkpoint
            model, clip, vae = self._load_checkpoint(checkpoint_name)

            # Generate info
            images_with_current_checkpoint = (normalized_counter % change_every) + 1
            checkpoint_num = checkpoint_index + 1
            total_checkpoints = len(checkpoints)

            info = (
                f"Image #{normalized_counter} (raw counter: {counter})\n"
                f"Checkpoint {checkpoint_num}/{total_checkpoints}\n"
                f"File: {os.path.basename(selected_checkpoint)}\n"
                f"Image {images_with_current_checkpoint}/{change_every} with this checkpoint\n"
                f"Next change at image #{((normalized_counter // change_every) + 1) * change_every}"
            )

            # Only print when checkpoint actually changes
            if self.last_checkpoint != checkpoint_name:
                print(f"\n{'='*60}")
                print(f"[CheckpointRotation] CHECKPOINT CHANGED!")
                print(f"  Image #{normalized_counter} (raw: {counter}, offset: {self.counter_offset})")
                print(f"  Now using: {os.path.basename(selected_checkpoint)}")
                print(f"  Checkpoint {checkpoint_num} of {total_checkpoints}")
                print(f"  Will use this for {change_every} images")
                print(f"{'='*60}\n")
                self.last_checkpoint = checkpoint_name
            else:
                print(f"[CheckpointRotation] Image #{normalized_counter} - Still using {os.path.basename(selected_checkpoint)} ({images_with_current_checkpoint}/{change_every})")

            return (model, clip, vae, info)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[CheckpointRotation] {error_msg}")
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
    def IS_CHANGED(cls, counter, **kwargs):
        """Tell ComfyUI to re-execute when counter changes."""
        return counter
