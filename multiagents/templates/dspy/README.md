# DSPy-Powered Intelligent Workflow

A MultiAgents framework example showcasing DSPy integration for LLM-powered workflows with intelligent content processing, analysis, and generation.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your LLM provider:
   ```bash
   # For OpenAI
   export OPENAI_API_KEY="your-api-key"
   
   # For other providers, see DSPy documentation
   ```

3. Start Redis server:
   ```bash
   redis-server
   ```

4. Run the example:
   ```bash
   python main.py
   ```

## What This Example Shows

- **DSPy Integration**: LLM-powered workers using @dspy_worker decorator
- **Intelligent Workflows**: Content analysis, summarization, and generation
- **Chain of Thought**: Multi-step reasoning with DSPy signatures
- **Error Handling**: Robust handling of LLM failures and retries
- **Optimization**: DSPy's automatic prompt optimization capabilities
- **Mixed Workers**: Combination of traditional and LLM-powered workers

## Workflow Steps

1. **Content Ingestion** - Parse and validate input content
2. **Content Analysis** - DSPy-powered analysis of themes, sentiment, and key points
3. **Summary Generation** - Intelligent summarization with configurable length
4. **Content Enhancement** - Generate related content, tags, and metadata
5. **Quality Review** - Final validation and quality scoring

## Project Structure

- `main.py` - Application entry point with content processing scenarios
- `workflows/` - Intelligent content processing workflows
- `workers/` - DSPy-powered and traditional workers
- `dspy_agents/` - DSPy signature definitions and agent implementations
- `config/` - Configuration for monitoring and DSPy settings
- `tests/` - Test suite including LLM worker testing patterns

## DSPy Features Demonstrated

### Signatures
- Content analysis with structured output
- Summarization with length control
- Quality assessment with scoring

### Agents
- Custom DSPy agents with multi-step reasoning
- Chain-of-thought prompting
- Automatic retry and error handling

### Optimization
- Few-shot examples for better performance
- Automatic prompt tuning (when evaluation data available)

## Configuration

### DSPy Settings
Configure your LLM provider in `config/dspy_config.yaml`:
```yaml
llm:
  provider: "openai"  # or "anthropic", "cohere", etc.  
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 1000
```

### Content Processing
Customize processing parameters in `config/content_settings.yaml`:
```yaml
analysis:
  max_themes: 5
  sentiment_analysis: true
  
summarization:
  default_length: "medium"  # short, medium, long
  preserve_key_points: true
  
enhancement:
  generate_tags: true
  suggest_related: true
```

## Example Scenarios

The demo processes different content types:
- 📰 **News Articles** - Analysis and summarization
- 📚 **Research Papers** - Key findings extraction
- 💬 **Social Media** - Sentiment and trend analysis
- 📧 **Customer Feedback** - Issue categorization and response generation

## Benefits of DSPy Integration

- **Structured Output**: Reliable, validated responses from LLMs
- **Error Recovery**: Automatic retry with different prompts on failures  
- **Optimization**: Continuous improvement of prompt effectiveness
- **Consistency**: Reproducible results across runs
- **Scalability**: Efficient handling of batch processing
- **Monitoring**: Full observability of LLM interactions

## Advanced Features

- **Custom Signatures**: Define your own input/output schemas
- **Multi-Model Support**: Use different models for different tasks
- **Caching**: Intelligent caching of LLM responses
- **Rate Limiting**: Respect API rate limits automatically
- **Cost Tracking**: Monitor token usage and costs