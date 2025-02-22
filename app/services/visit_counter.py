from typing import Dict, List, Any
import asyncio
from datetime import datetime
from ..core.redis_manager import RedisManager

class VisitCounterService:
    def __init__(self):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = RedisManager()
        self.cache : Dict[str, Dict[str, Any]] = {}  # In-memory cache
        self.TTL = 5  # Cache expiration time in seconds

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        """
        # TODO: Implement visit count increment
        try:
            if page_id in self.cache:
                del self.cache[page_id]
            new_count = await self.redis_manager.increment(page_id)

            return new_count
        except Exception as e:
            print(f"Error incrementing visit count: {e}")
            return 0  # Return 0 in case of failure

    async def get_visit_count(self, page_id: str) -> Dict[str, Any]:
        """
        Get current visit count for a page from Redis 
        
        Args:
            page_id: Unique identifier for the page
            
        Returns:
            Current visit count
        """
        # TODO: Implement getting visit count
        try:
            current_time = datetime.now().timestamp()
            key = page_id
            if page_id in self.cache:
                cached_data = self.cache[key]
             
                if current_time < cached_data['expires_at']:
                    return {
                        "visits": cached_data['value'],
                        "served_via": "in_memory"
                    }
                del self.cache[key]
            count = await self.redis_manager.get(page_id)
            if count is None:
                return {
                    "visits": 0,
                    "served_via": "redis"
                }
            
            value_int = int(count)
            self.cache[key] = {
                'value': value_int,
                'expires_at': current_time + self.TTL
            }
            
            return {
                "visits": value_int,
                "served_via": "redis"
            }
            return count
        except Exception as e:
            print(f"Error getting visit count: {e}")
            return 0
