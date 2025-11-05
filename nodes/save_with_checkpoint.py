"""
Custom save image node that includes checkpoint info in metadata.
"""

import os
import json
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from typing import Dict, Tuple, Any


class SaveImageWithCheckpoint:
    """
    Saves images with checkpoint information embedded in PNG metadata.
    This ensures each image has the correct checkpoint in its metadata.
    """

    def __init__(self):
        self.output_dir = self.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """Define input parameters."""
        return {
            "required": {
                "images": ("IMAGE",),
                "checkpoint_name": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Connect from Checkpoint Rotation node"
                }),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "tooltip": "Prefix for saved files"
                }),
            },
            "optional": {
                "checkpoint_info": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Additional info to embed"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image"

    def save_images(
        self,
        images,
        checkpoint_name: str = "",
        filename_prefix: str = "ComfyUI",
        checkpoint_info: str = "",
        prompt=None,
        extra_pnginfo=None
    ):
        """Save images with checkpoint metadata."""

        filename_prefix += self.prefix_append

        # Get image dimensions
        image_height = images[0].shape[0] if len(images) > 0 else 512
        image_width = images[0].shape[1] if len(images) > 0 else 512

        full_output_folder, filename, counter, subfolder, filename_prefix = \
            self.get_save_path(filename_prefix, self.output_dir, image_width, image_height)

        results = list()

        for (batch_number, image) in enumerate(images):
            # Convert tensor to numpy array
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            # Create metadata
            metadata = PngInfo()

            # Add standard ComfyUI workflow data
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            # Add checkpoint information (THE KEY PART!)
            if checkpoint_name:
                metadata.add_text("checkpoint", checkpoint_name)
                metadata.add_text("model", checkpoint_name)  # Alternative field name

            if checkpoint_info:
                metadata.add_text("checkpoint_info", checkpoint_info)

            # Generate filename
            file = f"{filename}_{counter:05}_.png"

            # Save with metadata
            img.save(
                os.path.join(full_output_folder, file),
                pnginfo=metadata,
                compress_level=self.compress_level
            )

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })

            counter += 1

            print(f"[SaveImageWithCheckpoint] Saved {file} with checkpoint: {checkpoint_name}")

        return {"ui": {"images": results}}

    def get_output_directory(self):
        """Get output directory from ComfyUI."""
        try:
            import folder_paths
            return folder_paths.get_output_directory()
        except:
            # Fallback
            return os.path.join(os.path.dirname(__file__), "..", "..", "output")

    def get_save_path(self, filename_prefix, output_dir, image_width=512, image_height=512):
        """Get save path details."""
        try:
            import folder_paths
            return folder_paths.get_save_image_path(
                filename_prefix,
                output_dir,
                image_width,
                image_height
            )
        except:
            # Fallback
            def map_filename(filename):
                prefix_len = len(os.path.basename(filename_prefix))
                prefix = filename[:prefix_len + 1]
                try:
                    digits = int(filename[prefix_len + 1:].split('_')[0])
                except:
                    digits = 0
                return (digits, prefix)

            def compute_vars(input, width, height):
                input = input.replace("%width%", str(width))
                input = input.replace("%height%", str(height))
                return input

            filename_prefix = compute_vars(filename_prefix, image_width, image_height)
            subfolder = os.path.dirname(os.path.normpath(filename_prefix))
            filename = os.path.basename(os.path.normpath(filename_prefix))
            full_output_folder = os.path.join(output_dir, subfolder)

            try:
                counter = max(
                    filter(
                        lambda a: a[1][:-1] == filename and a[1][-1] == "_",
                        map(map_filename, os.listdir(full_output_folder))
                    )
                )[0] + 1
            except ValueError:
                counter = 1
            except FileNotFoundError:
                os.makedirs(full_output_folder, exist_ok=True)
                counter = 1

            return full_output_folder, filename, counter, subfolder, filename_prefix

    @classmethod
    def IS_CHANGED(cls, images, checkpoint_name, **kwargs):
        """Force re-execution when checkpoint changes."""
        return checkpoint_name
