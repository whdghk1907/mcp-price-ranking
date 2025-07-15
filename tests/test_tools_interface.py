"""
MCP 도구 인터페이스 테스트
TDD: 도구 인터페이스와 레지스트리 기능 테스트
"""
import pytest
from src.tools import BaseTool, ToolRegistry, tool_registry
from src.exceptions import ToolExecutionError


class MockTool(BaseTool):
    """테스트용 모킹 도구"""
    
    def __init__(self):
        super().__init__("mock_tool", "Mock tool for testing")
    
    async def execute(self, **kwargs):
        """모킹 실행"""
        return {
            "tool_name": self.name,
            "parameters": kwargs,
            "result": "mock_result"
        }
    
    def _get_parameters_schema(self):
        """모킹 파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Test parameter 1"},
                "param2": {"type": "integer", "description": "Test parameter 2"}
            },
            "required": ["param1"]
        }


class ErrorTool(BaseTool):
    """에러 발생 테스트용 도구"""
    
    def __init__(self):
        super().__init__("error_tool", "Tool that throws errors")
    
    async def execute(self, **kwargs):
        """에러 발생"""
        raise ToolExecutionError("Test error", tool_name=self.name, parameters=kwargs)
    
    def _get_parameters_schema(self):
        return {"type": "object", "properties": {}}


class TestBaseTool:
    """BaseTool 테스트"""
    
    def test_tool_creation(self):
        """도구 생성 테스트"""
        tool = MockTool()
        
        assert tool.name == "mock_tool"
        assert tool.description == "Mock tool for testing"
        assert tool.validate_parameters() is True
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """도구 실행 테스트"""
        tool = MockTool()
        
        result = await tool.execute(param1="test", param2=123)
        
        assert result["tool_name"] == "mock_tool"
        assert result["parameters"]["param1"] == "test"
        assert result["parameters"]["param2"] == 123
        assert result["result"] == "mock_result"
    
    def test_tool_schema(self):
        """도구 스키마 테스트"""
        tool = MockTool()
        schema = tool.get_schema()
        
        assert schema["name"] == "mock_tool"
        assert schema["description"] == "Mock tool for testing"
        assert "parameters" in schema
        assert schema["parameters"]["type"] == "object"
        assert "param1" in schema["parameters"]["properties"]
        assert "param2" in schema["parameters"]["properties"]
        assert "param1" in schema["parameters"]["required"]
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """도구 에러 처리 테스트"""
        tool = ErrorTool()
        
        with pytest.raises(ToolExecutionError) as exc_info:
            await tool.execute(test_param="value")
        
        error = exc_info.value
        assert error.tool_name == "error_tool"
        assert error.parameters["test_param"] == "value"
        assert "Test error" in str(error)


class TestToolRegistry:
    """ToolRegistry 테스트"""
    
    @pytest.fixture
    def registry(self):
        """테스트용 레지스트리"""
        return ToolRegistry()
    
    def test_registry_creation(self, registry):
        """레지스트리 생성 테스트"""
        assert len(registry.list_tools()) == 0
        assert registry.get_tool("nonexistent") is None
    
    def test_tool_registration(self, registry):
        """도구 등록 테스트"""
        tool = MockTool()
        
        registry.register(tool)
        
        assert "mock_tool" in registry.list_tools()
        assert registry.get_tool("mock_tool") is tool
        assert len(registry.list_tools()) == 1
    
    def test_multiple_tool_registration(self, registry):
        """여러 도구 등록 테스트"""
        tool1 = MockTool()
        tool2 = ErrorTool()
        
        registry.register(tool1)
        registry.register(tool2)
        
        tools = registry.list_tools()
        assert "mock_tool" in tools
        assert "error_tool" in tools
        assert len(tools) == 2
    
    def test_tool_overwrite(self, registry):
        """도구 덮어쓰기 테스트"""
        tool1 = MockTool()
        tool2 = MockTool()  # 같은 이름의 다른 인스턴스
        
        registry.register(tool1)
        registry.register(tool2)
        
        # 두 번째 도구로 덮어써짐
        assert registry.get_tool("mock_tool") is tool2
        assert len(registry.list_tools()) == 1
    
    def test_get_all_schemas(self, registry):
        """모든 스키마 조회 테스트"""
        tool1 = MockTool()
        tool2 = ErrorTool()
        
        registry.register(tool1)
        registry.register(tool2)
        
        schemas = registry.get_all_schemas()
        
        assert len(schemas) == 2
        schema_names = [schema["name"] for schema in schemas]
        assert "mock_tool" in schema_names
        assert "error_tool" in schema_names


class TestGlobalRegistry:
    """전역 레지스트리 테스트"""
    
    def test_global_registry_exists(self):
        """전역 레지스트리 존재 확인"""
        assert tool_registry is not None
        assert isinstance(tool_registry, ToolRegistry)
    
    def test_global_registry_functionality(self):
        """전역 레지스트리 기능 테스트"""
        # 초기 상태 확인
        initial_count = len(tool_registry.list_tools())
        
        # 도구 등록
        tool = MockTool()
        tool_registry.register(tool)
        
        # 등록 확인
        assert len(tool_registry.list_tools()) == initial_count + 1
        assert tool_registry.get_tool("mock_tool") is tool
        
        # 정리 (다른 테스트에 영향 주지 않도록)
        tool_registry._tools.pop("mock_tool", None)


class TestToolValidation:
    """도구 검증 테스트"""
    
    def test_parameter_validation_default(self):
        """기본 파라미터 검증 테스트"""
        tool = MockTool()
        
        # 기본 구현은 항상 True 반환
        assert tool.validate_parameters() is True
        assert tool.validate_parameters(param1="test") is True
        assert tool.validate_parameters(invalid_param=123) is True
    
    @pytest.mark.asyncio
    async def test_tool_execution_with_invalid_params(self):
        """잘못된 파라미터로 도구 실행"""
        tool = MockTool()
        
        # BaseTool은 파라미터 검증을 강제하지 않음
        # 실제 구현에서는 각 도구가 자체적으로 검증
        result = await tool.execute(invalid_param="test")
        
        assert result["tool_name"] == "mock_tool"
        assert result["parameters"]["invalid_param"] == "test"