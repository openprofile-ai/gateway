from typing import Any

from gateway.handlers.base_handler import BaseHandler


class DisableFactPodHandler(BaseHandler):
    async def tool_method(self, pod_name: str) -> dict[str, Any]:
        """
        Disable a fact pod with the given name.

        Args:
            pod_name: The name of the pod to disable

        Returns:
            Dict containing status of the operation
        """
        # Placeholder implementation
        return {"status": "disabled", "pod_name": pod_name}
