"""
MCP Price Ranking Server 메인 실행 파일
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.server import PriceRankingMCPServer, create_server
from src.tools.basic_tools import HealthCheckTool, InfoTool, EchoTool
from src.tools.integrated_price_tool import IntegratedPriceRankingTool
from src.tools import tool_registry
from src.config import config
from src.utils import setup_logger


async def setup_tools():
    """도구 설정 및 등록"""
    logger = setup_logger("main.setup_tools")
    
    # 기본 도구들 등록
    basic_tools = [
        HealthCheckTool(),
        InfoTool(),
        EchoTool()
    ]
    
    for tool in basic_tools:
        tool_registry.register(tool)
        logger.info(f"Registered basic tool: {tool.name}")
    
    # 통합 가격 순위 도구 등록
    try:
        integrated_tool = IntegratedPriceRankingTool()
        tool_registry.register(integrated_tool)
        logger.info(f"Registered integrated tool: {integrated_tool.name}")
    except Exception as e:
        logger.error(f"Failed to register integrated tool: {str(e)}")
    
    return tool_registry


async def demo_run():
    """데모 실행"""
    logger = setup_logger("main.demo_run")
    
    # 서버 생성
    server = create_server()
    logger.info("Created MCP server")
    
    # 도구 설정
    tools = await setup_tools()
    logger.info(f"Registered {len(tools.list_tools())} tools")
    
    # 서버에 도구 등록
    for tool_name in tools.list_tools():
        tool = tools.get_tool(tool_name)
        if tool:
            server.register_tool(tool_name, tool.execute)
    
    # 서버 시작
    await server.start()
    
    try:
        # 데모 실행
        logger.info("=== MCP Price Ranking Server Demo ===")
        
        # 1. 헬스체크
        print("\n1. Health Check:")
        health_tool = tools.get_tool("health_check")
        health_result = await health_tool.execute()
        print(f"   Status: {health_result['status']}")
        print(f"   Uptime: {health_result['uptime']:.2f}s")
        
        # 2. 서버 정보
        print("\n2. Server Info:")
        info_tool = tools.get_tool("get_server_info")
        info_result = await info_tool.execute()
        print(f"   Server: {info_result['server_name']}")
        print(f"   Version: {info_result['version']}")
        print(f"   Available tools: {len(info_result['available_tools'])}")
        
        # 3. 에코 테스트
        print("\n3. Echo Test:")
        echo_tool = tools.get_tool("echo")
        echo_result = await echo_tool.execute(message="Hello, MCP Price Ranking!")
        print(f"   Echo: {echo_result['echo']}")
        
        # 4. 가격 순위 도구 테스트 (모킹 모드)
        print("\n4. Price Ranking Test (Mock Mode):")
        ranking_tool = tools.get_tool("get_price_change_ranking")
        if ranking_tool:
            try:
                ranking_result = await ranking_tool.execute(
                    ranking_type="TOP_GAINERS",
                    market="KOSPI",
                    count=3
                )
                print(f"   Ranking Type: {ranking_result['ranking_type']}")
                print(f"   Market: {ranking_result['market']}")
                print(f"   Count: {ranking_result['count']}")
                print(f"   Data Source: {ranking_result.get('data_source', 'Mock')}")
                
                if ranking_result.get('ranking'):
                    print("   Top 3 stocks:")
                    for i, stock in enumerate(ranking_result['ranking'][:3], 1):
                        print(f"     {i}. {stock['stock_name']} ({stock['stock_code']}) - {stock['change_rate']:.2f}%")
                
            except Exception as e:
                print(f"   Error: {str(e)}")
                print("   Note: This is expected without real API credentials")
        
        # 5. 서버 상태 확인
        print("\n5. Server Status:")
        server_health = await server.health_check()
        print(f"   Server Status: {server_health['status']}")
        print(f"   Registered Tools: {len(server_health['registered_tools'])}")
        
        print("\n=== Demo Complete ===")
        print("The MCP Price Ranking Server is ready for use!")
        print("Available tools:", ", ".join(tools.list_tools()))
        
    except Exception as e:
        logger.error(f"Demo error: {str(e)}")
        
    finally:
        # 정리
        await server.stop()
        
        # 통합 도구 정리
        integrated_tool = tools.get_tool("get_price_change_ranking")
        if integrated_tool and hasattr(integrated_tool, 'cleanup'):
            await integrated_tool.cleanup()
        
        logger.info("Demo completed and cleaned up")


async def main():
    """메인 함수"""
    logger = setup_logger("main")
    
    try:
        logger.info("Starting MCP Price Ranking Server")
        
        # 설정 확인
        logger.info(f"API Base URL: {config.api.base_url}")
        logger.info(f"Server Name: {config.server.name}")
        logger.info(f"Cache TTL: {config.cache.ttl_seconds}s")
        
        # 데모 실행
        await demo_run()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())