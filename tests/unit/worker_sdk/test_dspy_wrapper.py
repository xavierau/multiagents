"""
Comprehensive unit tests for DSPy wrapper.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import dspy
from pydantic import BaseModel
from multiagents.worker_sdk.dspy_wrapper import DSPyConfig, DSPySignature, DSPyAgent


class TestDSPyConfig:
    """Test cases for DSPyConfig."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = DSPyConfig()
        
        assert config.model == "gemini/gemini-1.5-flash"
        assert config.api_key is None
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.retry_attempts == 3
    
    def test_config_custom_values(self):
        """Test configuration with custom values."""
        config = DSPyConfig(
            model="gpt-4",
            api_key="test-key",
            temperature=0.5,
            max_tokens=2000,
            retry_attempts=5
        )
        
        assert config.model == "gpt-4"
        assert config.api_key == "test-key"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.retry_attempts == 5


class TestDSPySignature:
    """Test cases for DSPySignature."""
    
    def test_signature_creation(self):
        """Test basic signature creation."""
        class TestSignature(DSPySignature):
            input_field: str
            output_field: str
        
        # Test instantiation
        sig = TestSignature(input_field="test", output_field="result")
        assert sig.input_field == "test"
        assert sig.output_field == "result"
    
    def test_signature_forbids_extra_fields(self):
        """Test that signature forbids extra fields."""
        class TestSignature(DSPySignature):
            field1: str
        
        # Should raise validation error for extra field
        with pytest.raises(Exception):  # Pydantic validation error
            TestSignature(field1="test", extra_field="not_allowed")


class TestDSPyAgentInitialization:
    """Test cases for DSPyAgent initialization."""
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_init_with_default_config(self, mock_lm, mock_configure):
        """Test initialization with default config."""
        mock_lm_instance = Mock()
        mock_lm.return_value = mock_lm_instance
        
        agent = DSPyAgent()
        
        # Check config defaults
        assert agent.config.model == "gemini/gemini-1.5-flash"
        assert agent.config.temperature == 0.7
        assert agent.config.max_tokens == 1000
        
        # Check DSPy setup
        mock_lm.assert_called_once()
        mock_configure.assert_called_once_with(lm=mock_lm_instance)
        
        # Check internal state
        assert agent._signatures == {}
        assert agent._modules == {}
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_init_with_custom_config(self, mock_lm, mock_configure):
        """Test initialization with custom config."""
        config = DSPyConfig(model="gpt-4", temperature=0.8, max_tokens=1500)
        mock_lm_instance = Mock()
        mock_lm.return_value = mock_lm_instance
        
        agent = DSPyAgent(config)
        
        # Check config
        assert agent.config == config
        
        # Check LM creation with custom values
        mock_lm.assert_called_once_with(
            model="gpt-4",
            api_key=None,
            temperature=0.8,
            max_tokens=1500
        )
    
    @patch('multiagents.worker_sdk.dspy_wrapper.os.getenv')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_api_key_from_config(self, mock_lm, mock_configure, mock_getenv):
        """Test API key taken from config."""
        config = DSPyConfig(api_key="config-key")
        mock_lm_instance = Mock()
        mock_lm.return_value = mock_lm_instance
        
        agent = DSPyAgent(config)
        
        # Should use config API key, not environment
        mock_getenv.assert_not_called()
        mock_lm.assert_called_once_with(
            model="gemini/gemini-1.5-flash",
            api_key="config-key",
            temperature=0.7,
            max_tokens=1000
        )
    
    @patch('multiagents.worker_sdk.dspy_wrapper.os.getenv')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_api_key_from_environment_openai(self, mock_lm, mock_configure, mock_getenv):
        """Test API key from environment for OpenAI models."""
        mock_getenv.return_value = "env-openai-key"
        config = DSPyConfig(model="gpt-4")
        mock_lm_instance = Mock()
        mock_lm.return_value = mock_lm_instance
        
        agent = DSPyAgent(config)
        
        mock_getenv.assert_called_once_with("OPENAI_API_KEY")
        mock_lm.assert_called_once_with(
            model="gpt-4",
            api_key="env-openai-key",
            temperature=0.7,
            max_tokens=1000
        )
    
    @patch('multiagents.worker_sdk.dspy_wrapper.os.getenv')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_api_key_from_environment_google(self, mock_lm, mock_configure, mock_getenv):
        """Test API key from environment for Google models."""
        mock_getenv.return_value = "env-google-key"
        config = DSPyConfig(model="gemini/gemini-1.5-flash")
        mock_lm_instance = Mock()
        mock_lm.return_value = mock_lm_instance
        
        agent = DSPyAgent(config)
        
        mock_getenv.assert_called_once_with("GOOGLE_API_KEY")
        mock_lm.assert_called_once_with(
            model="gemini/gemini-1.5-flash",
            api_key="env-google-key",
            temperature=0.7,
            max_tokens=1000
        )


class TestDSPyAgentSignatures:
    """Test cases for signature creation and management."""
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.Signature')
    def test_create_signature(self, mock_signature_class, mock_lm, mock_configure):
        """Test signature creation."""
        mock_signature = Mock()
        mock_signature_class.return_value = mock_signature
        
        agent = DSPyAgent()
        
        result = agent.create_signature("input_text", "output_text")
        
        mock_signature_class.assert_called_once_with("input_text -> output_text")
        assert result == mock_signature
        
        # Check not cached without name
        assert agent._signatures == {}
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.Signature')
    def test_create_signature_with_name(self, mock_signature_class, mock_lm, mock_configure):
        """Test signature creation with caching."""
        mock_signature = Mock()
        mock_signature_class.return_value = mock_signature
        
        agent = DSPyAgent()
        
        result = agent.create_signature("input_text", "output_text", name="test_sig")
        
        assert result == mock_signature
        assert agent._signatures["test_sig"] == mock_signature


class TestDSPyAgentChains:
    """Test cases for chain creation and management."""
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_create_chain_single_module(self, mock_lm, mock_configure):
        """Test chain creation with single module."""
        agent = DSPyAgent()
        mock_module = Mock()
        
        result = agent.create_chain(mock_module)
        
        assert result == mock_module
        assert agent._modules == {}
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.ChainOfThought')
    def test_create_chain_multiple_modules(self, mock_cot_class, mock_lm, mock_configure):
        """Test chain creation with multiple modules."""
        mock_chain = Mock()
        mock_cot_class.return_value = mock_chain
        
        agent = DSPyAgent()
        mock_module1 = Mock()
        mock_module2 = Mock()
        
        result = agent.create_chain(mock_module1, mock_module2)
        
        mock_cot_class.assert_called_once_with(mock_module1, mock_module2)
        assert result == mock_chain
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.ChainOfThought')
    def test_create_chain_with_name(self, mock_cot_class, mock_lm, mock_configure):
        """Test chain creation with caching."""
        mock_chain = Mock()
        mock_cot_class.return_value = mock_chain
        
        agent = DSPyAgent()
        mock_module1 = Mock()
        mock_module2 = Mock()
        
        result = agent.create_chain(mock_module1, mock_module2, name="test_chain")
        
        assert result == mock_chain
        assert agent._modules["test_chain"] == mock_chain


class TestDSPyAgentPredict:
    """Test cases for prediction functionality."""
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.Predict')
    def test_predict(self, mock_predict_class, mock_lm, mock_configure):
        """Test basic prediction."""
        # Setup mocks
        mock_predictor = Mock()
        mock_predict_class.return_value = mock_predictor
        
        mock_result = Mock()
        mock_result.output_field = "test_output"
        mock_predictor.return_value = mock_result
        
        mock_signature = Mock()
        mock_signature.output_fields = ["output_field"]
        
        agent = DSPyAgent()
        
        # Test prediction
        result = agent.predict(mock_signature, input_field="test_input")
        
        mock_predict_class.assert_called_once_with(mock_signature)
        mock_predictor.assert_called_once_with(input_field="test_input")
        
        assert result == {"output_field": "test_output"}
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.Predict')
    def test_predict_missing_output_field(self, mock_predict_class, mock_lm, mock_configure):
        """Test prediction with missing output field."""
        mock_predictor = Mock()
        mock_predict_class.return_value = mock_predictor
        
        mock_result = Mock(spec=[])  # Empty spec means no attributes
        mock_predictor.return_value = mock_result
        
        mock_signature = Mock()
        mock_signature.output_fields = ["missing_field"]
        
        agent = DSPyAgent()
        
        result = agent.predict(mock_signature, input_field="test_input")
        
        assert result == {}


class TestDSPyAgentChainOfThought:
    """Test cases for chain of thought functionality."""
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.ChainOfThought')
    def test_chain_of_thought_with_signature(self, mock_cot_class, mock_lm, mock_configure):
        """Test chain of thought with provided signature."""
        mock_cot = Mock()
        mock_cot_class.return_value = mock_cot
        
        mock_result = Mock()
        mock_result.answer = "test_answer"
        mock_cot.return_value = mock_result
        
        mock_signature = Mock()
        
        agent = DSPyAgent()
        
        result = agent.chain_of_thought("test question", mock_signature)
        
        mock_cot_class.assert_called_once_with(mock_signature)
        mock_cot.assert_called_once_with(question="test question")
        assert result == "test_answer"
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.ChainOfThought')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.Signature')
    def test_chain_of_thought_without_signature(self, mock_signature_class, mock_cot_class, mock_lm, mock_configure):
        """Test chain of thought with auto-created signature."""
        mock_signature = Mock()
        mock_signature_class.return_value = mock_signature
        
        mock_cot = Mock()
        mock_cot_class.return_value = mock_cot
        
        mock_result = Mock()
        mock_result.answer = "auto_answer"
        mock_cot.return_value = mock_result
        
        agent = DSPyAgent()
        
        result = agent.chain_of_thought("test question")
        
        mock_signature_class.assert_called_once_with("question -> answer")
        mock_cot_class.assert_called_once_with(mock_signature)
        assert result == "auto_answer"
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.ChainOfThought')
    def test_chain_of_thought_no_answer_attribute(self, mock_cot_class, mock_lm, mock_configure):
        """Test chain of thought when result has no answer attribute."""
        mock_cot = Mock()
        mock_cot_class.return_value = mock_cot
        
        mock_result = "string_result"
        mock_cot.return_value = mock_result
        
        mock_signature = Mock()
        
        agent = DSPyAgent()
        
        result = agent.chain_of_thought("test question", mock_signature)
        
        assert result == "string_result"


class TestDSPyAgentReactAgent:
    """Test cases for ReAct agent functionality."""
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_react_agent_basic(self, mock_lm, mock_configure):
        """Test basic ReAct agent functionality."""
        agent = DSPyAgent()
        
        # Mock the predict method to return thought results
        with patch.object(agent, 'predict') as mock_predict:
            mock_predict.return_value = {
                'thought': 'I need to analyze this task',
                'action': 'analyze',
                'tool': 'analyzer'
            }
            
            with patch.object(agent, 'create_signature') as mock_create_sig:
                mock_signature = Mock()
                mock_create_sig.return_value = mock_signature
                
                result = agent.react_agent("test task", [], max_steps=2)
        
        assert "reasoning_trace" in result
        assert "final_answer" in result
        assert len(result["reasoning_trace"]) <= 2
        assert all("Thought:" in thought for thought in result["reasoning_trace"])
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_react_agent_final_answer(self, mock_lm, mock_configure):
        """Test ReAct agent stopping on final answer."""
        agent = DSPyAgent()
        
        with patch.object(agent, 'predict') as mock_predict:
            mock_predict.return_value = {
                'thought': 'This is the final answer to the task',
                'action': 'complete',
                'tool': 'none'
            }
            
            with patch.object(agent, 'create_signature') as mock_create_sig:
                mock_create_sig.return_value = Mock()
                
                result = agent.react_agent("test task", [], max_steps=5)
        
        # Should stop after one step due to "final answer" in thought
        assert len(result["reasoning_trace"]) == 1
        assert "final answer" in result["reasoning_trace"][0].lower()


class TestDSPyAgentStructuredOutput:
    """Test cases for structured output functionality."""
    
    def test_create_structured_output(self):
        """Test structured output creation."""
        class TestOutput(BaseModel):
            field1: str
            field2: int
        
        with patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure'):
            with patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM'):
                agent = DSPyAgent()
                
                with patch.object(agent, 'predict') as mock_predict:
                    mock_predict.return_value = {"field1": "test", "field2": 42}
                    
                    with patch.object(agent, 'create_signature') as mock_create_sig:
                        mock_create_sig.return_value = Mock()
                        
                        result = agent.create_structured_output(
                            TestOutput,
                            "Generate data for {topic}",
                            topic="testing"
                        )
        
        assert isinstance(result, TestOutput)
        assert result.field1 == "test"
        assert result.field2 == 42


class TestDSPyAgentBatchProcess:
    """Test cases for batch processing functionality."""
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_batch_process_success(self, mock_lm, mock_configure):
        """Test successful batch processing."""
        agent = DSPyAgent()
        
        items = [
            {"input": "item1"},
            {"input": "item2"}
        ]
        
        mock_signature = Mock()
        
        with patch.object(agent, 'predict') as mock_predict:
            mock_predict.side_effect = [
                {"output": "result1"},
                {"output": "result2"}
            ]
            
            results = agent.batch_process(items, mock_signature)
        
        assert len(results) == 2
        assert results[0] == {"output": "result1"}
        assert results[1] == {"output": "result2"}
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    def test_batch_process_with_error(self, mock_lm, mock_configure):
        """Test batch processing with error handling."""
        agent = DSPyAgent()
        
        items = [
            {"input": "item1"},
            {"input": "item2"}
        ]
        
        mock_signature = Mock()
        
        with patch.object(agent, 'predict') as mock_predict:
            mock_predict.side_effect = [
                {"output": "result1"},
                Exception("Processing error")
            ]
            
            results = agent.batch_process(items, mock_signature)
        
        assert len(results) == 2
        assert results[0] == {"output": "result1"}
        assert results[1] == {"error": "Processing error"}


class TestDSPyAgentOptimization:
    """Test cases for optimization functionality."""
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.Example')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.BootstrapFewShotWithRandomSearch')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.ChainOfThought')
    def test_optimize_chain_multiple_modules(self, mock_cot_class, mock_optimizer_class, mock_example_class, mock_lm, mock_configure):
        """Test chain optimization with multiple modules."""
        # Setup mocks
        mock_example1 = Mock()
        mock_example2 = Mock()
        mock_example_class.side_effect = [mock_example1, mock_example2]
        
        mock_optimizer = Mock()
        mock_optimized_program = Mock()
        mock_optimizer.compile.return_value = mock_optimized_program
        mock_optimizer_class.return_value = mock_optimizer
        
        mock_program = Mock()
        mock_cot_class.return_value = mock_program
        
        agent = DSPyAgent()
        
        examples = [
            {"input": "test1", "output": "result1"},
            {"input": "test2", "output": "result2"}
        ]
        
        mock_metric = Mock()
        mock_modules = [Mock(), Mock()]
        
        result = agent.optimize_chain(examples, mock_metric, mock_modules)
        
        # Check examples were converted
        assert mock_example_class.call_count == 2
        mock_example_class.assert_any_call(input="test1", output="result1")
        mock_example_class.assert_any_call(input="test2", output="result2")
        
        # Check optimizer setup
        mock_optimizer_class.assert_called_once_with(
            metric=mock_metric,
            max_bootstrapped_demos=4,
            max_labeled_demos=16
        )
        
        # Check program creation and optimization
        mock_cot_class.assert_called_once_with(*mock_modules)
        mock_optimizer.compile.assert_called_once_with(
            mock_program,
            trainset=[mock_example1, mock_example2]
        )
        
        assert result == mock_optimized_program
    
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.configure')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.LM')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.Example')
    @patch('multiagents.worker_sdk.dspy_wrapper.dspy.BootstrapFewShotWithRandomSearch')
    def test_optimize_chain_single_module(self, mock_optimizer_class, mock_example_class, mock_lm, mock_configure):
        """Test chain optimization with single module."""
        mock_optimizer = Mock()
        mock_optimized_program = Mock()
        mock_optimizer.compile.return_value = mock_optimized_program
        mock_optimizer_class.return_value = mock_optimizer
        
        agent = DSPyAgent()
        
        examples = [{"input": "test", "output": "result"}]
        mock_metric = Mock()
        mock_module = Mock()
        
        result = agent.optimize_chain(examples, mock_metric, [mock_module])
        
        # Should use single module directly, not ChainOfThought
        mock_optimizer.compile.assert_called_once()
        call_args = mock_optimizer.compile.call_args
        assert call_args[1]["trainset"] is not None
        # First argument should be the mock_module itself for single module
        assert call_args[0][0] == mock_module
        
        assert result == mock_optimized_program