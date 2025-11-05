"""
Helper node to create filenames with checkpoint information.
"""

from typing import Dict, Tuple, Any
import re


class CheckpointFilename:
    """
    Creates a filename that includes checkpoint information.
    Connect the checkpoint_name output from rotation node to this,
    then connect this to SaveImage's filename_prefix.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """Define input parameters."""
        return {
            "required": {
                "checkpoint_name": ("STRING", {
                    "default": "checkpoint",
                    "multiline": False,
                    "tooltip": "Connect from Checkpoint Rotation node"
                }),
                "prefix": ("STRING", {
                    "default": "ComfyUI",
                    "multiline": False,
                    "tooltip": "Prefix for filename"
                }),
                "include_path": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Include subfolder path in filename"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("filename_prefix",)

    FUNCTION = "create_filename"

    CATEGORY = "utils"

    OUTPUT_NODE = False

    def create_filename(
        self,
        checkpoint_name: str,
        prefix: str = "ComfyUI",
        include_path: bool = False
    ) -> Tuple[str]:
        """Create filename with checkpoint info."""

        # Extract just the checkpoint name without extension
        if include_path:
            # Keep the path but clean it
            clean_name = checkpoint_name.replace("\\", "_").replace("/", "_")
            clean_name = clean_name.rsplit(".", 1)[0]  # Remove extension
        else:
            # Just get the filename
            import os
            clean_name = os.path.basename(checkpoint_name)
            clean_name = clean_name.rsplit(".", 1)[0]  # Remove extension

        # Remove special characters that might cause issues
        clean_name = re.sub(r'[<>:"|?*]', '', clean_name)

        # Create filename prefix
        if prefix:
            filename = f"{prefix}_{clean_name}"
        else:
            filename = clean_name

        print(f"[CheckpointFilename] Generated filename prefix: {filename}")

        return (filename,)

    @classmethod
    def IS_CHANGED(cls, checkpoint_name, **kwargs):
        """Force re-execution when checkpoint changes."""
        return checkpoint_name
