# Document Verification Workflow

A comprehensive document verification system built with the multiagents framework, demonstrating real-world document processing workflows with AI-powered analysis, fraud detection, and compliance checking.

## 🎯 Overview

This example showcases a production-ready document verification system that processes documents through multiple verification stages:

- **Document Processing**: Extract text from PDFs, perform OCR on images, validate formats
- **AI-Powered Classification**: Use DSPy with Gemini to intelligently classify document types
- **Multi-Stage Verification**: Identity verification, financial analysis, compliance checking
- **Fraud Detection**: Advanced pattern recognition and risk assessment
- **Decision Making**: AI-powered final decisions with confidence scoring
- **Monitoring & Observability**: Comprehensive tracking and reporting

## 🏗️ Architecture

The system uses the multiagents framework's hybrid event-driven orchestration pattern:

```
📄 Document Input
       ↓
🔧 Document Processing → 🤖 AI Classification
                                 ↓
📋 Compliance Check ← 🆔 Identity Verification
       ↓                         
🚨 Fraud Detection → 💰 Financial Analysis (conditional)
                                 ↓
🎯 Final Decision Making ← All Analysis Results
       ↓
📊 Result Archiving → 📧 Notifications
```

### Key Components

- **Orchestrator Service**: Manages workflow state and coordinates activities
- **Worker Agents**: Specialized processors for each verification stage
- **Event Bus**: Redis-based communication layer
- **Monitoring System**: Real-time observability and performance tracking

## 🚀 Quick Start

### Prerequisites

1. **Redis Server**: Required for the event bus
   ```bash
   # Install Redis (macOS)
   brew install redis
   redis-server
   
   # Or using Docker
   docker run -d -p 6379:6379 redis:latest
   ```

2. **Python Environment**: Python 3.9+
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Gemini API Key** (optional but recommended):
   ```bash
   export GOOGLE_API_KEY="your-gemini-api-key"
   ```

### Running the System

1. **Basic Document Verification**:
   ```bash
   python main.py
   ```
   This processes a sample driver's license through the full verification workflow.

2. **Process Specific Document**:
   ```bash
   python main.py --document-path path/to/your/document.pdf
   ```

3. **Different Workflow Types**:
   ```bash
   # Identity verification only
   python main.py --workflow-type identity_only
   
   # Financial documents only
   python main.py --workflow-type financial_only
   
   # Batch processing
   python main.py --batch
   ```

4. **Create Sample Documents**:
   ```bash
   python main.py --create-samples
   ```

## 🔧 Configuration

### Monitoring Configuration (`config/monitoring.yaml`)

```yaml
logging:
  default_logger: "composite"
  level: "INFO"
  file_path: "./logs/document_verification.log"

event_monitoring:
  enabled: true
  trace_retention_hours: 48
  
worker_monitoring:
  enabled: true
  health_check_interval_seconds: 30
```

### Verification Rules (`config/verification_rules.yaml`)

```yaml
document_types:
  drivers_license:
    required_fields: ["license_number", "dates", "addresses"]
    verification:
      database_check_required: true
      fraud_check_level: "standard"
      
fraud_detection:
  risk_weights:
    low_ocr_confidence: 0.2
    suspicious_patterns: 0.3
    failed_database_verification: 0.4
```

## 📋 Document Types Supported

### Identity Documents
- **Driver's Licenses**: State-issued identification
- **Passports**: International travel documents
- **National ID Cards**: Government-issued identification

### Financial Documents
- **Bank Statements**: Monthly account statements
- **Tax Documents**: W-2, 1099, tax returns
- **Pay Stubs**: Employment income verification

### Proof of Address
- **Utility Bills**: Electric, gas, water bills
- **Government Correspondence**: Official mail
- **Lease Agreements**: Rental contracts

## 🤖 AI-Powered Workers

### DSPy Integration

The system uses DSPy with Google Gemini for intelligent document analysis:

```python
@dspy_worker("document_classifier",
            signature="document_content, file_metadata -> document_type: str, confidence: float",
            reasoning="chain_of_thought",
            model="gemini/gemini-1.5-pro")
async def document_classifier_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    # AI analyzes content and classifies document type
    pass
```

### Reasoning Patterns

- **Chain of Thought**: Step-by-step document analysis
- **ReAct**: Reasoning + Action for database lookups and verification
- **Tool Integration**: External API calls and database queries

### Available Tools

- **OCR Processing**: Extract text from images
- **Database Verification**: Check against official records
- **Fraud Detection**: Pattern analysis and risk assessment
- **Compliance Validation**: Regulatory requirement checking

## 📊 Monitoring & Observability

### Real-Time Monitoring

The system provides comprehensive monitoring:

- **Event Lifecycle Tracking**: Complete audit trail
- **Worker Performance Metrics**: Success rates, execution times
- **System Health**: Resource usage, queue depths
- **Error Tracking**: Detailed failure analysis

### Sample Output

```
📊 DOCUMENT VERIFICATION REPORT
======================================================================
🔍 WORKFLOW SUMMARY
Transaction ID: TXN-1699123456
Final State: completed
Steps Completed: 8

📄 DOCUMENT ANALYSIS
Document Type: drivers_license
Classification Confidence: 0.92
Manual Review Required: False

🆔 IDENTITY VERIFICATION
Identity Verified: True
Verification Confidence: 0.87

🚨 FRAUD DETECTION
Fraud Risk Level: LOW
Risk Score: 0.15
Fraud Indicators: 0

📋 COMPLIANCE CHECK
Compliance Status: compliant
Compliance Score: 0.95
Missing Requirements: 0

🎯 FINAL DECISION
Decision: APPROVED
Confidence: 0.91
Human Review Required: False

⚡ SYSTEM PERFORMANCE
Total Events: 24
Event Success Rate: 100.0%
Worker Commands: 8
Worker Success Rate: 100.0%
```

## 🧪 Testing

### Running Tests

```bash
# Unit tests
pytest tests/test_document_verification.py -v

# Integration tests (requires Redis)
pytest tests/test_document_verification.py::TestIntegrationScenarios -v

# All tests
pytest tests/ -v --tb=short
```

### Test Coverage

The test suite covers:
- ✅ Individual tool functionality
- ✅ Worker processing logic
- ✅ Workflow definitions
- ✅ Error handling and compensation
- ✅ End-to-end integration scenarios

## 🔄 Workflow Types

### Full Verification (`--workflow-type full`)
Complete document verification including:
- Document processing and classification
- Identity verification (if applicable)
- Financial analysis (if applicable)
- Compliance checking
- Fraud detection
- Final decision making
- Result archiving and notifications

### Identity Only (`--workflow-type identity_only`)
Streamlined workflow for identity documents:
- Faster processing
- Focus on identity verification
- Basic compliance and fraud checks

### Financial Only (`--workflow-type financial_only`)
Specialized for financial documents:
- Enhanced financial analysis
- Risk assessment
- Compliance with financial regulations

### Batch Processing (`--workflow-type batch`)
Process multiple documents efficiently:
- Parallel processing where possible
- Batch reporting
- Optimized resource usage

## 🛡️ Security & Compliance

### Data Protection
- Sensitive data encryption
- Secure file handling
- Audit trail maintenance
- GDPR compliance considerations

### Fraud Prevention
- Multi-layer fraud detection
- Pattern recognition
- Risk scoring algorithms
- Manual review triggers

### Compliance Frameworks
- KYC (Know Your Customer)
- AML (Anti-Money Laundering) 
- Document authenticity verification
- Regulatory requirement validation

## 🔧 Customization

### Adding New Document Types

1. **Define Document Rules** in `config/verification_rules.yaml`:
   ```yaml
   document_types:
     new_document_type:
       required_fields: ["field1", "field2"]
       validation_rules:
         field1:
           pattern: "^[A-Z0-9]+$"
           required: true
   ```

2. **Update Entity Extraction** in `tools.py`:
   ```python
   elif document_type == "new_document_type":
       # Add specific extraction patterns
       new_pattern = r'Field1:?\s*([A-Z0-9]+)'
       entities["field1"] = re.findall(new_pattern, text_content)
   ```

3. **Configure Workers** to handle the new type in classification logic.

### Adding New Verification Steps

1. **Create Worker Function**:
   ```python
   @dspy_worker("new_verification_step", 
               signature="input -> output",
               reasoning="chain_of_thought")
   async def new_verification_worker(context: Dict[str, Any]) -> Dict[str, Any]:
       # Implementation
       pass
   ```

2. **Update Workflow Definition**:
   ```python
   builder.add_step(
       "new_verification_step",
       new_verification_worker,
       compensation_worker=cleanup_worker
   )
   ```

### Integrating External Services

1. **Add Tool for External API**:
   ```python
   @tool("external_verification_api")
   async def call_external_api(document_data: Dict[str, Any]) -> Dict[str, Any]:
       async with httpx.AsyncClient() as client:
           response = await client.post("https://api.example.com/verify", 
                                      json=document_data)
           return response.json()
   ```

2. **Use in DSPy Worker**:
   ```python
   @dspy_worker("enhanced_verifier",
               tools=[call_external_api],
               reasoning="react")
   async def enhanced_verification_worker(context):
       # Worker can now call external API through ReAct reasoning
       pass
   ```

## 📈 Performance Optimization

### Scaling Considerations

- **Horizontal Scaling**: Multiple worker instances
- **Load Balancing**: Distribute document processing
- **Caching**: Store verification results
- **Batch Processing**: Handle multiple documents efficiently

### Resource Management

- **Memory Usage**: Large documents and OCR processing
- **CPU Intensive**: AI model inference
- **I/O Operations**: File processing and database calls
- **Network**: External API integrations

## 🚨 Error Handling

### Compensation Patterns

The system implements comprehensive error handling:

1. **Processing Failures**: Clean up temporary files
2. **Verification Errors**: Revert stored results
3. **Communication Failures**: Send failure notifications
4. **System Errors**: Graceful degradation

### Recovery Strategies

- **Retry Logic**: Transient failure recovery
- **Circuit Breakers**: Prevent cascade failures
- **Fallback Modes**: Continue with reduced functionality
- **Manual Intervention**: Queue for human review

## 📚 Advanced Features

### Workflow Orchestration
- **Saga Pattern**: Distributed transaction management
- **Compensation Actions**: Automatic rollback on failures
- **State Persistence**: Resume interrupted workflows
- **Event Sourcing**: Complete audit trail

### AI/ML Integration
- **DSPy Framework**: Structured LLM programming
- **Tool Usage**: External system integration
- **Reasoning Patterns**: Chain-of-thought, ReAct, CodeAct
- **Model Optimization**: Training data collection

### Production Readiness
- **Monitoring**: Comprehensive observability
- **Logging**: Structured, searchable logs
- **Metrics**: Performance and business metrics
- **Alerting**: Proactive issue detection

## 🤝 Contributing

To extend or modify this example:

1. Follow the existing patterns for workers and tools
2. Add comprehensive tests for new functionality
3. Update configuration files as needed
4. Document new features and usage patterns

## 📄 License

This example is part of the multiagents framework and follows its licensing terms.

## 🆘 Support

For questions or issues:

1. Check the [multiagents framework documentation](../../docs/)
2. Review the test suite for usage examples
3. Examine the monitoring logs for debugging
4. Create issues in the main framework repository

---

**Note**: This is a demonstration system. For production use, implement proper security measures, integrate with real external services, and follow your organization's compliance requirements.