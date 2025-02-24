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
        self.buffer: Dict[str, int] = {}  # Buffer for batching writes
        self.flush_interval = 30  # Time interval (seconds) for flushing buffer to Redis
        self.lock = asyncio.Lock()  # Lock to prevent race conditions
        asyncio.create_task(self.flush_pending_writes())  # Start background flush task

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        """
        # TODO: Implement visit count increment
        try:
            async with self.lock:
                if page_id in self.buffer:
                    self.buffer[page_id] += 1
                else:
                    self.buffer[page_id] = 1
        except Exception as e:
            print(f"Error incrementing visit count: {e}")

    async def get_visit_count(self, page_id: str) -> Dict[str, Any]:
        """
        Get current visit count for a page from Redis 
        
        Args:
            page_id: Unique identifier for the page
            
        Returns:
            Current visit count
        """
        # TODO: Implement getting visit count
        current_time = datetime.now().timestamp()
        if page_id in self.buffer:
            redisValue = await self.redis_manager.get(page_id)
            if redisValue is None:
                redisValue = 0
            bufferValue = self.buffer[page_id]
            self.cache[page_id]={
                "value": bufferValue+int(redisValue),
                "expires_at": current_time
            }
            return {"visits":self.cache[page_id]['value'],"served_via":"Buffer+redis"}   
        else:
            if page_id in self.cache:
                cacheData = self.cache[page_id]    
                if cacheData["expires_at"] > current_time-self.TTL:
                    redisValue = await self.redis_manager.get(page_id)
                    self.cache[page_id]={
                    "value": redisValue,
                    "expires_at": current_time
                }
            else:
                redisValue = await self.redis_manager.get(page_id)
                self.cache[page_id]={
                    "value": redisValue,
                    "expires_at": current_time
                }
            
        return {"visits":self.cache[page_id]['value'],"served_via":"redis+cache"}                   

    async def flush_pending_writes(self):
        """
        Flush buffered writes to Redis once.
        """
        while True:
            await asyncio.sleep(self.flush_interval)
            async with self.lock:
                if not self.buffer:
                    return  
                try:
                    for key, value in self.buffer.items():
                        await self.redis_manager.increment(key, value)
                        print(key,value)
                    self.buffer.clear()  # Clear buffer after successful flush
                    print(self.redis_manager)
                except Exception as e:
                    print(f"Error flushing buffer to Redis: {e}")

