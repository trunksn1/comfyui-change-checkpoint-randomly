"""
Path utility functions for handling checkpoint directory operations.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple


class PathUtils:
    """Utility class for path operations related to checkpoint management."""

    @staticmethod
    def get_checkpoints_base_path() -> str:
        """
        Get the base ComfyUI checkpoints directory.

        Returns:
            str: Absolute path to the checkpoints directory
        """
        try:
            import folder_paths
            checkpoints_dir = folder_paths.get_folder_paths("checkpoints")
            if checkpoints_dir:
                return checkpoints_dir[0]
        except ImportError:
            # Fallback if folder_paths is not available (for testing)
            pass

        # Fallback to common ComfyUI checkpoint locations
        possible_paths = [
            os.path.join(os.getcwd(), "models", "checkpoints"),
            os.path.join(os.path.expanduser("~"), "ComfyUI", "models", "checkpoints"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Default to current directory + models/checkpoints
        return os.path.join(os.getcwd(), "models", "checkpoints")

    @staticmethod
    def list_subfolders(base_path: str) -> List[str]:
        """
        List all subfolders in the checkpoints directory.

        Args:
            base_path: Base directory to search

        Returns:
            List of subfolder names (relative to base_path)
        """
        if not os.path.exists(base_path):
            return []

        subfolders = []
        try:
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    subfolders.append(item)
        except (PermissionError, OSError):
            pass

        return sorted(subfolders)

    @staticmethod
    def validate_subfolder(base_path: str, subfolder: str) -> Tuple[bool, str]:
        """
        Validate that a subfolder exists and is accessible.

        Args:
            base_path: Base checkpoints directory
            subfolder: Subfolder path relative to base_path

        Returns:
            Tuple of (is_valid, full_path or error_message)
        """
        if not subfolder:
            return True, base_path

        # Prevent directory traversal attacks
        if ".." in subfolder or subfolder.startswith("/"):
            return False, "Invalid subfolder path: directory traversal not allowed"

        full_path = os.path.join(base_path, subfolder)

        # Ensure the resolved path is still within base_path
        try:
            full_path = os.path.abspath(full_path)
            base_path = os.path.abspath(base_path)

            if not full_path.startswith(base_path):
                return False, "Invalid subfolder path: outside checkpoints directory"
        except (OSError, ValueError) as e:
            return False, f"Invalid path: {str(e)}"

        if not os.path.exists(full_path):
            return False, f"Subfolder does not exist: {subfolder}"

        if not os.path.isdir(full_path):
            return False, f"Path is not a directory: {subfolder}"

        return True, full_path

    @staticmethod
    def get_relative_path(base_path: str, full_path: str) -> str:
        """
        Get relative path from base to full path.

        Args:
            base_path: Base directory
            full_path: Full path to convert

        Returns:
            Relative path string
        """
        try:
            return os.path.relpath(full_path, base_path)
        except ValueError:
            return full_path
