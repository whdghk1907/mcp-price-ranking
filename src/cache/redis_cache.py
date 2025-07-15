"""
Redis 캐시 구현
Redis 기반 분산 캐시 시스템
"""

import asyncio
import json
import pickle
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from src.cache.cache_strategy import CacheStrategy, CacheKey
from src.exceptions import CacheError
from src.utils import setup_logger

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisCache:
    """Redis 캐시 클래스"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 300,
        encoding: str = "utf-8"
    ):
        if not REDIS_AVAILABLE:
            raise CacheError("Redis is not available. Install redis-py: pip install redis")
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = default_ttl
        self.encoding = encoding
        
        self.redis: Optional[redis.Redis] = None
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
    
    async def connect(self) -> None:
        """Redis 연결"""
        try:
            url = f"redis://{self.host}:{self.port}/{self.db}"
            if self.password:
                url = f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
            
            self.redis = redis.from_url(url, encoding=self.encoding, decode_responses=True)
            
            # 연결 테스트
            await self.redis.ping()
            self.logger.info(f"Connected to Redis at {self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {str(e)}")
            raise CacheError(f"Redis connection failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """Redis 연결 해제"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            self.logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # JSON 디코딩 시도
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # JSON이 아닌 경우 그대로 반환
                return value
                
        except Exception as e:
            self.logger.error(f"Failed to get cache key {key}: {str(e)}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """캐시에 데이터 저장"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            # JSON 인코딩
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            ttl = ttl or self.default_ttl
            result = await self.redis.setex(key, ttl, serialized_value)
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Failed to set cache key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            result = await self.redis.delete(key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete cache key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """캐시 키 존재 여부 확인"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            result = await self.redis.exists(key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Failed to check cache key {key}: {str(e)}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """캐시 키 만료 시간 설정"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            result = await self.redis.expire(key, ttl)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Failed to set expiry for cache key {key}: {str(e)}")
            return False
    
    async def ttl(self, key: str) -> int:
        """캐시 키 TTL 조회"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            return await self.redis.ttl(key)
            
        except Exception as e:
            self.logger.error(f"Failed to get TTL for cache key {key}: {str(e)}")
            return -1
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """다중 키 조회"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            values = await self.redis.mget(keys)
            results = []
            
            for value in values:
                if value is None:
                    results.append(None)
                else:
                    try:
                        results.append(json.loads(value))
                    except json.JSONDecodeError:
                        results.append(value)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to mget cache keys: {str(e)}")
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """다중 키 저장"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            # 직렬화
            serialized_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[key] = json.dumps(value, default=str)
                else:
                    serialized_mapping[key] = str(value)
            
            # 저장
            result = await self.redis.mset(serialized_mapping)
            
            # TTL 설정
            if ttl and result:
                ttl = ttl or self.default_ttl
                pipe = self.redis.pipeline()
                for key in mapping.keys():
                    pipe.expire(key, ttl)
                await pipe.execute()
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Failed to mset cache keys: {str(e)}")
            return False
    
    async def scan_iter(self, match: str) -> List[str]:
        """패턴 매칭으로 키 검색"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=match):
                keys.append(key)
            return keys
            
        except Exception as e:
            self.logger.error(f"Failed to scan keys with pattern {match}: {str(e)}")
            return []
    
    async def flushdb(self) -> bool:
        """현재 DB의 모든 키 삭제"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            await self.redis.flushdb()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to flush database: {str(e)}")
            return False
    
    async def ping(self) -> bool:
        """Redis 연결 상태 확인"""
        if not self.redis:
            return False
        
        try:
            result = await self.redis.ping()
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Redis ping failed: {str(e)}")
            return False
    
    async def info(self) -> Dict[str, Any]:
        """Redis 서버 정보 조회"""
        if not self.redis:
            raise CacheError("Redis not connected")
        
        try:
            return await self.redis.info()
            
        except Exception as e:
            self.logger.error(f"Failed to get Redis info: {str(e)}")
            return {}


class RedisCacheManager:
    """Redis 캐시 매니저"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 300,
        max_connections: int = 20
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_connections = max_connections
        
        self.cache: Optional[RedisCache] = None
        self.strategy = CacheStrategy()
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        self._connected = False
    
    async def connect(self) -> None:
        """캐시 연결"""
        if self._connected:
            return
        
        try:
            # URL 파싱
            if self.redis_url.startswith("redis://"):
                url_parts = self.redis_url.replace("redis://", "").split("/")
                host_port = url_parts[0].split(":")
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                db = int(url_parts[1]) if len(url_parts) > 1 else 0
            else:
                host, port, db = "localhost", 6379, 0
            
            self.cache = RedisCache(
                host=host,
                port=port,
                db=db,
                default_ttl=self.default_ttl
            )
            
            await self.cache.connect()
            self._connected = True
            self.logger.info("Cache manager connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect cache manager: {str(e)}")
            raise CacheError(f"Cache manager connection failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """캐시 연결 해제"""
        if self.cache:
            await self.cache.disconnect()
            self.cache = None
            self._connected = False
            self.logger.info("Cache manager disconnected")
    
    async def get_ranking_cache(
        self,
        ranking_type: str,
        market: str,
        count: int,
        **filters
    ) -> Optional[List[Dict[str, Any]]]:
        """순위 캐시 조회"""
        if not self._connected:
            await self.connect()
        
        cache_key = self.strategy.generate_ranking_key(
            ranking_type, market, count, **filters
        )
        
        return await self.cache.get(cache_key.full_key)
    
    async def set_ranking_cache(
        self,
        ranking_type: str,
        market: str,
        count: int,
        data: List[Dict[str, Any]],
        **filters
    ) -> bool:
        """순위 캐시 저장"""
        if not self._connected:
            await self.connect()
        
        cache_key = self.strategy.generate_ranking_key(
            ranking_type, market, count, **filters
        )
        
        return await self.cache.set(cache_key.full_key, data, cache_key.ttl)
    
    async def get_high_low_cache(
        self,
        type_param: str,
        market: str,
        count: int,
        breakthrough_only: bool
    ) -> Optional[Dict[str, Any]]:
        """52주 고저가 캐시 조회"""
        if not self._connected:
            await self.connect()
        
        cache_key = self.strategy.generate_high_low_key(
            type_param, market, count, breakthrough_only
        )
        
        return await self.cache.get(cache_key.full_key)
    
    async def set_high_low_cache(
        self,
        type_param: str,
        market: str,
        count: int,
        breakthrough_only: bool,
        data: Dict[str, Any]
    ) -> bool:
        """52주 고저가 캐시 저장"""
        if not self._connected:
            await self.connect()
        
        cache_key = self.strategy.generate_high_low_key(
            type_param, market, count, breakthrough_only
        )
        
        return await self.cache.set(cache_key.full_key, data, cache_key.ttl)
    
    async def get_limit_cache(
        self,
        limit_type: str,
        market: str,
        include_history: bool
    ) -> Optional[Dict[str, Any]]:
        """상한가/하한가 캐시 조회"""
        if not self._connected:
            await self.connect()
        
        cache_key = self.strategy.generate_limit_key(
            limit_type, market, include_history
        )
        
        return await self.cache.get(cache_key.full_key)
    
    async def set_limit_cache(
        self,
        limit_type: str,
        market: str,
        include_history: bool,
        data: Dict[str, Any]
    ) -> bool:
        """상한가/하한가 캐시 저장"""
        if not self._connected:
            await self.connect()
        
        cache_key = self.strategy.generate_limit_key(
            limit_type, market, include_history
        )
        
        return await self.cache.set(cache_key.full_key, data, cache_key.ttl)
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """다중 키 조회"""
        if not self._connected:
            await self.connect()
        
        return await self.cache.mget(keys)
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """다중 키 저장"""
        if not self._connected:
            await self.connect()
        
        return await self.cache.mset(mapping, ttl)
    
    async def delete_pattern(self, pattern: str) -> int:
        """패턴으로 키 삭제"""
        if not self._connected:
            await self.connect()
        
        keys = await self.cache.scan_iter(pattern)
        if keys:
            # 배치로 삭제
            delete_count = 0
            for key in keys:
                if await self.cache.delete(key):
                    delete_count += 1
            return delete_count
        return 0
    
    async def invalidate_market_cache(self) -> int:
        """시장 데이터 캐시 무효화"""
        patterns = [
            "ranking:*",
            "high_low:*", 
            "limit:*",
            "market_summary:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.delete_pattern(pattern)
            total_deleted += deleted
        
        self.logger.info(f"Invalidated {total_deleted} market cache entries")
        return total_deleted
    
    async def health_check(self) -> Dict[str, Any]:
        """캐시 헬스 체크"""
        if not self._connected:
            return {
                "status": "disconnected",
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Ping 테스트
            ping_result = await self.cache.ping()
            
            # 서버 정보 조회
            info = await self.cache.info()
            
            # 메모리 사용량 계산
            used_memory = info.get("used_memory", 0)
            maxmemory = info.get("maxmemory", 0)
            
            # 히트율 계산
            keyspace_hits = info.get("keyspace_hits", 0)
            keyspace_misses = info.get("keyspace_misses", 0)
            total_requests = keyspace_hits + keyspace_misses
            hit_rate = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "status": "healthy" if ping_result else "unhealthy",
                "connected": ping_result,
                "memory_usage": used_memory,
                "max_memory": maxmemory,
                "memory_usage_percent": (used_memory / maxmemory * 100) if maxmemory > 0 else 0,
                "hit_rate": round(hit_rate, 2),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """메모리 사용량 조회"""
        if not self._connected:
            await self.connect()
        
        info = await self.cache.info()
        
        used_memory = info.get("used_memory", 0)
        used_memory_peak = info.get("used_memory_peak", 0)
        maxmemory = info.get("maxmemory", 0)
        
        return {
            "used_memory_mb": round(used_memory / 1024 / 1024, 2),
            "peak_memory_mb": round(used_memory_peak / 1024 / 1024, 2),
            "max_memory_mb": round(maxmemory / 1024 / 1024, 2) if maxmemory > 0 else None,
            "memory_usage_percent": round((used_memory / maxmemory * 100), 2) if maxmemory > 0 else None,
            "timestamp": datetime.now().isoformat()
        }