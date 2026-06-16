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
    def get_checkpoints_roots() -> List[str]:
        """
        Get every registered ComfyUI checkpoints root directory.

        ComfyUI can register multiple checkpoint roots (the base models folder,
        ComfyUI-Shared, extra_model_paths entries, symlinked drives, etc.). The
        stock loaders merge all of them; this returns the full list so we can do
        the same instead of only looking at the first root.

        Returns:
            List of absolute paths to all checkpoints roots (may be empty).
        """
        try:
            import folder_paths
            roots = folder_paths.get_folder_paths("checkpoints")
            if roots:
                return list(roots)
        except ImportError:
            # Fallback if folder_paths is not available (for testing)
            pass

        # Fall back to the single best-guess base path.
        base = PathUtils.get_checkpoints_base_path()
        return [base] if base else []

    @staticmethod
    def validate_subfolder(base_path: str, subfolder: str) -> Tuple[bool, str]:
        """
        Validate that a subfolder exists under any registered checkpoints root.

        ComfyUI may register several checkpoints roots. A subfolder (e.g.
        "Illustrious") can live under any one of them, not necessarily the first
        root returned by folder_paths. This checks every root and returns the
        first one that actually contains the subfolder.

        Args:
            base_path: Primary checkpoints directory (checked first)
            subfolder: Subfolder path relative to a checkpoints root

        Returns:
            Tuple of (is_valid, full_path or error_message)
        """
        if not subfolder:
            return True, base_path

        # Normalize the widget value: trim whitespace, unify separators, and
        # drop any trailing separator (the widget often stores "Illustrious\").
        subfolder = subfolder.strip().replace("\\", os.sep).replace("/", os.sep)
        subfolder = subfolder.strip(os.sep)

        if not subfolder:
            return True, base_path

        # Prevent directory traversal attacks
        if ".." in subfolder.split(os.sep):
            return False, "Invalid subfolder path: directory traversal not allowed"

        # Gather every registered checkpoints root, with base_path checked first.
        roots = PathUtils.get_checkpoints_roots()
        if base_path and base_path not in roots:
            roots.insert(0, base_path)

        searched = []
        for root in roots:
            try:
                root_abs = os.path.abspath(root)
                full_path = os.path.abspath(os.path.join(root_abs, subfolder))
            except (OSError, ValueError):
                continue

            # Ensure the resolved path stays within this root. commonpath raises
            # ValueError for paths on different drives (Windows C: vs N:), which
            # just means this root doesn't contain the subfolder.
            try:
                if os.path.commonpath([full_path, root_abs]) != root_abs:
                    continue
            except ValueError:
                continue

            searched.append(root_abs)

            if os.path.isdir(full_path):
                return True, full_path

        if searched:
            roots_str = ", ".join(searched)
            return False, (
                f"Subfolder does not exist in any checkpoints root: "
                f"{subfolder} (searched: {roots_str})"
            )
        return False, f"Subfolder does not exist: {subfolder}"

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
