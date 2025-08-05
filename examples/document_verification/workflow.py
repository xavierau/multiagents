"""
Document Verification Workflow Definition
========================================

This module defines the comprehensive document verification workflow
with multiple stages, error handling, and compensation patterns.
"""

from multiagents.orchestrator import WorkflowBuilder
from .workers import (
    # Main processing workers
    document_processor_worker,
    document_classifier_worker,
    identity_document_verifier_worker,
    financial_document_analyzer_worker,
    compliance_checker_worker,
    fraud_detector_worker,
    verification_decision_maker_worker,
    notification_dispatcher_worker,
    result_archiver_worker,
    
    # Compensation workers
    cleanup_failed_processing_worker,
    revert_verification_storage_worker,
    send_failure_notification_worker
)


def create_document_verification_workflow():
    """
    Create the main document verification workflow.
    
    This workflow processes documents through multiple verification stages:
    1. Document Processing & Classification
    2. Specialized Analysis (Identity/Financial)
    3. Compliance & Fraud Checking
    4. Final Decision Making
    5. Result Archiving & Notification
    
    Each stage has appropriate compensation actions for error handling.
    """
    builder = WorkflowBuilder("document_verification")
    
    # Stage 1: Document Processing & Classification
    # ============================================
    builder.add_step(
        "document_processing",
        document_processor_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Extract content and metadata from document"
    )
    
    builder.add_step(
        "document_classification", 
        document_classifier_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Classify document type using AI analysis"
    )
    
    # Stage 2: Specialized Verification
    # =================================
    
    # Conditional step for identity documents
    builder.add_conditional_step(
        "identity_verification",
        identity_document_verifier_worker,
        condition=lambda context: context.get("document_type") in [
            "drivers_license", "passport", "national_id", "visa"
        ],
        compensation_worker=cleanup_failed_processing_worker,
        description="Verify identity documents against official databases"
    )
    
    # Conditional step for financial documents  
    builder.add_conditional_step(
        "financial_analysis",
        financial_document_analyzer_worker,
        condition=lambda context: context.get("document_type") in [
            "bank_statement", "tax_document", "pay_stub", "financial_report"
        ],
        compensation_worker=cleanup_failed_processing_worker,
        description="Analyze financial documents for accuracy and risk"
    )
    
    # Stage 3: Compliance & Fraud Detection
    # ====================================
    builder.add_step(
        "compliance_check",
        compliance_checker_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Validate document against compliance requirements"
    )
    
    builder.add_step(
        "fraud_detection",
        fraud_detector_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Detect potential fraud indicators and assess risk"
    )
    
    # Stage 4: Decision Making
    # =======================
    builder.add_step(
        "verification_decision",
        verification_decision_maker_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Make final verification decision based on all analyses"
    )
    
    # Stage 5: Result Processing & Notification
    # ========================================
    builder.add_step(
        "result_archiving",
        result_archiver_worker,
        compensation_worker=revert_verification_storage_worker,
        description="Store verification results and clean up temporary files"
    )
    
    builder.add_step(
        "notification_dispatch",
        notification_dispatcher_worker,
        compensation_worker=send_failure_notification_worker,
        description="Send notifications about verification results"
    )
    
    return builder.build()


def create_identity_only_workflow():
    """
    Create a simplified workflow for identity document verification only.
    Used for quick identity checks without full financial analysis.
    """
    builder = WorkflowBuilder("identity_verification_only")
    
    builder.add_step(
        "document_processing",
        document_processor_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "document_classification",
        document_classifier_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "identity_verification",
        identity_document_verifier_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "compliance_check",
        compliance_checker_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "fraud_detection",
        fraud_detector_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "verification_decision",
        verification_decision_maker_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "result_archiving",
        result_archiver_worker,
        compensation_worker=revert_verification_storage_worker
    )
    
    builder.add_step(
        "notification_dispatch",
        notification_dispatcher_worker,
        compensation_worker=send_failure_notification_worker
    )
    
    return builder.build()


def create_financial_only_workflow():
    """
    Create a workflow focused on financial document verification.
    Used when identity is already verified and only financial analysis is needed.
    """
    builder = WorkflowBuilder("financial_verification_only")
    
    builder.add_step(
        "document_processing",
        document_processor_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "document_classification",
        document_classifier_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "financial_analysis",
        financial_document_analyzer_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "compliance_check",
        compliance_checker_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "fraud_detection",
        fraud_detector_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "verification_decision",
        verification_decision_maker_worker,
        compensation_worker=cleanup_failed_processing_worker
    )
    
    builder.add_step(
        "result_archiving",
        result_archiver_worker,
        compensation_worker=revert_verification_storage_worker
    )
    
    builder.add_step(
        "notification_dispatch",
        notification_dispatcher_worker,
        compensation_worker=send_failure_notification_worker
    )
    
    return builder.build()


def create_batch_verification_workflow():
    """
    Create a workflow for processing multiple documents in batch.
    This workflow processes documents in parallel when possible.
    """
    builder = WorkflowBuilder("batch_document_verification")
    
    # Process each document through the main pipeline
    # In a real implementation, this would use parallel processing
    builder.add_step(
        "batch_document_processing",
        document_processor_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Process multiple documents in batch"
    )
    
    builder.add_step(
        "batch_classification",
        document_classifier_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Classify all documents"
    )
    
    # Parallel verification steps
    builder.add_step(
        "batch_identity_verification",
        identity_document_verifier_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Verify identity documents in batch"
    )
    
    builder.add_step(
        "batch_financial_analysis",
        financial_document_analyzer_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Analyze financial documents in batch"
    )
    
    builder.add_step(
        "batch_compliance_check",
        compliance_checker_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Check compliance for all documents"
    )
    
    builder.add_step(
        "batch_fraud_detection",
        fraud_detector_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Detect fraud across document batch"
    )
    
    builder.add_step(
        "batch_decision_making",
        verification_decision_maker_worker,
        compensation_worker=cleanup_failed_processing_worker,
        description="Make decisions for all documents"
    )
    
    builder.add_step(
        "batch_result_archiving",
        result_archiver_worker,
        compensation_worker=revert_verification_storage_worker,
        description="Archive all batch results"
    )
    
    builder.add_step(
        "batch_notification_dispatch",
        notification_dispatcher_worker,
        compensation_worker=send_failure_notification_worker,
        description="Send batch completion notifications"
    )
    
    return builder.build()


def get_workflow_by_type(workflow_type: str):
    """
    Get the appropriate workflow based on the type requested.
    
    Args:
        workflow_type: One of 'full', 'identity_only', 'financial_only', 'batch'
        
    Returns:
        Workflow instance
    """
    workflows = {
        'full': create_document_verification_workflow,
        'identity_only': create_identity_only_workflow,
        'financial_only': create_financial_only_workflow,
        'batch': create_batch_verification_workflow
    }
    
    workflow_factory = workflows.get(workflow_type)
    if not workflow_factory:
        raise ValueError(f"Unknown workflow type: {workflow_type}. Available: {list(workflows.keys())}")
    
    return workflow_factory()


def create_test_context():
    """
    Create a test context for workflow development and testing.
    """
    return {
        "file_path": "/path/to/test/document.pdf",
        "document_type": "drivers_license",
        "compliance_requirements": {
            "required_fields": ["dates", "license_number", "addresses"],
            "max_document_age_days": 90,
            "signature_required": False
        },
        "notification_config": {
            "recipients": ["reviewer@example.com", "admin@example.com"],
            "failure_recipients": ["alerts@example.com"]
        },
        "processing_options": {
            "enable_ocr": True,
            "fraud_check_level": "standard",
            "auto_approve_threshold": 0.9
        }
    }