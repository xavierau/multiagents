# MultiAgents Framework - Workflow Patterns

## Core Workflow Patterns

### 1. Sequential Processing Pattern

```python
# Linear workflow where each step depends on the previous
def create_sequential_workflow():
    """Standard sequential processing workflow."""
    return (WorkflowBuilder("sequential_processing")
        .add_step("validate_input", "validate_input")
        .add_step("process_data", "process_data") 
        .add_step("transform_output", "transform_output")
        .add_step("save_results", "save_results")
        .build())

# Worker implementations
@worker("validate_input")
async def validate_input(context: Dict[str, Any]) -> Dict[str, Any]:
    data = context.get("raw_data")
    if not data:
        raise ValueError("No data provided")
    
    return {
        "validated_data": data,
        "validation_timestamp": datetime.utcnow().isoformat(),
        "data_size": len(str(data))
    }

@worker("process_data")
async def process_data(context: Dict[str, Any]) -> Dict[str, Any]:
    validated_data = context["validated_data"]
    
    # Processing logic
    processed = perform_complex_processing(validated_data)
    
    return {
        "processed_data": processed,
        "processing_stats": {
            "input_size": context["data_size"],
            "output_size": len(str(processed)),
            "processing_time": "2.3s"
        }
    }
```

### 2. Compensated Transaction Pattern (Saga)

```python
# Workflow with compensation for each step that allocates resources
def create_compensated_workflow():
    """Workflow with built-in rollback capabilities."""
    return (WorkflowBuilder("order_processing")
        .add_step("reserve_inventory", "reserve_inventory", 
                 compensation="release_inventory")
        .add_step("charge_payment", "charge_payment",
                 compensation="refund_payment")
        .add_step("create_shipment", "create_shipment",
                 compensation="cancel_shipment")
        .add_step("send_confirmation", "send_confirmation")
        .build())

# Resource allocation worker
@worker("reserve_inventory")
async def reserve_inventory(context: Dict[str, Any]) -> Dict[str, Any]:
    order_items = context["order_items"]
    
    # Allocate resources
    reservation_id = allocate_inventory(order_items)
    
    return {
        "reservation_id": reservation_id,
        "reserved_items": order_items,
        "reservation_timestamp": datetime.utcnow().isoformat()
    }

# Compensation worker
@worker("release_inventory")
async def release_inventory(context: Dict[str, Any]) -> Dict[str, Any]:
    reservation_id = context.get("reservation_id")
    
    if not reservation_id:
        return {"status": "no_action_needed"}
    
    try:
        release_allocated_inventory(reservation_id)
        return {
            "status": "success",
            "released_reservation": reservation_id,
            "release_timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Compensation failures should not raise exceptions
        return {
            "status": "failed",
            "error": str(e),
            "requires_manual_intervention": True
        }
```

### 3. Fan-Out/Fan-In Pattern (Simulated)

```python
# Simulate parallel processing using multiple sequential workflows
def create_parallel_processing_workflow():
    """Process multiple data streams in parallel."""
    return (WorkflowBuilder("parallel_data_processing")
        .add_step("split_data", "split_data")
        .add_step("process_batch_1", "process_batch")
        .add_step("process_batch_2", "process_batch") 
        .add_step("process_batch_3", "process_batch")
        .add_step("combine_results", "combine_results")
        .build())

@worker("split_data")
async def split_data(context: Dict[str, Any]) -> Dict[str, Any]:
    """Split input data into parallel processing batches."""
    data = context["data"]
    batch_size = context.get("batch_size", 100)
    
    batches = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]
    
    return {
        "batch_1": batches[0] if len(batches) > 0 else [],
        "batch_2": batches[1] if len(batches) > 1 else [],
        "batch_3": batches[2] if len(batches) > 2 else [],
        "total_batches": len(batches),
        "batch_size": batch_size
    }

@worker("process_batch")
async def process_batch(context: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single batch of data."""
    # Determine which batch to process based on context
    for i in range(1, 4):
        batch_key = f"batch_{i}"
        if batch_key in context and context[batch_key]:
            batch_data = context[batch_key]
            processed = [process_item(item) for item in batch_data]
            
            return {
                f"processed_batch_{i}": processed,
                "batch_number": i,
                "items_processed": len(processed),
                "processing_timestamp": datetime.utcnow().isoformat()
            }
    
    return {"message": "No batch data found"}

@worker("combine_results")
async def combine_results(context: Dict[str, Any]) -> Dict[str, Any]:
    """Combine results from parallel processing."""
    combined_results = []
    batch_stats = []
    
    for i in range(1, 4):
        batch_key = f"processed_batch_{i}"
        if batch_key in context:
            batch_data = context[batch_key]
            combined_results.extend(batch_data)
            batch_stats.append({
                "batch_number": i,
                "items_count": len(batch_data)
            })
    
    return {
        "combined_results": combined_results,
        "total_items": len(combined_results),
        "batch_statistics": batch_stats,
        "combination_timestamp": datetime.utcnow().isoformat()
    }
```

### 4. Conditional Processing Pattern

```python
# Workflow with conditional logic based on data characteristics
def create_conditional_workflow():
    """Workflow that branches based on data analysis."""
    return (WorkflowBuilder("conditional_processing")
        .add_step("analyze_input", "analyze_input")
        .add_step("route_processing", "route_processing")
        .add_step("finalize_results", "finalize_results")
        .build())

@worker("analyze_input")
async def analyze_input(context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze input to determine processing path."""
    data = context["data"]
    data_type = context.get("data_type", "unknown")
    
    # Analyze data characteristics
    analysis = {
        "size": len(str(data)),
        "complexity": calculate_complexity(data),
        "data_type": data_type,
        "requires_llm": needs_llm_processing(data),
        "priority": determine_priority(data)
    }
    
    return {
        "original_data": data,
        "analysis": analysis,
        "analysis_timestamp": datetime.utcnow().isoformat()
    }

@worker("route_processing")
async def route_processing(context: Dict[str, Any]) -> Dict[str, Any]:
    """Route to appropriate processing based on analysis."""
    analysis = context["analysis"]
    data = context["original_data"]
    
    if analysis["requires_llm"]:
        # LLM processing
        result = await process_with_llm(data, analysis)
        processing_type = "llm_enhanced"
    elif analysis["complexity"] > 0.7:
        # Complex processing
        result = await complex_processing(data, analysis)
        processing_type = "complex_analysis"
    else:
        # Simple processing
        result = await simple_processing(data, analysis)
        processing_type = "basic_processing"
    
    return {
        "processed_result": result,
        "processing_type": processing_type,
        "processing_duration": calculate_duration(),
        "analysis_used": analysis
    }

async def process_with_llm(data, analysis):
    """Simulate LLM processing."""
    return {"llm_insights": "AI-generated insights", "confidence": 0.85}

async def complex_processing(data, analysis):
    """Simulate complex processing."""
    return {"complex_result": "Advanced analysis result", "accuracy": 0.92}

async def simple_processing(data, analysis):
    """Simulate simple processing."""
    return {"simple_result": "Basic analysis result", "speed": "fast"}
```

### 5. Error Recovery Pattern

```python
# Workflow with comprehensive error handling and recovery
def create_resilient_workflow():
    """Workflow with built-in error recovery mechanisms."""
    return (WorkflowBuilder("resilient_processing")
        .add_step("attempt_processing", "attempt_processing")
        .add_step("verify_results", "verify_results")
        .add_step("cleanup_resources", "cleanup_resources")
        .build())

@worker("attempt_processing")
async def attempt_processing(context: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt processing with error recovery."""
    data = context["data"]
    retry_count = context.get("retry_count", 0)
    max_retries = context.get("max_retries", 3)
    
    try:
        # Primary processing attempt
        result = await primary_processing(data)
        
        return {
            "result": result,
            "status": "success",
            "method": "primary",
            "attempts_used": retry_count + 1
        }
        
    except TemporaryFailure as e:
        if retry_count < max_retries:
            # Increment retry and signal for retry
            return {
                "status": "retry_needed",
                "error": str(e),
                "retry_count": retry_count + 1,
                "next_attempt_delay": calculate_backoff_delay(retry_count)
            }
        else:
            # Fall back to alternative processing
            try:
                result = await fallback_processing(data)
                return {
                    "result": result,
                    "status": "fallback_success",
                    "method": "fallback",
                    "attempts_used": retry_count + 1,
                    "primary_error": str(e)
                }
            except Exception as fallback_error:
                return {
                    "status": "failed",
                    "primary_error": str(e),
                    "fallback_error": str(fallback_error),
                    "attempts_used": retry_count + 1
                }
    
    except CriticalFailure as e:
        # Immediate failure, no retry
        return {
            "status": "critical_failure",
            "error": str(e),
            "requires_intervention": True
        }

async def primary_processing(data):
    """Primary processing method (may fail)."""
    # Simulate processing that might fail
    if random.random() < 0.3:  # 30% failure rate
        raise TemporaryFailure("Service temporarily unavailable")
    return {"processed": True, "method": "primary"}

async def fallback_processing(data):
    """Fallback processing method."""
    # Simulate more reliable but slower processing
    await asyncio.sleep(1)  # Slower processing
    return {"processed": True, "method": "fallback", "quality": "basic"}

class TemporaryFailure(Exception):
    """Retryable failure."""
    pass

class CriticalFailure(Exception):
    """Non-retryable failure."""
    pass

def calculate_backoff_delay(attempt):
    """Calculate exponential backoff delay."""
    return min(30, 2 ** attempt)  # Max 30 seconds
```

### 6. Data Transformation Pipeline Pattern

```python
# Multi-stage data transformation workflow
def create_transformation_pipeline():
    """Data transformation pipeline with validation at each stage."""
    return (WorkflowBuilder("data_transformation_pipeline")
        .add_step("validate_schema", "validate_schema")
        .add_step("normalize_data", "normalize_data")
        .add_step("enrich_data", "enrich_data")
        .add_step("validate_output", "validate_output")
        .add_step("export_data", "export_data")
        .build())

@worker("validate_schema")
async def validate_schema(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate input data schema."""
    data = context["data"]
    expected_schema = context.get("schema", {})
    
    validation_errors = []
    
    # Schema validation logic
    for field, field_type in expected_schema.items():
        if field not in data:
            validation_errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], field_type):
            validation_errors.append(f"Invalid type for {field}: expected {field_type.__name__}")
    
    if validation_errors:
        return {
            "status": "validation_failed",
            "errors": validation_errors,
            "data": data
        }
    
    return {
        "status": "validation_passed",
        "validated_data": data,
        "schema_version": expected_schema.get("version", "1.0")
    }

@worker("normalize_data")
async def normalize_data(context: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize data format and values."""
    validated_data = context["validated_data"]
    
    # Normalization logic
    normalized = {}
    for key, value in validated_data.items():
        if isinstance(value, str):
            normalized[key] = value.strip().lower()
        elif isinstance(value, (int, float)):
            normalized[key] = float(value)
        else:
            normalized[key] = value
    
    return {
        "normalized_data": normalized,
        "normalization_rules_applied": ["trim_whitespace", "lowercase_strings", "float_conversion"],
        "original_data": validated_data
    }

@worker("enrich_data")
async def enrich_data(context: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich data with additional information."""
    normalized_data = context["normalized_data"]
    
    # Data enrichment logic
    enriched = dict(normalized_data)
    
    # Add computed fields
    enriched["enrichment_timestamp"] = datetime.utcnow().isoformat()
    enriched["data_fingerprint"] = calculate_data_fingerprint(normalized_data)
    
    # Add external data if applicable
    if "user_id" in enriched:
        enriched["user_metadata"] = await fetch_user_metadata(enriched["user_id"])
    
    return {
        "enriched_data": enriched,
        "enrichment_sources": ["computed_fields", "user_metadata"],
        "enrichment_completeness": calculate_completeness(enriched)
    }

@worker("validate_output")
async def validate_output(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate final output quality."""
    enriched_data = context["enriched_data"]
    
    quality_score = 0.0
    quality_checks = []
    
    # Quality validation logic
    if "data_fingerprint" in enriched_data:
        quality_score += 0.3
        quality_checks.append("fingerprint_present")
    
    if context.get("enrichment_completeness", 0) > 0.8:
        quality_score += 0.4
        quality_checks.append("high_completeness")
    
    if len(enriched_data) >= len(context.get("normalized_data", {})):
        quality_score += 0.3
        quality_checks.append("data_preserved")
    
    return {
        "final_data": enriched_data,
        "quality_score": quality_score,
        "quality_checks_passed": quality_checks,
        "ready_for_export": quality_score >= 0.7
    }

async def fetch_user_metadata(user_id):
    """Simulate fetching user metadata."""
    await asyncio.sleep(0.1)  # Simulate API call
    return {
        "user_segment": "premium",
        "registration_date": "2023-01-15",
        "preferences": {"notifications": True}
    }

def calculate_data_fingerprint(data):
    """Calculate a fingerprint for data integrity."""
    import hashlib
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()[:8]

def calculate_completeness(data):
    """Calculate data completeness score."""
    expected_fields = ["user_id", "timestamp", "data_fingerprint"]
    present_fields = [field for field in expected_fields if field in data]
    return len(present_fields) / len(expected_fields)
```

### 7. Event Processing Pattern

```python
# Event-driven processing workflow
def create_event_processing_workflow():
    """Process events with routing and aggregation."""
    return (WorkflowBuilder("event_processing")
        .add_step("parse_event", "parse_event")
        .add_step("classify_event", "classify_event")
        .add_step("process_by_type", "process_by_type")
        .add_step("aggregate_metrics", "aggregate_metrics")
        .build())

@worker("parse_event")
async def parse_event(context: Dict[str, Any]) -> Dict[str, Any]:
    """Parse raw event data."""
    raw_event = context["raw_event"]
    
    try:
        if isinstance(raw_event, str):
            parsed_event = json.loads(raw_event)
        else:
            parsed_event = raw_event
        
        # Standard event fields
        event_data = {
            "event_id": parsed_event.get("id", generate_event_id()),
            "event_type": parsed_event.get("type", "unknown"),
            "timestamp": parsed_event.get("timestamp", datetime.utcnow().isoformat()),
            "source": parsed_event.get("source", "unknown"),
            "data": parsed_event.get("data", {}),
            "metadata": parsed_event.get("metadata", {})
        }
        
        return {
            "parsed_event": event_data,
            "parsing_status": "success",
            "original_format": type(raw_event).__name__
        }
        
    except Exception as e:
        return {
            "parsing_status": "failed",
            "error": str(e),
            "raw_event": raw_event
        }

@worker("classify_event")
async def classify_event(context: Dict[str, Any]) -> Dict[str, Any]:
    """Classify event for routing."""
    parsed_event = context["parsed_event"]
    
    event_type = parsed_event["event_type"]
    source = parsed_event["source"]
    data = parsed_event["data"]
    
    # Classification logic
    if event_type in ["user_action", "click", "view"]:
        category = "user_engagement"
        priority = "normal"
    elif event_type in ["error", "exception", "failure"]:
        category = "system_error"
        priority = "high"
    elif event_type in ["purchase", "payment", "subscription"]:
        category = "business_transaction"
        priority = "high"
    else:
        category = "general"
        priority = "low"
    
    # Additional classification based on data content
    urgency = "normal"
    if data.get("amount", 0) > 1000:
        urgency = "high"
    elif "error" in str(data).lower():
        urgency = "high"
    
    return {
        "classified_event": {
            **parsed_event,
            "category": category,
            "priority": priority,
            "urgency": urgency
        },
        "classification_metadata": {
            "classifier_version": "1.0",
            "classification_timestamp": datetime.utcnow().isoformat()
        }
    }

@worker("process_by_type")
async def process_by_type(context: Dict[str, Any]) -> Dict[str, Any]:
    """Process event based on its classification."""
    classified_event = context["classified_event"]
    category = classified_event["category"]
    
    processing_result = {}
    
    if category == "user_engagement":
        processing_result = await process_engagement_event(classified_event)
    elif category == "system_error":
        processing_result = await process_error_event(classified_event)
    elif category == "business_transaction":
        processing_result = await process_transaction_event(classified_event)
    else:
        processing_result = await process_general_event(classified_event)
    
    return {
        "processed_event": classified_event,
        "processing_result": processing_result,
        "processing_category": category,
        "processing_timestamp": datetime.utcnow().isoformat()
    }

async def process_engagement_event(event):
    """Process user engagement events."""
    return {
        "action": "update_user_metrics",
        "metrics_updated": ["session_duration", "page_views"],
        "next_actions": ["recommend_content", "update_preferences"]
    }

async def process_error_event(event):
    """Process system error events."""
    return {
        "action": "create_incident",
        "severity": determine_error_severity(event),
        "notifications_sent": ["engineering_team", "ops_team"],
        "auto_remediation": "attempted"
    }

async def process_transaction_event(event):
    """Process business transaction events."""
    return {
        "action": "update_revenue_metrics",
        "fraud_check": "passed",
        "customer_lifecycle": "updated",
        "next_actions": ["send_receipt", "update_inventory"]
    }

async def process_general_event(event):
    """Process general events."""
    return {
        "action": "log_and_archive",
        "storage_location": "general_events_store",
        "retention_policy": "30_days"
    }

def determine_error_severity(event):
    """Determine error severity based on event data."""
    error_keywords = event.get("data", {}).get("error_message", "").lower()
    
    if any(keyword in error_keywords for keyword in ["critical", "fatal", "security"]):
        return "critical"
    elif any(keyword in error_keywords for keyword in ["warning", "timeout"]):
        return "medium"
    else:
        return "low"

def generate_event_id():
    """Generate unique event ID."""
    import uuid
    return str(uuid.uuid4())[:8]
```

## Workflow Composition Patterns

### 1. Nested Workflow Pattern

```python
# Main workflow that calls sub-workflows
def create_master_workflow():
    """Master workflow that orchestrates sub-workflows."""
    return (WorkflowBuilder("master_workflow")
        .add_step("prepare_data", "prepare_data")
        .add_step("execute_sub_workflow_1", "execute_sub_workflow")
        .add_step("execute_sub_workflow_2", "execute_sub_workflow")
        .add_step("consolidate_results", "consolidate_results")
        .build())

@worker("execute_sub_workflow")
async def execute_sub_workflow(context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a sub-workflow within the main workflow."""
    # This could integrate with a hierarchical orchestrator
    # For now, simulate sub-workflow execution
    
    sub_workflow_type = context.get("sub_workflow_type", "default")
    input_data = context.get("sub_workflow_input", {})
    
    # Simulate sub-workflow execution
    if sub_workflow_type == "data_analysis":
        result = await simulate_analysis_workflow(input_data)
    elif sub_workflow_type == "data_export":
        result = await simulate_export_workflow(input_data)
    else:
        result = await simulate_default_workflow(input_data)
    
    return {
        "sub_workflow_result": result,
        "sub_workflow_type": sub_workflow_type,
        "execution_time": "3.2s"
    }
```

### 2. Dynamic Workflow Pattern

```python
# Workflow that adapts based on runtime conditions
@worker("dynamic_router")
async def dynamic_router(context: Dict[str, Any]) -> Dict[str, Any]:
    """Route to different processing based on runtime analysis."""
    data = context["data"]
    
    # Analyze data to determine optimal processing path
    analysis = analyze_data_characteristics(data)
    
    if analysis["complexity"] > 0.8:
        processing_steps = ["complex_analysis", "detailed_validation", "expert_review"]
    elif analysis["data_type"] == "time_series":
        processing_steps = ["time_series_analysis", "trend_detection", "forecasting"]
    elif analysis["size"] > 1000000:  # Large data
        processing_steps = ["chunk_data", "parallel_processing", "merge_results"]
    else:
        processing_steps = ["standard_processing", "basic_validation"]
    
    return {
        "dynamic_steps": processing_steps,
        "analysis_results": analysis,
        "routing_decision": "adaptive_processing",
        "estimated_duration": estimate_processing_time(processing_steps)
    }

def analyze_data_characteristics(data):
    """Analyze data to determine processing strategy."""
    return {
        "size": len(str(data)),
        "complexity": calculate_complexity_score(data),
        "data_type": infer_data_type(data),
        "quality": assess_data_quality(data)
    }
```

These workflow patterns provide comprehensive templates for building complex, resilient, and adaptive workflows with the MultiAgents Framework. Each pattern addresses specific use cases and can be combined or modified based on application requirements.