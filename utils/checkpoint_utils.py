"""
Checkpoint utility functions for discovering and managing checkpoint files.
"""

import os
import random
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


class CheckpointUtils:
    """Utility class for checkpoint file operations."""

    # Supported checkpoint file extensions
    SUPPORTED_EXTENSIONS = ['.safetensors', '.ckpt', '.pt', '.pth']

    @staticmethod
    def scan_checkpoint_folder(folder_path: str, recursive: bool = True) -> List[str]:
        """
        Scan folder for checkpoint files.

        Args:
            folder_path: Path to folder to scan
            recursive: Whether to scan subdirectories recursively

        Returns:
            List of absolute paths to checkpoint files
        """
        checkpoints = []

        if not os.path.exists(folder_path):
            return checkpoints

        try:
            if recursive:
                # Recursively search for checkpoint files
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if CheckpointUtils._is_checkpoint_file(file):
                            full_path = os.path.join(root, file)
                            checkpoints.append(full_path)
            else:
                # Only search immediate directory
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    if os.path.isfile(item_path) and CheckpointUtils._is_checkpoint_file(item):
                        checkpoints.append(item_path)
        except (PermissionError, OSError) as e:
            print(f"Error scanning checkpoint folder {folder_path}: {e}")

        return sorted(checkpoints)

    @staticmethod
    def _is_checkpoint_file(filename: str) -> bool:
        """
        Check if a file is a checkpoint based on extension.

        Args:
            filename: Name of the file to check

        Returns:
            True if file is a checkpoint, False otherwise
        """
        return any(filename.lower().endswith(ext) for ext in CheckpointUtils.SUPPORTED_EXTENSIONS)

    @staticmethod
    def filter_checkpoints(checkpoint_list: List[str], pattern: Optional[str] = None) -> List[str]:
        """
        Filter checkpoints by name pattern.

        Args:
            checkpoint_list: List of checkpoint paths
            pattern: Pattern to match (case-insensitive substring match)

        Returns:
            Filtered list of checkpoint paths
        """
        if not pattern:
            return checkpoint_list

        pattern_lower = pattern.lower()
        filtered = []

        for checkpoint in checkpoint_list:
            filename = os.path.basename(checkpoint).lower()
            if pattern_lower in filename:
                filtered.append(checkpoint)

        return filtered

    @staticmethod
    def get_checkpoint_info(checkpoint_path: str) -> Dict[str, Any]:
        """
        Get metadata about a checkpoint file.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Dictionary with checkpoint metadata
        """
        info = {
            'path': checkpoint_path,
            'filename': os.path.basename(checkpoint_path),
            'exists': False,
            'size': 0,
            'size_mb': 0,
            'modified': None,
        }

        if os.path.exists(checkpoint_path):
            info['exists'] = True
            try:
                stat = os.stat(checkpoint_path)
                info['size'] = stat.st_size
                info['size_mb'] = stat.st_size / (1024 * 1024)
                info['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except (OSError, PermissionError):
                pass

        return info

    @staticmethod
    def select_checkpoint_by_rotation(
        checkpoint_list: List[str],
        batch_index: int,
        interval: int,
        mode: str = "sequential",
        seed: int = 0
    ) -> Optional[str]:
        """
        Select a checkpoint based on rotation logic.

        Args:
            checkpoint_list: List of available checkpoint paths
            batch_index: Current position in batch generation
            interval: Number of images before changing checkpoint
            mode: Rotation mode - "sequential", "random", or "shuffle"
            seed: Random seed for reproducibility

        Returns:
            Selected checkpoint path, or None if list is empty
        """
        if not checkpoint_list:
            return None

        # Calculate which checkpoint index to use
        rotation_index = (batch_index // interval) % len(checkpoint_list)

        if mode == "sequential":
            return checkpoint_list[rotation_index]

        elif mode == "random":
            # Use seed + rotation_index for reproducible randomness
            # This ensures same checkpoint for all images in an interval
            rng = random.Random(seed + rotation_index)
            return rng.choice(checkpoint_list)

        elif mode == "shuffle":
            # Shuffle list once based on seed, then iterate sequentially
            rng = random.Random(seed)
            shuffled_list = checkpoint_list.copy()
            rng.shuffle(shuffled_list)
            return shuffled_list[rotation_index]

        else:
            # Default to sequential
            return checkpoint_list[rotation_index]

    @staticmethod
    def get_checkpoint_name_for_comfyui(checkpoint_path: str, base_path: str) -> str:
        """
        Get checkpoint name in ComfyUI format (relative to checkpoints folder).

        Args:
            checkpoint_path: Absolute path to checkpoint
            base_path: Base checkpoints directory

        Returns:
            Checkpoint name suitable for ComfyUI's checkpoint loader (with forward slashes)
        """
        checkpoint_abs = os.path.abspath(checkpoint_path)

        # The checkpoint may live under any registered checkpoints root, not just
        # base_path. ComfyUI's get_full_path() resolves a name against all roots,
        # so we compute the relative name against the root that actually contains
        # this file (preferring the most specific / longest matching root).
        candidate_roots = []
        try:
            import folder_paths
            candidate_roots.extend(folder_paths.get_folder_paths("checkpoints") or [])
        except ImportError:
            pass
        if base_path:
            candidate_roots.append(base_path)

        best_rel = None
        best_root_len = -1
        for root in candidate_roots:
            try:
                root_abs = os.path.abspath(root)
            except (OSError, ValueError):
                continue
            try:
                if os.path.commonpath([checkpoint_abs, root_abs]) != root_abs:
                    continue
            except ValueError:
                # Different drives (Windows) -> this root can't contain the file.
                continue
            if len(root_abs) > best_root_len:
                best_root_len = len(root_abs)
                best_rel = os.path.relpath(checkpoint_abs, root_abs)

        if best_rel is not None:
            return best_rel.replace(os.sep, '/')

        # Fall back to base_path-relative, then basename.
        try:
            rel_path = os.path.relpath(checkpoint_abs, base_path)
            return rel_path.replace(os.sep, '/')
        except ValueError:
            return os.path.basename(checkpoint_path)
