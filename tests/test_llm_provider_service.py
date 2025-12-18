"""
Nano Banana Studio Pro - LLM Provider Service Tests
====================================================
Comprehensive test coverage for LLMProviderService.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestLLMProviderService:
    """Tests for LLMProviderService"""
    
    def test_init(self):
        """Test service initialization"""
        from backend.services.llm_provider_service import LLMProviderService
        service = LLMProviderService()
        assert service is not None
    
    @pytest.mark.asyncio
    async def test_complete_with_openai(self):
        """Test completion with OpenAI provider"""
        from backend.services.llm_provider_service import LLMProviderService
        
        service = LLMProviderService()
        
        with patch.object(service, '_call_openai', new_callable=AsyncMock, return_value='OpenAI response'):
            result = await service.complete('Test prompt', provider='openai')
            assert result == 'OpenAI response'
    
    @pytest.mark.asyncio
    async def test_complete_with_gemini(self):
        """Test completion with Gemini provider"""
        from backend.services.llm_provider_service import LLMProviderService
        
        service = LLMProviderService()
        
        with patch.object(service, '_call_gemini', new_callable=AsyncMock, return_value='Gemini response'):
            result = await service.complete('Test prompt', provider='gemini')
            assert result == 'Gemini response'
    
    @pytest.mark.asyncio
    async def test_complete_with_local_llm(self):
        """Test completion with local LLM"""
        from backend.services.llm_provider_service import LLMProviderService
        
        service = LLMProviderService()
        
        with patch.object(service, '_call_local', new_callable=AsyncMock, return_value='Local response'):
            result = await service.complete('Test prompt', provider='local')
            assert result == 'Local response'
    
    @pytest.mark.asyncio
    async def test_auto_provider_selection(self):
        """Test automatic provider selection"""
        from backend.services.llm_provider_service import LLMProviderService
        
        service = LLMProviderService()
        
        with patch.object(service, '_select_best_provider', return_value='openai'):
            with patch.object(service, '_call_openai', new_callable=AsyncMock, return_value='Auto response'):
                result = await service.complete('Test prompt', provider='auto')
                assert result == 'Auto response'
    
    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        """Test fallback to another provider on error"""
        from backend.services.llm_provider_service import LLMProviderService
        
        service = LLMProviderService()
        
        with patch.object(service, '_call_openai', new_callable=AsyncMock, side_effect=Exception('API Error')):
            with patch.object(service, '_call_gemini', new_callable=AsyncMock, return_value='Fallback response'):
                result = await service.complete('Test prompt', provider='openai', fallback=True)
                assert result == 'Fallback response'
    
    @pytest.mark.asyncio
    async def test_streaming_response(self):
        """Test streaming response"""
        from backend.services.llm_provider_service import LLMProviderService
        
        service = LLMProviderService()
        
        async def mock_stream():
            for chunk in ['Hello', ' ', 'World']:
                yield chunk
        
        with patch.object(service, '_stream_openai', return_value=mock_stream()):
            chunks = []
            async for chunk in service.stream('Test prompt', provider='openai'):
                chunks.append(chunk)
            
            assert ''.join(chunks) == 'Hello World'
    
    @pytest.mark.asyncio
    async def test_json_response(self):
        """Test JSON response parsing"""
        from backend.services.llm_provider_service import LLMProviderService
        
        service = LLMProviderService()
        
        with patch.object(service, 'complete', new_callable=AsyncMock, return_value='{"key": "value"}'):
            result = await service.complete_json('Generate JSON', provider='openai')
            assert result == {'key': 'value'}
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting"""
        from backend.services.llm_provider_service import LLMProviderService
        
        service = LLMProviderService()
        
        with patch.object(service, '_check_rate_limit', return_value=True):
            with patch.object(service, '_call_openai', new_callable=AsyncMock, return_value='response'):
                result = await service.complete('Test', provider='openai')
                assert result is not None


class TestLLMDataModels:
    """Tests for LLM data models"""
    
    def test_provider_enum(self):
        """Test LLMProvider enum"""
        from backend.services.llm_provider_service import LLMProvider
        
        assert LLMProvider.OPENAI.value == 'openai'
        assert LLMProvider.GEMINI.value == 'gemini'
        assert LLMProvider.LOCAL.value == 'local'
    
    def test_completion_request(self):
        """Test CompletionRequest model"""
        from backend.services.llm_provider_service import CompletionRequest
        
        request = CompletionRequest(
            prompt='Test prompt',
            max_tokens=1000,
            temperature=0.7
        )
        
        assert request.prompt == 'Test prompt'
        assert request.max_tokens == 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
