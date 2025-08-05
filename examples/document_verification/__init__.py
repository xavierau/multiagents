"""
Document Verification System
===========================

A comprehensive document verification workflow example demonstrating:
- Multi-stage document processing pipeline
- DSPy-powered intelligent analysis
- Real-time monitoring and observability
- Error handling with compensation patterns
- Production-ready architecture

Key Components:
- tools.py: Reusable document processing tools
- workers.py: DSPy-powered verification workers
- workflow.py: Workflow definitions and orchestration
- main.py: Application entry point with monitoring

Usage:
    python main.py [--workflow-type full] [--document-path path/to/doc.pdf]

For detailed documentation, see README.md
"""

__version__ = "1.0.0"
__author__ = "Multiagents Framework"
__description__ = "Document Verification Workflow Example"

# Import main components for easy access
from .workflow import (
    create_document_verification_workflow,
    create_identity_only_workflow,
    create_financial_only_workflow,
    get_workflow_by_type
)

from .workers import (
    document_processor_worker,
    document_classifier_worker,
    identity_document_verifier_worker,
    financial_document_analyzer_worker,
    compliance_checker_worker,
    fraud_detector_worker,
    verification_decision_maker_worker,
    notification_dispatcher_worker,
    result_archiver_worker
)

from .tools import (
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

__all__ = [
    # Workflows
    "create_document_verification_workflow",
    "create_identity_only_workflow", 
    "create_financial_only_workflow",
    "get_workflow_by_type",
    
    # Workers
    "document_processor_worker",
    "document_classifier_worker",
    "identity_document_verifier_worker",
    "financial_document_analyzer_worker",
    "compliance_checker_worker",
    "fraud_detector_worker",
    "verification_decision_maker_worker",
    "notification_dispatcher_worker",
    "result_archiver_worker",
    
    # Tools
    "validate_document_format",
    "extract_text_from_pdf",
    "perform_ocr",
    "extract_document_entities",
    "verify_document_against_database",
    "check_fraud_indicators",
    "validate_compliance_requirements",
    "store_verification_result",
    "send_verification_notification",
    "cleanup_temporary_files"
]