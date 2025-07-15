"""
프로젝트 구조 검증 테스트
TDD: 먼저 테스트를 작성하여 프로젝트 구조가 올바르게 설정되었는지 확인
"""
import os
import pytest
from pathlib import Path


class TestProjectStructure:
    """프로젝트 구조 테스트"""
    
    def test_root_directory_exists(self):
        """루트 디렉토리 존재 확인"""
        root_path = Path(__file__).parent.parent
        assert root_path.exists()
        assert root_path.is_dir()
    
    def test_src_directory_structure(self):
        """src 디렉토리 구조 테스트"""
        root_path = Path(__file__).parent.parent
        src_path = root_path / "src"
        
        # src 디렉토리가 존재해야 함
        assert src_path.exists()
        assert src_path.is_dir()
        
        # 필수 서브디렉토리들이 존재해야 함
        required_dirs = ["tools", "api", "analysis", "utils"]
        for dir_name in required_dirs:
            dir_path = src_path / dir_name
            assert dir_path.exists(), f"{dir_name} directory should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"
    
    def test_required_files_exist(self):
        """필수 파일들 존재 확인"""
        root_path = Path(__file__).parent.parent
        src_path = root_path / "src"
        
        # 필수 Python 파일들
        required_files = [
            "src/__init__.py",
            "src/server.py",
            "src/config.py",
            "src/exceptions.py",
            "src/tools/__init__.py",
            "src/api/__init__.py",
            "src/analysis/__init__.py",
            "src/utils/__init__.py",
        ]
        
        for file_path in required_files:
            full_path = root_path / file_path
            assert full_path.exists(), f"{file_path} should exist"
            assert full_path.is_file(), f"{file_path} should be a file"
    
    def test_config_files_exist(self):
        """설정 파일들 존재 확인"""
        root_path = Path(__file__).parent.parent
        
        config_files = [
            "requirements.txt",
            ".env.example",
            "README.md"
        ]
        
        for file_name in config_files:
            file_path = root_path / file_name
            assert file_path.exists(), f"{file_name} should exist"
            assert file_path.is_file(), f"{file_name} should be a file"
    
    def test_tests_directory_structure(self):
        """테스트 디렉토리 구조 확인"""
        root_path = Path(__file__).parent.parent
        tests_path = root_path / "tests"
        
        assert tests_path.exists()
        assert tests_path.is_dir()
        
        # __init__.py 파일이 있어야 함
        init_file = tests_path / "__init__.py"
        assert init_file.exists()


class TestRequirements:
    """requirements.txt 테스트"""
    
    def test_requirements_file_format(self):
        """requirements.txt 파일 형식 확인"""
        root_path = Path(__file__).parent.parent
        req_file = root_path / "requirements.txt"
        
        assert req_file.exists()
        
        with open(req_file, 'r') as f:
            content = f.read()
            
        # 기본 패키지들이 포함되어 있어야 함
        required_packages = [
            "mcp",
            "aiohttp",
            "pandas",
            "numpy",
            "pydantic",
            "pytest",
            "pytest-asyncio"
        ]
        
        for package in required_packages:
            assert package in content, f"{package} should be in requirements.txt"


class TestEnvironmentConfig:
    """환경 설정 테스트"""
    
    def test_env_example_exists(self):
        """.env.example 파일 존재 확인"""
        root_path = Path(__file__).parent.parent
        env_example = root_path / ".env.example"
        
        assert env_example.exists()
        
        with open(env_example, 'r') as f:
            content = f.read()
            
        # 필수 환경 변수들이 정의되어 있어야 함
        required_vars = [
            "KOREA_INVESTMENT_APP_KEY",
            "KOREA_INVESTMENT_APP_SECRET",
            "CACHE_TTL_SECONDS",
            "LOG_LEVEL"
        ]
        
        for var in required_vars:
            assert var in content, f"{var} should be defined in .env.example"