# server/app/services/worker/redis_label_cache.py
"""
Redis Label Cache Service
Stores and retrieves email labels per account using Redis Database 1.
"""

import redis
import json
from typing import List, Optional
from app.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RedisLabelCache:
    """
    Redis-based cache for storing email labels per account.
    Uses Redis Database 1 (separate from Celery's Database 0).
    """
    
    def __init__(self):
        """
        Initialize Redis connection for label cache (Database 1).
        """
        self.redis_client: Optional[redis.Redis] = None
        self._initialize_redis()
    
    def _initialize_redis(self) -> redis.Redis:
        """
        Create and initialize Redis client object.
        
        Returns:
            Redis client instance
        """
        try:
            # Get Redis cache URL from config
            redis_url = settings.REDIS_CACHE_URL
            
            if not redis_url:
                raise ValueError(
                    "REDIS_CACHE_URL not configured. "
                    "Please set it in your .env file."
                )
            
            # Create Redis client object
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            
            logger.info(f"✓ Redis label cache connected (Database 1)")
            return self.redis_client
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis for label cache: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing Redis for label cache: {e}")
            raise
    
    def _get_key(self, account_id: str) -> str:
        """
        Generate Redis key for account labels (internal helper).
        
        Args:
            account_id: Gmail account UUID
        
        Returns:
            Redis key string
        """
        return f"labels:account:{account_id}"
    
    def get_labels(self, account_id: str) -> List[str]:
        """
        Get cached labels for an account.
        
        Args:
            account_id: Gmail account UUID (as string)
        
        Returns:
            List of label names, empty list if not found
        """
        try:
            if not self.redis_client:
                logger.error("Redis client not initialized")
                return []
            
            key = self._get_key(account_id)
            cached_data = self.redis_client.get(key)
            
            if not cached_data:
                logger.debug(f"No cached labels found for account {account_id}")
                return []
            
            # Parse JSON data
            data = json.loads(cached_data)
            labels = data.get("labels", [])
            
            logger.debug(f"Retrieved {len(labels)} labels from cache for account {account_id}")
            return labels
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse cached labels for account {account_id}: {e}")
            return []
        except redis.RedisError as e:
            logger.error(f"Redis error getting labels for account {account_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting labels for account {account_id}: {e}")
            return []
    
    def set_labels(
        self, 
        account_id: str, 
        labels: List[str], 
        ttl: int = 3600
    ) -> bool:
        """
        Cache labels for an account.
        
        Args:
            account_id: Gmail account UUID (as string)
            labels: List of label names
            ttl: Time to live in seconds (default: 1 hour)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                logger.error("Redis client not initialized")
                return False
            
            key = self._get_key(account_id)
            
            # Prepare data structure
            data = {
                "labels": labels,
                "last_synced": datetime.utcnow().isoformat(),
                "source": "gmail"
            }
            
            # Store in Redis with TTL
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(data)
            )
            
            logger.info(f"Cached {len(labels)} labels for account {account_id} (TTL: {ttl}s)")
            logger.info(f"Labels cached: {labels}") 
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error setting labels for account {account_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting labels for account {account_id}: {e}")
            return False
    
    def add_label(self, account_id: str, label: str, ttl: int = 3600) -> bool:
        """
        Add a single label to cache (or create cache if doesn't exist).
        
        Args:
            account_id: Gmail account UUID
            label: Label name to add
            ttl: Time to live in seconds
        
        Returns:
            True if successful
        """
        try:
            # Get existing labels
            existing_labels = self.get_labels(account_id)
            
            # Add new label if not already present (case-insensitive)
            label_lower = label.lower().strip()
            if label_lower not in [l.lower() for l in existing_labels]:
                existing_labels.append(label)
                return self.set_labels(account_id, existing_labels, ttl)
            
            logger.debug(f"Label '{label}' already exists for account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding label {label} for account {account_id}: {e}")
            return False
    
    def remove_label(self, account_id: str, label: str) -> bool:
        """
        Remove a label from cache.
        
        Args:
            account_id: Gmail account UUID
            label: Label name to remove
        
        Returns:
            True if successful
        """
        try:
            existing_labels = self.get_labels(account_id)
            
            # Remove label (case-insensitive)
            label_lower = label.lower()
            updated_labels = [l for l in existing_labels if l.lower() != label_lower]
            
            if len(updated_labels) != len(existing_labels):
                # Label was removed, update cache
                if updated_labels:
                    return self.set_labels(account_id, updated_labels)
                else:
                    # No labels left, invalidate cache
                    return self.invalidate(account_id)
            
            logger.debug(f"Label '{label}' not found for account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing label {label} for account {account_id}: {e}")
            return False
    
    def invalidate(self, account_id: str) -> bool:
        """
        Remove cached labels for an account.
        Use this when labels are updated in Gmail.
        
        Args:
            account_id: Gmail account UUID
        
        Returns:
            True if successful
        """
        try:
            if not self.redis_client:
                logger.error("Redis client not initialized")
                return False
            
            key = self._get_key(account_id)
            deleted = self.redis_client.delete(key)
            
            if deleted:
                logger.info(f"Invalidated label cache for account {account_id}")
            else:
                logger.debug(f"No cache to invalidate for account {account_id}")
            
            return bool(deleted)
            
        except redis.RedisError as e:
            logger.error(f"Redis error invalidating cache for account {account_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error invalidating cache for account {account_id}: {e}")
            return False