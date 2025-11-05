"""
Node that modifies workflow metadata to include checkpoint information.
This should work with any standard SaveImage node.
"""

import nodes
from typing import Dict, Tuple, Any


class AddCheckpointToMetadata:
    """
    Adds checkpoint information to the workflow metadata that SaveImage will use.

    This node passes through the images unchanged but modifies the metadata
    that will be saved by downstream SaveImage nodes.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """Define input parameters."""
        return {
            "required": {
                "images": ("IMAGE",),
                "checkpoint_name": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)

    FUNCTION = "add_checkpoint_metadata"

    CATEGORY = "image"

    OUTPUT_NODE = False

    def add_checkpoint_metadata(
        self,
        images,
        checkpoint_name: str,
        prompt=None,
        extra_pnginfo=None
    ):
        """Add checkpoint to metadata and pass through images."""

        # Modify the prompt to include checkpoint info
        if prompt is not None:
            # Add checkpoint info to the prompt dict
            if isinstance(prompt, dict):
                # Find our node in the prompt
                for node_id, node_data in prompt.items():
                    if isinstance(node_data, dict) and node_data.get("class_type") == "AddCheckpointToMetadata":
                        # Add checkpoint as a visible input so it appears in metadata
                        if "inputs" not in node_data:
                            node_data["inputs"] = {}
                        node_data["inputs"]["checkpoint_used"] = checkpoint_name
                        print(f"[AddCheckpointToMetadata] Added checkpoint to metadata: {checkpoint_name}")
                        break

        # Pass through images unchanged
        return (images,)

    @classmethod
    def IS_CHANGED(cls, images, checkpoint_name, **kwargs):
        """Force re-execution when checkpoint changes."""
        return checkpoint_name
