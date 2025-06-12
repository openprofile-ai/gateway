from typing import Dict, List, Any

from handlers.base_handler import BaseHandler


class ListOfCategoriesHandler(BaseHandler):
    async def tool_method(self) -> Dict[str, List[str]]:
        """
        Retrieve a list of all available fact categories.
        
        Returns:
            Dict containing a list of category names
        """
        # Placeholder implementation
        return {"categories": []}
