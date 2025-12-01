"""
Main checkpoint rotation node for ComfyUI.
"""

import os
import sys
from typing import Dict, List, Tuple, Optional, Any

# Use relative imports to avoid conflicts with ComfyUI's built-in modules
try:
    from ..utils.path_utils import PathUtils
    from ..utils.checkpoint_utils import CheckpointUtils
except ImportError:
    # Fallback for direct execution
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from utils.path_utils import PathUtils
    from utils.checkpoint_utils import CheckpointUtils


class CheckpointRotationNode:
    """
    A custom ComfyUI node that rotates through checkpoints based on batch generation count.

    This node allows automatic switching between different model checkpoints during
    batch image generation, enabling diverse outputs from multiple models.
    """

    def __init__(self):
        """Initialize the checkpoint rotation node."""
        self.checkpoint_cache: Dict[str, List[str]] = {}
        self.last_checkpoint_path: Optional[str] = None

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary defining required and optional inputs
        """
        return {
            "required": {
                "subfolder": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "subfolder path (leave empty for root)"
                }),
                "change_interval": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 10000,
                    "step": 1,
                    "display": "number",
                    "tooltip": "Number of images to generate before switching checkpoint"
                }),
                "batch_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000000,
                    "step": 1,
                    "display": "number",
                    "tooltip": "Current batch index (use BatchIndexCounter node)"
                }),
                "rotation_mode": (["sequential", "random", "shuffle"], {
                    "default": "sequential",
                    "tooltip": "How to select next checkpoint"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Seed for random/shuffle modes"
                }),
            },
            "optional": {
                "checkpoint_filter": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "filter pattern (optional)"
                }),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "checkpoint_name", "info")

    FUNCTION = "load_checkpoint_rotated"

    CATEGORY = "loaders"

    OUTPUT_NODE = False

    def load_checkpoint_rotated(
        self,
        subfolder: str,
        change_interval: int,
        batch_index: int,
        rotation_mode: str,
        seed: int,
        checkpoint_filter: str = ""
    ) -> Tuple:
        """
        Main execution function that loads the appropriate checkpoint based on rotation logic.

        Args:
            subfolder: Subfolder path relative to checkpoints directory
            change_interval: Number of images before changing checkpoint
            batch_index: Current position in batch generation
            rotation_mode: How to select checkpoint (sequential/random/shuffle)
            seed: Random seed for reproducibility
            checkpoint_filter: Optional filter pattern for checkpoint names

        Returns:
            Tuple of (model, clip, vae, checkpoint_name, info)
        """
        try:
            # Get base checkpoints directory
            base_path = PathUtils.get_checkpoints_base_path()

            # Validate and get full path to subfolder
            is_valid, result = PathUtils.validate_subfolder(base_path, subfolder)
            if not is_valid:
                error_msg = f"Error: {result}"
                print(error_msg)
                return self._return_error(error_msg)

            checkpoint_folder = result

            # Discover checkpoints
            checkpoints = self._discover_checkpoints(
                checkpoint_folder,
                checkpoint_filter,
                subfolder
            )

            if not checkpoints:
                error_msg = f"No checkpoints found in: {subfolder or 'root checkpoints folder'}"
                if checkpoint_filter:
                    error_msg += f" (filter: '{checkpoint_filter}')"
                print(error_msg)
                return self._return_error(error_msg)

            # Select checkpoint based on rotation logic
            selected_checkpoint = CheckpointUtils.select_checkpoint_by_rotation(
                checkpoints,
                batch_index,
                change_interval,
                rotation_mode,
                seed
            )

            if not selected_checkpoint:
                error_msg = "Failed to select checkpoint"
                print(error_msg)
                return self._return_error(error_msg)

            # Get checkpoint name for ComfyUI (for loading)
            checkpoint_name_for_loading = CheckpointUtils.get_checkpoint_name_for_comfyui(
                selected_checkpoint,
                base_path
            )

            # Load the checkpoint
            model, clip, vae = self._load_checkpoint(checkpoint_name_for_loading)

            # Get basename for output (for metadata and display compatibility)
            checkpoint_name = os.path.basename(selected_checkpoint)

            # Generate info string
            rotation_num = batch_index // change_interval
            checkpoint_index = rotation_num % len(checkpoints)
            info = (
                f"Checkpoint: {os.path.basename(selected_checkpoint)}\n"
                f"Index: {checkpoint_index + 1}/{len(checkpoints)}\n"
                f"Batch: {batch_index}\n"
                f"Rotation: {rotation_num}\n"
                f"Mode: {rotation_mode}"
            )

            self.last_checkpoint_path = selected_checkpoint
            print(f"[CheckpointRotation] Loaded: {checkpoint_name_for_loading} -> {checkpoint_name}")

            return (model, clip, vae, checkpoint_name, info)

        except Exception as e:
            error_msg = f"Error in checkpoint rotation: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return self._return_error(error_msg)

    def _discover_checkpoints(
        self,
        folder_path: str,
        filter_pattern: str,
        cache_key: str
    ) -> List[str]:
        """
        Discover checkpoints in folder with caching.

        Args:
            folder_path: Path to folder to scan
            filter_pattern: Optional filter pattern
            cache_key: Key for caching results

        Returns:
            List of checkpoint paths
        """
        # Create cache key
        full_cache_key = f"{cache_key}:{filter_pattern}"

        # Check cache
        if full_cache_key in self.checkpoint_cache:
            return self.checkpoint_cache[full_cache_key]

        # Scan for checkpoints
        checkpoints = CheckpointUtils.scan_checkpoint_folder(folder_path, recursive=True)

        # Apply filter if provided
        if filter_pattern:
            checkpoints = CheckpointUtils.filter_checkpoints(checkpoints, filter_pattern)

        # Cache results
        self.checkpoint_cache[full_cache_key] = checkpoints

        return checkpoints

    def _load_checkpoint(self, checkpoint_name: str) -> Tuple:
        """
        Load a checkpoint using ComfyUI's checkpoint loader.

        Args:
            checkpoint_name: Name of checkpoint to load (relative to checkpoints folder)

        Returns:
            Tuple of (model, clip, vae)
        """
        try:
            # Import ComfyUI modules
            import comfy.sd
            import folder_paths

            # Get full path to checkpoint
            checkpoint_path = folder_paths.get_full_path("checkpoints", checkpoint_name)

            # Load checkpoint
            out = comfy.sd.load_checkpoint_guess_config(
                checkpoint_path,
                output_vae=True,
                output_clip=True,
                embedding_directory=folder_paths.get_folder_paths("embeddings")
            )

            return (out[0], out[1], out[2])

        except ImportError as e:
            # Fallback error handling when ComfyUI modules not available
            raise ImportError(f"ComfyUI modules not available: {e}")
        except Exception as e:
            raise Exception(f"Failed to load checkpoint '{checkpoint_name}': {e}")

    def _return_error(self, error_message: str) -> Tuple:
        """
        Return error state with None values.

        Args:
            error_message: Error message to include

        Returns:
            Tuple with None values and error message
        """
        return (None, None, None, "ERROR", error_message)

    @classmethod
    def IS_CHANGED(cls, **kwargs) -> float:
        """
        Determine if node needs to re-execute.

        This node should re-execute when batch_index changes.

        Returns:
            Value that changes when node should re-execute
        """
        # Return batch_index so node re-executes on each batch change
        return float(kwargs.get('batch_index', 0))


# Node registration is handled in main __init__.py
# Keeping this for reference only
# NODE_CLASS_MAPPINGS = {
#     "CheckpointRotation": CheckpointRotationNode
# }
#
# NODE_DISPLAY_NAME_MAPPINGS = {
#     "CheckpointRotation": "Checkpoint Rotation Loader"
# }
