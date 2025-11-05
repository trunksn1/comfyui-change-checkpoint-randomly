"""
Batch index counter node for tracking generation progress.
"""

from typing import Dict, Tuple, Any


class BatchIndexCounter:
    """
    Helper node to manage and increment batch index for checkpoint rotation.

    This node helps track the current position in batch generation,
    making it easier to use with CheckpointRotation node.
    """

    # Class variable to maintain state across executions
    _counters: Dict[str, int] = {}

    def __init__(self):
        """Initialize the batch counter node."""
        self.counter_id = "default"

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary defining required and optional inputs
        """
        return {
            "required": {
                "action": (["increment", "set", "reset"], {
                    "default": "increment",
                    "tooltip": "Action to perform on the counter"
                }),
            },
            "optional": {
                "counter_id": ("STRING", {
                    "default": "default",
                    "multiline": False,
                    "tooltip": "Unique ID for this counter (allows multiple independent counters)"
                }),
                "set_value": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000000,
                    "step": 1,
                    "tooltip": "Value to set when action is 'set'"
                }),
                "increment_by": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000,
                    "step": 1,
                    "tooltip": "Amount to increment by"
                }),
            }
        }

    RETURN_TYPES = ("INT", "STRING")
    RETURN_NAMES = ("batch_index", "info")

    FUNCTION = "update_counter"

    CATEGORY = "utils"

    OUTPUT_NODE = False

    def update_counter(
        self,
        action: str,
        counter_id: str = "default",
        set_value: int = 0,
        increment_by: int = 1
    ) -> Tuple[int, str]:
        """
        Update the batch counter based on the specified action.

        Args:
            action: Action to perform (increment/set/reset)
            counter_id: Unique identifier for this counter
            set_value: Value to set (when action is 'set')
            increment_by: Amount to increment (when action is 'increment')

        Returns:
            Tuple of (current_value, info_string)
        """
        # Initialize counter if it doesn't exist
        if counter_id not in self._counters:
            self._counters[counter_id] = 0

        # Perform action
        if action == "reset":
            self._counters[counter_id] = 0
            info = f"Counter '{counter_id}' reset to 0"

        elif action == "set":
            self._counters[counter_id] = set_value
            info = f"Counter '{counter_id}' set to {set_value}"

        elif action == "increment":
            self._counters[counter_id] += increment_by
            info = f"Counter '{counter_id}' incremented to {self._counters[counter_id]}"

        else:
            # Default to increment
            self._counters[counter_id] += increment_by
            info = f"Counter '{counter_id}' = {self._counters[counter_id]}"

        current_value = self._counters[counter_id]
        print(f"[BatchIndexCounter] {info}")

        return (current_value, info)

    @classmethod
    def reset_all_counters(cls):
        """Reset all counters. Useful for batch processing."""
        cls._counters.clear()

    @classmethod
    def get_counter(cls, counter_id: str = "default") -> int:
        """
        Get current value of a counter without modifying it.

        Args:
            counter_id: Counter identifier

        Returns:
            Current counter value
        """
        return cls._counters.get(counter_id, 0)


class SimpleCounter:
    """
    Simplified counter node that just outputs incrementing numbers.

    Useful for simple sequential workflows.
    """

    _value: int = 0

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """Define input parameters."""
        return {
            "required": {
                "start": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000000,
                    "tooltip": "Starting value"
                }),
                "step": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000,
                    "tooltip": "Increment step"
                }),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)

    FUNCTION = "get_value"

    CATEGORY = "utils"

    OUTPUT_NODE = False

    def get_value(self, start: int, step: int) -> Tuple[int]:
        """
        Get current counter value.

        Args:
            start: Starting value
            step: Increment step

        Returns:
            Tuple containing current value
        """
        current = self._value
        self._value += step

        # Reset if we've gone too far
        if self._value > 1000000:
            self._value = start

        return (current,)

    @classmethod
    def reset(cls):
        """Reset the counter."""
        cls._value = 0


# Node registration is handled in main __init__.py
# Keeping this for reference only
# NODE_CLASS_MAPPINGS = {
#     "BatchIndexCounter": BatchIndexCounter,
#     "SimpleCounter": SimpleCounter
# }
#
# NODE_DISPLAY_NAME_MAPPINGS = {
#     "BatchIndexCounter": "Batch Index Counter",
#     "SimpleCounter": "Simple Counter"
# }
