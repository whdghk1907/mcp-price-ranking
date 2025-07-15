"""
Redis 캐시 시스템 테스트
TDD: Redis 기반 분산 캐시 시스템 구현 및 테스트
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from src.cache.redis_cache import RedisCache, RedisCacheManager
from src.cache.cache_strategy import CacheStrategy, CacheKey
from src.exceptions import CacheError


class TestRedisCache:
    """Redis 캐시 기본 테스트"""
    
    @pytest.fixture
    def cache(self):
        """Redis 캐시 인스턴스"""
        return RedisCache(
            host="localhost",
            port=6379,
            db=0,
            password=None,
            default_ttl=300
        )
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, cache):
        """캐시 초기화 테스트"""
        assert cache.host == "localhost"
        assert cache.port == 6379
        assert cache.db == 0
        assert cache.default_ttl == 300
        assert cache.redis is None  # 연결 전
    
    @pytest.mark.asyncio
    async def test_cache_connection(self, cache):
        """캐시 연결 테스트"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            
            await cache.connect()
            
            assert cache.redis is not None
            mock_redis_instance.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache):
        """캐시 저장/조회 테스트"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            
            # 연결
            await cache.connect()
            
            # 데이터 저장
            test_data = {"stock_code": "005930", "price": 78500}
            key = "test:stock:005930"
            
            # set 메서드 모킹
            mock_redis_instance.setex.return_value = True
            await cache.set(key, test_data, ttl=300)
            
            # 데이터 조회
            mock_redis_instance.get.return_value = json.dumps(test_data).encode()
            result = await cache.get(key)
            
            assert result == test_data
            mock_redis_instance.setex.assert_called_once()
            mock_redis_instance.get.assert_called_once_with(key)
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache):
        """캐시 삭제 테스트"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            
            await cache.connect()
            
            key = "test:stock:005930"
            mock_redis_instance.delete.return_value = 1
            
            result = await cache.delete(key)
            
            assert result is True
            mock_redis_instance.delete.assert_called_once_with(key)
    
    @pytest.mark.asyncio
    async def test_cache_exists(self, cache):
        """캐시 존재 확인 테스트"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            
            await cache.connect()
            
            key = "test:stock:005930"
            mock_redis_instance.exists.return_value = 1
            
            result = await cache.exists(key)
            
            assert result is True
            mock_redis_instance.exists.assert_called_once_with(key)
    
    @pytest.mark.asyncio
    async def test_cache_expire(self, cache):
        """캐시 만료 시간 설정 테스트"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            
            await cache.connect()
            
            key = "test:stock:005930"
            ttl = 600
            mock_redis_instance.expire.return_value = True
            
            result = await cache.expire(key, ttl)
            
            assert result is True
            mock_redis_instance.expire.assert_called_once_with(key, ttl)
    
    @pytest.mark.asyncio
    async def test_cache_connection_error_handling(self, cache):
        """캐시 연결 오류 처리 테스트"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            with pytest.raises(CacheError):
                await cache.connect()
    
    @pytest.mark.asyncio
    async def test_cache_get_nonexistent_key(self, cache):
        """존재하지 않는 키 조회 테스트"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.get.return_value = None
            
            await cache.connect()
            
            result = await cache.get("nonexistent:key")
            
            assert result is None


class TestCacheStrategy:
    """캐시 전략 테스트"""
    
    def test_cache_key_generation(self):
        """캐시 키 생성 테스트"""
        strategy = CacheStrategy()
        
        # 주식 순위 키
        cache_key = strategy.generate_ranking_key("TOP_GAINERS", "KOSPI", count=20)
        assert cache_key.prefix == "ranking"
        assert "TOP_GAINERS" in cache_key.full_key
        assert "KOSPI" in cache_key.full_key
        
        # 52주 고저가 키
        cache_key = strategy.generate_high_low_key("HIGH", "ALL", breakthrough_only=True)
        assert cache_key.prefix == "high_low"
        assert "HIGH" in cache_key.full_key
        assert "ALL" in cache_key.full_key
        
        # 상한가/하한가 키
        cache_key = strategy.generate_limit_key("UPPER", "KOSPI")
        assert cache_key.prefix == "limit"
        assert "UPPER" in cache_key.full_key
        assert "KOSPI" in cache_key.full_key
    
    def test_cache_ttl_calculation(self):
        """캐시 TTL 계산 테스트"""
        strategy = CacheStrategy()
        
        # 시장 시간 내
        market_hours_ttl = strategy.get_ttl_for_market_hours()
        assert market_hours_ttl <= 60  # 1분 이하
        
        # 시장 시간 외
        after_hours_ttl = strategy.get_ttl_for_after_hours()
        assert after_hours_ttl >= 300  # 5분 이상
    
    def test_cache_invalidation_rules(self):
        """캐시 무효화 규칙 테스트"""
        strategy = CacheStrategy()
        
        # 시간 기반 무효화
        should_invalidate = strategy.should_invalidate_by_time(
            cache_time=datetime.now() - timedelta(minutes=10),
            max_age_minutes=5
        )
        assert should_invalidate is True
        
        # 이벤트 기반 무효화
        should_invalidate = strategy.should_invalidate_by_event("market_open")
        assert should_invalidate is True


class TestRedisCacheManager:
    """Redis 캐시 매니저 테스트"""
    
    @pytest.fixture
    def cache_manager(self):
        """캐시 매니저 인스턴스"""
        return RedisCacheManager(
            redis_url="redis://localhost:6379/0",
            default_ttl=300,
            max_connections=20
        )
    
    @pytest.mark.asyncio
    async def test_cache_manager_initialization(self, cache_manager):
        """캐시 매니저 초기화 테스트"""
        assert cache_manager.redis_url == "redis://localhost:6379/0"
        assert cache_manager.default_ttl == 300
        assert cache_manager.max_connections == 20
    
    @pytest.mark.asyncio
    async def test_cache_manager_ranking_operations(self, cache_manager):
        """순위 데이터 캐시 작업 테스트"""
        # Mock RedisCache를 만들어서 할당
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        cache_manager.cache = mock_cache
        cache_manager._connected = True
        
        # 캐시 미스
        result = await cache_manager.get_ranking_cache("TOP_GAINERS", "KOSPI", 20)
        assert result is None
        
        # 캐시 저장
        test_data = [{"stock_code": "005930", "rank": 1}]
        await cache_manager.set_ranking_cache("TOP_GAINERS", "KOSPI", 20, test_data)
        
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_manager_bulk_operations(self, cache_manager):
        """대량 캐시 작업 테스트"""
        # Mock RedisCache를 만들어서 할당
        mock_cache = AsyncMock()
        mock_cache.mget.return_value = [None, None, None]
        mock_cache.mset.return_value = True
        cache_manager.cache = mock_cache
        cache_manager._connected = True
        
        # 대량 조회
        keys = ["key1", "key2", "key3"]
        results = await cache_manager.mget(keys)
        assert len(results) == 3
        
        # 대량 저장
        data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        await cache_manager.mset(data, ttl=300)
        
        mock_cache.mset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_manager_pattern_operations(self, cache_manager):
        """패턴 기반 캐시 작업 테스트"""
        # Mock RedisCache를 만들어서 할당
        mock_cache = AsyncMock()
        mock_cache.scan_iter.return_value = ["ranking:TOP_GAINERS:KOSPI", "ranking:TOP_LOSERS:KOSPI"]
        mock_cache.delete.return_value = 2
        cache_manager.cache = mock_cache
        cache_manager._connected = True
        
        # 패턴으로 키 삭제
        deleted_count = await cache_manager.delete_pattern("ranking:*:KOSPI")
        assert deleted_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_manager_health_check(self, cache_manager):
        """캐시 매니저 헬스 체크 테스트"""
        # Mock RedisCache를 만들어서 할당
        mock_cache = AsyncMock()
        mock_cache.ping.return_value = True
        mock_cache.info.return_value = {
            "connected_clients": 10,
            "used_memory": 1024000,
            "keyspace_hits": 1000,
            "keyspace_misses": 100
        }
        cache_manager.cache = mock_cache
        cache_manager._connected = True
        
        health = await cache_manager.health_check()
        
        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert "memory_usage" in health
        assert "hit_rate" in health


class TestCacheIntegration:
    """캐시 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_tool_cache_integration(self):
        """도구 캐시 통합 테스트 (캐시 기능 구현 시 활성화)"""
        # TODO: 도구에 캐시 기능 구현 후 테스트 활성화
        # 현재는 캐시 매니저 기본 기능만 테스트
        cache_manager = RedisCacheManager()
        
        # Mock RedisCache를 만들어서 할당
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        cache_manager.cache = mock_cache
        cache_manager._connected = True
        
        # 기본 캐시 연산 테스트
        result = await cache_manager.get_ranking_cache("TOP_GAINERS", "KOSPI", 20)
        assert result is None
        
        test_data = [{"stock_code": "005930", "rank": 1}]
        success = await cache_manager.set_ranking_cache("TOP_GAINERS", "KOSPI", 20, test_data)
        assert success is True
    
    @pytest.mark.asyncio
    async def test_cache_hit_scenario(self):
        """캐시 히트 시나리오 테스트 (캐시 기능 구현 시 활성화)"""
        # TODO: 도구에 캐시 기능 구현 후 테스트 활성화
        # 현재는 캐시 매니저 기본 기능만 테스트
        cache_manager = RedisCacheManager()
        
        # Mock RedisCache를 만들어서 할당
        mock_cache = AsyncMock()
        cached_data = [{"rank": 1, "stock_code": "005930", "stock_name": "삼성전자"}]
        mock_cache.get.return_value = cached_data
        cache_manager.cache = mock_cache
        cache_manager._connected = True
        
        # 캐시 히트 테스트
        result = await cache_manager.get_ranking_cache("TOP_GAINERS", "KOSPI", 20)
        assert result == cached_data
    
    @pytest.mark.asyncio 
    async def test_cache_invalidation_on_market_events(self):
        """시장 이벤트에 따른 캐시 무효화 테스트"""
        cache_manager = RedisCacheManager()
        
        # Mock RedisCache를 만들어서 할당
        mock_cache = AsyncMock()
        mock_cache.scan_iter.return_value = [
            "ranking:TOP_GAINERS:KOSPI",
            "ranking:TOP_LOSERS:KOSPI", 
            "high_low:HIGH:ALL"
        ]
        mock_cache.delete.return_value = 3
        cache_manager.cache = mock_cache
        cache_manager._connected = True
        
        # 시장 개장 이벤트로 캐시 무효화
        await cache_manager.invalidate_market_cache()
        
        # 관련 키들이 삭제되었는지 확인
        mock_cache.scan_iter.assert_called()
        mock_cache.delete.assert_called()


class TestCachePerformance:
    """캐시 성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """동시 캐시 작업 테스트"""
        cache_manager = RedisCacheManager()
        
        with patch.object(cache_manager, 'cache') as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True
            
            # 동시 캐시 작업
            tasks = []
            for i in range(100):
                task = cache_manager.get_ranking_cache("TOP_GAINERS", "KOSPI", 20)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # 모든 작업이 완료되었는지 확인
            assert len(results) == 100
            assert all(result is None for result in results)
    
    @pytest.mark.asyncio
    async def test_cache_memory_usage(self):
        """캐시 메모리 사용량 테스트"""
        cache_manager = RedisCacheManager()
        
        # Mock RedisCache를 만들어서 할당
        mock_cache = AsyncMock()
        mock_cache.info.return_value = {
            "used_memory": 1048576,  # 정확히 1MB
            "used_memory_peak": 2097152,  # 정확히 2MB
            "maxmemory": 134217728  # 128MB
        }
        cache_manager.cache = mock_cache
        cache_manager._connected = True
        
        memory_info = await cache_manager.get_memory_usage()
        
        assert memory_info["used_memory_mb"] == 1.0
        assert memory_info["peak_memory_mb"] == 2.0
        assert memory_info["memory_usage_percent"] < 100