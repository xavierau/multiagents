"""
Basic worker implementations for the MultiAgents framework.

This module demonstrates simple worker patterns including:
- Input validation
- Data processing 
- Result persistence
- Compensation/rollback logic
"""

import asyncio
import logging
from typing import Dict, Any

from multiagents import worker, WorkerManager


logger = logging.getLogger(__name__)


@worker("input-validator")
async def validate_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate input data and ensure required fields are present."""
    
    logger.info("Validating input data: %s", data)
    
    # Simulate validation logic
    required_fields = ["input", "user_id"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(data["input"], str):
        raise ValueError("Input must be a string")
    
    if len(data["input"]) < 1:
        raise ValueError("Input cannot be empty")
    
    # Add validation metadata
    validated_data = data.copy()
    validated_data["validation"] = {
        "status": "passed",
        "fields_checked": required_fields,
        "validated_at": "2024-01-01T00:00:00Z"
    }
    
    logger.info("Input validation successful")
    return validated_data


@worker("data-processor")
async def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process the validated data and transform it."""
    
    logger.info("Processing data: %s", data.get("input", ""))
    
    # Simulate processing work
    await asyncio.sleep(0.1)  # Simulate processing time
    
    processed_input = data["input"].upper()
    word_count = len(data["input"].split())
    
    # Create processed result
    result = data.copy()
    result["processed"] = {
        "original": data["input"],
        "transformed": processed_input,
        "word_count": word_count,
        "processed_at": "2024-01-01T00:00:00Z"
    }
    
    logger.info("Data processing completed: %d words processed", word_count)
    return result


@worker("result-saver")
async def save_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """Save the processed result to storage."""
    
    logger.info("Saving result for user: %s", data.get("user_id", "unknown"))
    
    # Simulate saving to database/storage
    await asyncio.sleep(0.05)  # Simulate I/O time
    
    # Generate save metadata
    save_id = f"save_{data.get('user_id', 'unknown')}_001"
    
    result = data.copy()
    result["saved"] = {
        "save_id": save_id,
        "location": f"/data/results/{save_id}.json",
        "saved_at": "2024-01-01T00:00:00Z",
        "status": "success"
    }
    
    logger.info("Result saved successfully with ID: %s", save_id)
    return result


# Compensation Workers

@worker("cleanup-saver")
async def cleanup_save_operation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker to cleanup failed save operations."""
    
    logger.info("Performing cleanup for failed save operation")
    
    # Simulate cleanup logic
    save_id = data.get("saved", {}).get("save_id")
    if save_id:
        logger.info("Cleaning up save ID: %s", save_id)
        # Would delete the saved file/database record here
    
    result = data.copy()
    result["compensation"] = {
        "action": "cleanup_save",
        "cleaned_save_id": save_id,
        "cleaned_at": "2024-01-01T00:00:00Z"
    }
    
    logger.info("Save cleanup completed")
    return result


@worker("rollback-processor")
async def rollback_processing(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker to rollback processing operations."""
    
    logger.info("Rolling back data processing operations")
    
    # Remove processed data
    result = data.copy()
    if "processed" in result:
        original_input = result["processed"]["original"]
        del result["processed"]
        
        result["compensation"] = {
            "action": "rollback_processing",
            "restored_input": original_input,
            "rolled_back_at": "2024-01-01T00:00:00Z"
        }
        
        logger.info("Processing rollback completed, restored original input")
    
    return result


def setup_workers(worker_manager: WorkerManager) -> None:
    """Register all workers with the worker manager."""
    
    workers = [
        validate_input,
        process_data,
        save_result,
        cleanup_save_operation,
        rollback_processing
    ]
    
    for worker_func in workers:
        worker_manager.register_worker(worker_func)
        logger.info("Registered worker: %s", worker_func.__name__)
    
    logger.info("All workers registered successfully")