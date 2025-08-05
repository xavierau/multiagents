"""
Comprehensive Test Suite for Document Verification System
========================================================

Tests cover:
- Individual worker functionality
- Tool integrations
- Workflow execution
- Error handling and compensation
- Integration scenarios
"""

import asyncio
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the parent directories to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from multiagents.orchestrator import Orchestrator
from multiagents.event_bus.redis_bus import RedisEventBus
from multiagents.worker_sdk import WorkerManager
from multiagents.core.factory import create_simple_framework

# Import our modules
from tools import (
    validate_document_format,
    extract_text_from_pdf,
    perform_ocr,
    extract_document_entities,
    verify_document_against_database,
    check_fraud_indicators,
    validate_compliance_requirements,
    store_verification_result,
    send_verification_notification,
    cleanup_temporary_files
)

from workers import (
    document_processor_worker,
    document_classifier_worker,
    identity_document_verifier_worker,
    financial_document_analyzer_worker,
    compliance_checker_worker,
    fraud_detector_worker,
    verification_decision_maker_worker,
    notification_dispatcher_worker,
    result_archiver_worker,
    cleanup_failed_processing_worker,
    revert_verification_storage_worker,
    send_failure_notification_worker
)

from workflow import (
    create_document_verification_workflow,
    create_identity_only_workflow,
    create_financial_only_workflow,
    get_workflow_by_type
)


class TestDocumentTools:
    """Test the document processing tools."""
    
    def test_validate_document_format_valid_file(self):
        """Test document format validation with valid file."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Mock PDF content")
            temp_path = temp_file.name
        
        try:
            result = validate_document_format(temp_path)
            
            assert result["valid"] is True
            assert result["file_extension"] == ".pdf"
            assert result["file_size"] > 0
            assert "file_hash" in result
            
        finally:
            os.unlink(temp_path)
    
    def test_validate_document_format_invalid_extension(self):
        """Test document format validation with invalid extension."""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as temp_file:
            temp_file.write(b"Not a document")
            temp_path = temp_file.name
        
        try:
            result = validate_document_format(temp_path)
            
            assert result["valid"] is False
            assert "Unsupported format" in result["error"]
            
        finally:
            os.unlink(temp_path)
    
    def test_validate_document_format_nonexistent_file(self):
        """Test document format validation with nonexistent file."""
        result = validate_document_format("/nonexistent/file.pdf")
        
        assert result["valid"] is False
        assert "File does not exist" in result["error"]
    
    def test_extract_document_entities_drivers_license(self):
        """Test entity extraction from driver's license text."""
        text_content = """
        DRIVER LICENSE
        Name: JOHN DOE
        DOB: 01/15/1985
        License No: D1234567
        Address: 123 Main St, Anytown, CA 90210
        Expires: 01/15/2025
        """
        
        result = extract_document_entities(text_content, "drivers_license")
        
        assert result["success"] is True
        entities = result["entities"]
        assert len(entities["dates"]) > 0
        assert len(entities["license_number"]) > 0
        assert len(entities["addresses"]) > 0
    
    def test_extract_document_entities_bank_statement(self):
        """Test entity extraction from bank statement text."""
        text_content = """
        BANK STATEMENT
        Account Holder: JOHN DOE
        Account Number: ****5678
        Beginning Balance: $2,500.00
        Ending Balance: $3,250.00
        """
        
        result = extract_document_entities(text_content, "bank_statement")
        
        assert result["success"] is True
        entities = result["entities"]
        assert len(entities["account_number"]) > 0
        assert len(entities["monetary_amounts"]) > 0
    
    @pytest.mark.asyncio
    async def test_perform_ocr_drivers_license(self):
        """Test OCR processing on a mock driver's license image."""
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='_drivers_license.jpg', delete=False) as temp_file:
            # Create a simple test image using PIL
            from PIL import Image
            img = Image.new('RGB', (800, 600), color='white')
            img.save(temp_file.name, 'JPEG')
            temp_path = temp_file.name
        
        try:
            result = await perform_ocr(temp_path)
            
            assert result["success"] is True
            assert "DRIVER LICENSE" in result["ocr_text"]
            assert result["confidence"] > 0
            assert "image_dimensions" in result
            
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_verify_document_against_database(self):
        """Test database verification functionality."""
        document_data = {
            "entities": {
                "license_number": ["D1234567"],
                "dates": ["01/15/2025"]
            }
        }
        
        result = await verify_document_against_database(document_data, "drivers_license")
        
        assert result["success"] is True
        assert "verification_results" in result
        assert result["confidence_score"] > 0
    
    def test_check_fraud_indicators_low_risk(self):
        """Test fraud detection with low-risk document."""
        document_data = {
            "confidence": 0.9,
            "ocr_text": "Normal document content"
        }
        file_metadata = {
            "file_size": 100000
        }
        
        result = check_fraud_indicators(document_data, file_metadata)
        
        assert result["success"] is True
        assert result["risk_level"] == "LOW"
        assert result["requires_manual_review"] is False
    
    def test_check_fraud_indicators_high_risk(self):
        """Test fraud detection with high-risk indicators."""
        document_data = {
            "confidence": 0.5,  # Low confidence
            "ocr_text": "Document with multiple date formats: 01/01/2024 2024-01-02 Jan 3, 2024 04/01/24"
        }
        file_metadata = {
            "file_size": 500  # Very small file
        }
        
        result = check_fraud_indicators(document_data, file_metadata)
        
        assert result["success"] is True
        assert result["risk_level"] in ["MEDIUM", "HIGH"]
        assert len(result["fraud_indicators"]) > 0
    
    def test_validate_compliance_requirements(self):
        """Test compliance validation."""
        document_data = {
            "entities": {
                "dates": ["01/15/2025"],
                "addresses": ["123 Main St"],
                "ssn": ["***-**-1234"]
            }
        }
        requirements = {
            "required_fields": ["dates", "addresses", "ssn"],
            "max_document_age_days": 90,
            "signature_required": False
        }
        
        result = validate_compliance_requirements(document_data, requirements)
        
        assert result["success"] is True
        assert result["is_compliant"] is True
        assert result["compliance_score"] > 0.8
    
    @pytest.mark.asyncio
    async def test_store_verification_result(self):
        """Test storing verification results."""
        verification_data = {
            "document_id": "DOC-12345",
            "file_path": "/test/document.pdf",
            "status": "approved",
            "fraud_risk_level": "LOW",
            "compliance_score": 0.95
        }
        
        result = await store_verification_result(verification_data)
        
        assert result["success"] is True
        assert "result_id" in result
        assert "stored_at" in result
    
    @pytest.mark.asyncio
    async def test_send_verification_notification(self):
        """Test sending verification notifications."""
        verification_result = {
            "status": "approved",
            "file_path": "/test/document.pdf"
        }
        
        result = await send_verification_notification(
            "test@example.com", 
            verification_result, 
            "completion"
        )
        
        assert result["success"] is True
        assert result["recipient"] == "test@example.com"
        assert "notification_id" in result
    
    def test_cleanup_temporary_files(self):
        """Test temporary file cleanup."""
        # Create temporary files
        temp_files = []
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(dir="/tmp", delete=False)
            temp_files.append(temp_file.name)
            temp_file.close()
        
        try:
            result = cleanup_temporary_files(temp_files)
            
            assert result["success"] is True
            assert result["cleaned_count"] == len(temp_files)
            
            # Verify files are actually deleted
            for file_path in temp_files:
                assert not os.path.exists(file_path)
                
        except Exception:
            # Cleanup in case of test failure
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)


class TestDocumentWorkers:
    """Test the document verification workers."""
    
    @pytest.mark.asyncio
    async def test_document_processor_worker_success(self):
        """Test successful document processing."""
        # Create a test text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("Test document content")
            temp_path = temp_file.name
        
        try:
            context = {"file_path": temp_path}
            result = await document_processor_worker(context)
            
            assert result["success"] is True
            assert "file_metadata" in result
            assert "content_data" in result
            assert "document_id" in result
            
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_document_processor_worker_invalid_file(self):
        """Test document processing with invalid file."""
        context = {"file_path": "/nonexistent/file.pdf"}
        result = await document_processor_worker(context)
        
        assert result["success"] is False
        assert "error" in result
        assert result["stage"] == "document_processing"
    
    @pytest.mark.asyncio 
    async def test_document_processor_worker_missing_path(self):
        """Test document processing with missing file path."""
        context = {}
        result = await document_processor_worker(context)
        
        assert result["success"] is False
        assert "No file path provided" in result["error"]
    
    @pytest.mark.asyncio
    async def test_notification_dispatcher_worker(self):
        """Test notification dispatcher worker."""
        context = {
            "verification_result": {
                "verification_status": "approved",
                "fraud_risk_level": "LOW",
                "is_compliant": True
            },
            "notification_config": {
                "recipients": ["test1@example.com", "test2@example.com"]
            }
        }
        
        result = await notification_dispatcher_worker(context)
        
        assert result["total_sent"] >= 0
        assert result["notification_type"] == "completion"
        assert "dispatched_at" in result
    
    @pytest.mark.asyncio
    async def test_result_archiver_worker(self):
        """Test result archiver worker."""
        context = {
            "verification_result": {
                "document_id": "DOC-12345",
                "status": "approved"
            },
            "temp_files": []
        }
        
        result = await result_archiver_worker(context)
        
        assert "storage_result" in result
        assert "cleanup_result" in result
        assert "archived_at" in result
    
    @pytest.mark.asyncio
    async def test_cleanup_failed_processing_worker(self):
        """Test cleanup compensation worker."""
        # Create temporary files for cleanup
        temp_files = []
        for i in range(2):
            temp_file = tempfile.NamedTemporaryFile(dir="/tmp", delete=False)
            temp_files.append(temp_file.name)
            temp_file.close()
        
        try:
            context = {
                "document_id": "DOC-FAILED",
                "temp_files": temp_files,
                "error_details": {
                    "error": "Processing failed",
                    "stage": "document_processing"
                }
            }
            
            result = await cleanup_failed_processing_worker(context)
            
            assert result["cleanup_completed"] is True
            assert "failure_record" in result
            assert result["stage"] == "cleanup_compensation"
            
        except Exception:
            # Cleanup in case of test failure
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)


class TestWorkflows:
    """Test workflow definitions and configurations."""
    
    def test_create_document_verification_workflow(self):
        """Test creating the main document verification workflow."""
        workflow = create_document_verification_workflow()
        
        assert workflow is not None
        assert workflow.get_id() == "document_verification"
        
        # Verify workflow has expected steps
        steps = workflow.get_steps()
        expected_steps = [
            "document_processing",
            "document_classification",
            "compliance_check",
            "fraud_detection",
            "verification_decision",
            "result_archiving",
            "notification_dispatch"
        ]
        
        step_names = [step.name for step in steps]
        for expected_step in expected_steps:
            assert expected_step in step_names
    
    def test_create_identity_only_workflow(self):
        """Test creating identity-only workflow."""
        workflow = create_identity_only_workflow()
        
        assert workflow is not None
        assert workflow.get_id() == "identity_verification_only"
        
        steps = workflow.get_steps()
        step_names = [step.name for step in steps]
        
        # Should include identity verification
        assert "identity_verification" in step_names
        # Should not include financial analysis
        assert "financial_analysis" not in step_names
    
    def test_create_financial_only_workflow(self):
        """Test creating financial-only workflow."""
        workflow = create_financial_only_workflow()
        
        assert workflow is not None
        assert workflow.get_id() == "financial_verification_only"
        
        steps = workflow.get_steps()
        step_names = [step.name for step in steps]
        
        # Should include financial analysis
        assert "financial_analysis" in step_names
        # Should not include identity verification
        assert "identity_verification" not in step_names
    
    def test_get_workflow_by_type(self):
        """Test workflow factory function."""
        # Test valid workflow types
        full_workflow = get_workflow_by_type("full")
        assert full_workflow.get_id() == "document_verification"
        
        identity_workflow = get_workflow_by_type("identity_only")
        assert identity_workflow.get_id() == "identity_verification_only"
        
        financial_workflow = get_workflow_by_type("financial_only")
        assert financial_workflow.get_id() == "financial_verification_only"
        
        # Test invalid workflow type
        with pytest.raises(ValueError, match="Unknown workflow type"):
            get_workflow_by_type("invalid_type")


class TestIntegrationScenarios:
    """Integration tests for complete workflow execution."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_document_verification(self):
        """Test complete document verification workflow (requires Redis)."""
        # Skip if Redis is not available (for CI/CD environments)
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
        except Exception:
            pytest.skip("Redis not available for integration test")
        
        # Create a test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("""
            DRIVER LICENSE
            Name: TEST USER
            DOB: 01/15/1990
            License No: T1234567
            Address: 123 Test St, Test City, CA 90210
            Expires: 01/15/2026
            """)
            temp_path = temp_file.name
        
        try:
            # Create framework
            workflow = create_identity_only_workflow()
            event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
            
            # Register workers
            workers_to_register = [
                document_processor_worker,
                document_classifier_worker,
                identity_document_verifier_worker,
                compliance_checker_worker,
                fraud_detector_worker,
                verification_decision_maker_worker,
                result_archiver_worker,
                notification_dispatcher_worker,
                cleanup_failed_processing_worker
            ]
            
            for worker in workers_to_register:
                worker_manager.register(worker)
            
            # Start framework
            await event_bus.start()
            await worker_manager.start()
            await orchestrator.start()
            
            # Execute workflow
            context = {
                "file_path": temp_path,
                "compliance_requirements": {
                    "required_fields": ["dates", "license_number"],
                    "max_document_age_days": 90
                },
                "notification_config": {
                    "recipients": ["test@example.com"]
                }
            }
            
            transaction_id = await orchestrator.execute_workflow(
                workflow.get_id(),
                context
            )
            
            # Wait for completion (with timeout)
            max_wait = 30  # seconds
            wait_time = 0
            completed_states = {"completed", "failed", "compensated", "cancelled"}
            
            while wait_time < max_wait:
                status = await orchestrator.get_status(transaction_id)
                if status['state'] in completed_states:
                    break
                await asyncio.sleep(1)
                wait_time += 1
            
            # Verify completion
            final_status = await orchestrator.get_status(transaction_id)
            assert final_status['state'] in completed_states
            assert len(final_status['step_results']) > 0
            
            # Stop framework
            await worker_manager.stop()
            await orchestrator.stop()
            await event_bus.stop()
            
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test workflow error handling and compensation."""
        # Skip if Redis is not available
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
        except Exception:
            pytest.skip("Redis not available for integration test")
        
        # Create framework
        workflow = create_identity_only_workflow()
        event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
        
        # Register workers
        worker_manager.register(document_processor_worker)
        worker_manager.register(cleanup_failed_processing_worker)
        
        # Start framework
        await event_bus.start()
        await worker_manager.start()
        await orchestrator.start()
        
        try:
            # Execute workflow with invalid file path (should trigger error handling)
            context = {
                "file_path": "/nonexistent/file.pdf",
                "notification_config": {
                    "recipients": ["test@example.com"]
                }
            }
            
            transaction_id = await orchestrator.execute_workflow(
                workflow.get_id(),
                context
            )
            
            # Wait for completion or compensation
            max_wait = 15
            wait_time = 0
            
            while wait_time < max_wait:
                status = await orchestrator.get_status(transaction_id)
                if status['state'] in {"failed", "compensated"}:
                    break
                await asyncio.sleep(1)
                wait_time += 1
            
            # Verify error was handled
            final_status = await orchestrator.get_status(transaction_id)
            assert final_status['state'] in {"failed", "compensated"}
            assert final_status.get('error') is not None
            
        finally:
            await worker_manager.stop()
            await orchestrator.stop()
            await event_bus.stop()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])