"""
In-Memory Search Component

This module provides a class for searching and querying memory items in the
in-memory storage.
"""

from typing import Any, Dict, List, Optional

from neuroca.memory.backends.in_memory.components.storage import InMemoryStorage


class InMemorySearch:
    """
    Handles search and query operations for memory items in in-memory storage.
    
    This class provides methods for searching, filtering, and retrieving memory
    items based on various criteria.
    """
    
    def __init__(self, storage: InMemoryStorage):
        """
        Initialize the search operations handler.
        
        Args:
            storage: The storage component to use
        """
        self.storage = storage
    
    async def query_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query items in the in-memory store.
        
        Args:
            filters: Dict of field-value pairs to filter by
            sort_by: Field to sort results by
            ascending: Sort order (True for ascending, False for descending)
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of items matching the query criteria
        """
        filters = filters or {}
        
        await self.storage.acquire_lock()
        try:
            # Make a copy of all items with their IDs
            items_with_ids = [
                {"_id": item_id, **item}
                for item_id, item in self.storage.get_all_items().items()
            ]
            
            # Apply filters
            if filters:
                filtered_items = []
                for item in items_with_ids:
                    if self._matches_filters(item, filters):
                        filtered_items.append(item)
                items_with_ids = filtered_items
            
            # Apply sorting
            if sort_by:
                items_with_ids = sorted(
                    items_with_ids,
                    key=lambda x: self._get_field_value(x, sort_by),
                    reverse=not ascending,
                )
            
            # Apply pagination
            if offset:
                items_with_ids = items_with_ids[offset:]
            if limit:
                items_with_ids = items_with_ids[:limit]
            
            return items_with_ids
        finally:
            self.storage.release_lock()
    
    async def count_items(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count items in the in-memory store.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of matching items
        """
        if not filters:
            await self.storage.acquire_lock()
            try:
                return self.storage.count_items()
            finally:
                self.storage.release_lock()
        
        # If filters are provided, we need to check each item
        results = await self.query_items(filters=filters)
        return len(results)
    
    async def find_items_by_field(
        self, field: str, value: Any, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find items by a specific field value.
        
        Args:
            field: The field to search by
            value: The value to match
            limit: Maximum number of results to return
            
        Returns:
            List of matching items
        """
        # Create a filter for the specified field
        filters = {field: value}
        
        # Use the query_items method
        return await self.query_items(filters=filters, limit=limit)
    
    async def text_search(
        self, query: str, fields: List[str], limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform a simple text search across specified fields.
        
        Args:
            query: The text to search for
            fields: List of fields to search in
            limit: Maximum number of results to return
            
        Returns:
            List of matching items
        """
        await self.storage.acquire_lock()
        try:
            items_with_ids = [
                {"_id": item_id, **item}
                for item_id, item in self.storage.get_all_items().items()
            ]
            
            # Filter items by text match in specified fields
            matching_items = []
            for item in items_with_ids:
                for field in fields:
                    value = self._get_field_value(item, field)
                    if value is not None and isinstance(value, str) and query.lower() in value.lower():
                        matching_items.append(item)
                        break
            
            # Apply limit if provided
            if limit:
                matching_items = matching_items[:limit]
            
            return matching_items
        finally:
            self.storage.release_lock()
    
    def _matches_filters(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if an item matches the given filters.
        
        Args:
            item: The item to check
            filters: Dict of field-value pairs to filter by
            
        Returns:
            bool: True if the item matches all filters, False otherwise
        """
        for field, value in filters.items():
            if field.startswith("_meta."):
                # Handle nested fields in metadata
                meta_field = field.split(".", 1)[1]
                if "_meta" not in item or meta_field not in item["_meta"]:
                    return False
                
                if item["_meta"][meta_field] != value:
                    return False
            elif field == "_id":
                # Special case for item ID
                if item.get("_id") != value:
                    return False
            elif "." in field:
                # Handle nested fields
                field_parts = field.split(".")
                current = item
                
                for part in field_parts:
                    if not isinstance(current, dict) or part not in current:
                        return False
                    current = current[part]
                
                if current != value:
                    return False
            elif field not in item:
                return False
            elif item[field] != value:
                return False
        
        return True
    
    def _get_field_value(self, item: Dict[str, Any], field: str) -> Any:
        """
        Get the value of a field from an item, handling nested fields.
        
        Args:
            item: The item to get the field value from
            field: The field to get
            
        Returns:
            The field value or None if not found
        """
        if field == "_id":
            return item.get("_id")
        
        if field.startswith("_meta."):
            meta_field = field.split(".", 1)[1]
            if "_meta" in item and meta_field in item["_meta"]:
                return item["_meta"][meta_field]
            return None
        
        if "." in field:
            field_parts = field.split(".")
            current = item
            
            for part in field_parts:
                if not isinstance(current, dict) or part not in current:
                    return None
                current = current[part]
            
            return current
        
        return item.get(field)
