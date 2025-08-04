import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from multiagents.worker_sdk.decorators import worker, dspy_worker, FunctionWorker
from multiagents.worker_sdk.base_worker import WorkerConfig


class TestFunctionWorker:
    def test_function_worker_with_sync_function(self):
        def sync_func(context):
            return {"result": context["value"] * 2}
        
        config = WorkerConfig(worker_type="test_worker")
        worker = FunctionWorker(config, sync_func)
        
        assert worker.func == sync_func
        assert not worker.is_async
        assert worker.config.worker_type == "test_worker"

    def test_function_worker_with_async_function(self):
        async def async_func(context):
            return {"result": context["value"] * 2}
        
        config = WorkerConfig(worker_type="test_worker")
        worker = FunctionWorker(config, async_func)
        
        assert worker.func == async_func
        assert worker.is_async

    @pytest.mark.asyncio
    async def test_execute_sync_function(self):
        def sync_func(context):
            return {"result": context["value"] * 2}
        
        config = WorkerConfig(worker_type="test_worker")
        worker = FunctionWorker(config, sync_func)
        
        result = await worker.execute({"value": 5})
        assert result == {"result": 10}

    @pytest.mark.asyncio
    async def test_execute_async_function(self):
        async def async_func(context):
            await asyncio.sleep(0.01)  # Simulate async work
            return {"result": context["value"] * 2}
        
        config = WorkerConfig(worker_type="test_worker")
        worker = FunctionWorker(config, async_func)
        
        result = await worker.execute({"value": 5})
        assert result == {"result": 10}

    @pytest.mark.asyncio
    async def test_execute_non_dict_return(self):
        def func(context):
            return "simple string"
        
        config = WorkerConfig(worker_type="test_worker")
        worker = FunctionWorker(config, func)
        
        result = await worker.execute({"value": 5})
        assert result == {"result": "simple string"}

    def test_validate_input_with_kwargs(self):
        def func(**kwargs):
            pass
        
        config = WorkerConfig(worker_type="test_worker")
        worker = FunctionWorker(config, func)
        
        assert worker.validate_input({"any": "data"}) is True

    def test_validate_input_single_parameter(self):
        def func(context):
            pass
        
        config = WorkerConfig(worker_type="test_worker")
        worker = FunctionWorker(config, func)
        
        assert worker.validate_input({"any": "data"}) is True

    def test_validate_input_required_parameters(self):
        def func(value, multiplier=2):
            pass
        
        config = WorkerConfig(worker_type="test_worker")
        worker = FunctionWorker(config, func)
        
        # Should pass with required parameter
        assert worker.validate_input({"value": 5}) is True
        
        # Should fail without required parameter
        assert worker.validate_input({"other": 5}) is False


class TestWorkerDecorator:
    def test_worker_decorator_basic(self):
        @worker("test_worker")
        def test_func(context):
            return {"result": "ok"}
        
        assert isinstance(test_func, FunctionWorker)
        assert test_func.config.worker_type == "test_worker"
        assert test_func.config.timeout_seconds == 300
        assert test_func.config.retry_attempts == 3
        assert test_func.config.retry_delay_seconds == 1

    def test_worker_decorator_with_custom_config(self):
        @worker(
            "test_worker",
            timeout=600,
            retry_attempts=5,
            retry_delay=2
        )
        def test_func(context):
            return {"result": "ok"}
        
        assert test_func.config.timeout_seconds == 600
        assert test_func.config.retry_attempts == 5
        assert test_func.config.retry_delay_seconds == 2

    def test_worker_decorator_with_validation(self):
        def input_validator(context):
            return "value" in context
        
        def output_validator(result):
            return "status" in result
        
        @worker(
            "test_worker",
            validate_input=input_validator,
            validate_output=output_validator
        )
        def test_func(context):
            return {"status": "ok"}
        
        assert test_func.validate_input == input_validator
        assert test_func.validate_output == output_validator

    @pytest.mark.asyncio
    async def test_worker_decorator_async_function(self):
        @worker("async_worker")
        async def async_func(context):
            await asyncio.sleep(0.01)
            return {"result": context["value"] * 2}
        
        result = await async_func.execute({"value": 5})
        assert result == {"result": 10}

    def test_worker_decorator_preserves_original_function(self):
        def original_func(context):
            return {"result": "ok"}
        
        decorated = worker("test_worker")(original_func)
        
        assert hasattr(decorated, "original_function")
        assert decorated.original_function == original_func


class TestDSPyWorkerDecorator:
    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyAgent')
    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyConfig')
    def test_dspy_worker_basic(self, mock_config_class, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        
        @dspy_worker("test_dspy_worker")
        def test_func(context):
            return {"processed": True}
        
        assert isinstance(test_func, FunctionWorker)
        assert test_func.config.worker_type == "test_dspy_worker"
        mock_config_class.assert_called_once()
        mock_agent_class.assert_called_once_with(mock_config)

    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyAgent')
    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyConfig')
    def test_dspy_worker_with_signature(self, mock_config_class, mock_agent_class):
        mock_agent = MagicMock()
        mock_signature = MagicMock()
        mock_agent.create_signature.return_value = mock_signature
        mock_agent.predict.return_value = {"summary": "test summary"}
        mock_agent_class.return_value = mock_agent
        
        @dspy_worker(
            "summarizer",
            signature="text -> summary"
        )
        def summarize(context):
            return {"additional": "data"}
        
        # Test signature creation
        mock_agent.create_signature.assert_called_once_with("text", "summary")

    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyAgent')
    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyConfig')
    def test_dspy_worker_with_custom_model(self, mock_config_class, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        @dspy_worker(
            "test_worker",
            model="gpt-4"
        )
        def test_func(context):
            return {}
        
        # Verify DSPyConfig was called with the model
        mock_config_class.assert_called_once_with(model="gpt-4")

    @pytest.mark.asyncio
    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyAgent')
    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyConfig')
    async def test_dspy_worker_execution_without_signature(self, mock_config_class, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        @dspy_worker("test_worker")
        async def test_func(context):
            # Should have access to DSPy agent
            assert "_dspy_agent" in context
            return {"result": "processed"}
        
        # Get the wrapped function
        wrapped_func = test_func.func
        
        result = await wrapped_func({"input": "data"})
        assert result == {"result": "processed"}

    @pytest.mark.asyncio
    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyAgent')
    @patch('multiagents.worker_sdk.dspy_wrapper.DSPyConfig')
    async def test_dspy_worker_execution_with_signature(self, mock_config_class, mock_agent_class):
        mock_agent = MagicMock()
        mock_signature = MagicMock()
        mock_agent.create_signature.return_value = mock_signature
        mock_agent.predict.return_value = {"summary": "AI generated summary"}
        mock_agent_class.return_value = mock_agent
        
        @dspy_worker(
            "summarizer",
            signature="text -> summary"
        )
        def summarize(context):
            return {"metadata": {"length": len(context.get("text", ""))}}
        
        # Get the wrapped function
        wrapped_func = summarize.func
        
        result = await wrapped_func({"text": "Long text to summarize"})
        
        # Should include both AI result and function result
        assert result["summary"] == "AI generated summary"
        assert result["metadata"]["length"] == 22
        
        # Verify predict was called
        mock_agent.predict.assert_called_once()

    def test_dspy_worker_config_parameters(self):
        with patch('multiagents.worker_sdk.dspy_wrapper.DSPyAgent'):
            with patch('multiagents.worker_sdk.dspy_wrapper.DSPyConfig'):
                @dspy_worker(
                    "test_worker",
                    timeout=600,
                    retry_attempts=5
                )
                def test_func(context):
                    return {}
                
                assert test_func.config.timeout_seconds == 600
                assert test_func.config.retry_attempts == 5