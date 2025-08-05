"""
Document Verification Workers
============================

DSPy-powered workers for intelligent document verification.
Each worker handles a specific stage of the verification pipeline.
"""

import os
from datetime import datetime
from typing import Dict, Any, List

from multiagents import worker, dspy_worker, tool
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


# ===========================================
# Basic Processing Workers
# ===========================================

@worker("document_processor")
async def document_processor_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Process document files and extract basic metadata."""
    file_path = context.get("file_path")
    if not file_path:
        return {
            "success": False,
            "error": "No file path provided",
            "stage": "document_processing"
        }
    
    # Validate document format
    validation_result = validate_document_format(file_path)
    if not validation_result["valid"]:
        return {
            "success": False,
            "error": validation_result["error"],
            "stage": "document_processing",
            "file_path": file_path
        }
    
    # Extract content based on file type
    file_extension = validation_result["file_extension"]
    
    if file_extension == ".pdf":
        content_result = extract_text_from_pdf(file_path)
    elif file_extension in [".jpg", ".jpeg", ".png", ".tiff"]:
        content_result = await perform_ocr(file_path)
    else:
        # For other text formats, read directly
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            content_result = {
                "success": True,
                "text_content": text_content,
                "word_count": len(text_content.split()),
                "char_count": len(text_content)
            }
        except Exception as e:
            content_result = {
                "success": False,
                "error": f"Failed to read file: {str(e)}"
            }
    
    if not content_result["success"]:
        return {
            "success": False,
            "error": content_result["error"],
            "stage": "document_processing",
            "file_path": file_path
        }
    
    return {
        "success": True,
        "file_metadata": validation_result,
        "content_data": content_result,
        "document_id": f"DOC-{datetime.now().timestamp():.0f}",
        "processed_at": datetime.utcnow().isoformat(),
        "stage": "document_processing"
    }


# ===========================================
# DSPy-Powered Intelligent Workers
# ===========================================

@dspy_worker("document_classifier",
            signature="document_content, file_metadata -> document_type: str, confidence: float, classification_reason: str",
            reasoning="chain_of_thought",
            model="gemini/gemini-1.5-pro")
async def document_classifier_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Classify document type using DSPy with chain-of-thought reasoning."""
    # DSPy will analyze the content and metadata to classify the document
    document_type = context.get("document_type", "unknown")
    confidence = context.get("confidence", 0.0)
    classification_reason = context.get("classification_reason", "")
    
    # Additional processing based on classification
    processing_rules = {
        "drivers_license": {
            "required_entities": ["license_number", "dates", "addresses"],
            "verification_priority": "high",
            "fraud_check_level": "standard"
        },
        "passport": {
            "required_entities": ["passport_number", "dates"],
            "verification_priority": "high",
            "fraud_check_level": "enhanced"
        },
        "bank_statement": {
            "required_entities": ["account_number", "monetary_amounts", "dates"],
            "verification_priority": "medium",
            "fraud_check_level": "standard"
        },
        "tax_document": {
            "required_entities": ["ssn", "monetary_amounts", "dates"],
            "verification_priority": "high",
            "fraud_check_level": "enhanced"
        },
        "unknown": {
            "required_entities": [],
            "verification_priority": "low",
            "fraud_check_level": "basic"
        }
    }
    
    rules = processing_rules.get(document_type, processing_rules["unknown"])
    
    return {
        "document_type": document_type,
        "confidence": confidence,
        "classification_reason": classification_reason,
        "processing_rules": rules,
        "needs_manual_review": confidence < 0.8,
        "classified_at": datetime.utcnow().isoformat(),
        "stage": "document_classification"
    }


@dspy_worker("identity_document_verifier",
            signature="""document_type, extracted_entities, verification_database_result -> 
                        identity_verified: bool, verification_confidence: float, 
                        verification_details: str, next_actions: list[str]""",
            tools=[verify_document_against_database],
            reasoning="react",
            max_iters=3,
            model="gemini/gemini-1.5-pro")
async def identity_document_verifier_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Verify identity documents using ReAct reasoning with database tools."""
    # DSPy will use ReAct to reason about verification and call database tools
    identity_verified = context.get("identity_verified", False)
    verification_confidence = context.get("verification_confidence", 0.0)
    verification_details = context.get("verification_details", "")
    next_actions = context.get("next_actions", [])
    
    # Additional verification logic
    document_type = context.get("document_type", "unknown")
    
    verification_result = {
        "identity_verified": identity_verified,
        "verification_confidence": verification_confidence,
        "verification_details": verification_details,
        "next_actions": next_actions,
        "document_type": document_type,
        "verified_at": datetime.utcnow().isoformat(),
        "stage": "identity_verification"
    }
    
    # Determine if manual review is needed
    verification_result["requires_manual_review"] = (
        verification_confidence < 0.7 or 
        not identity_verified or
        "manual_review" in next_actions
    )
    
    return verification_result


@dspy_worker("financial_document_analyzer",
            signature="""document_content, extracted_entities -> 
                        financial_summary: str, risk_assessment: str, 
                        compliance_status: str, anomalies_detected: list[str]""",
            reasoning="chain_of_thought",
            model="gemini/gemini-1.5-pro")
async def financial_document_analyzer_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze financial documents with detailed reasoning."""
    # DSPy will analyze financial content and provide structured insights
    financial_summary = context.get("financial_summary", "")
    risk_assessment = context.get("risk_assessment", "")
    compliance_status = context.get("compliance_status", "")
    anomalies_detected = context.get("anomalies_detected", [])
    
    # Calculate risk score based on anomalies
    risk_score = min(len(anomalies_detected) * 0.2, 1.0)
    
    if risk_score >= 0.8:
        risk_level = "HIGH"
    elif risk_score >= 0.5:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return {
        "financial_summary": financial_summary,
        "risk_assessment": risk_assessment,
        "compliance_status": compliance_status,
        "anomalies_detected": anomalies_detected,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "requires_escalation": risk_level in ["HIGH", "MEDIUM"],
        "analyzed_at": datetime.utcnow().isoformat(),
        "stage": "financial_analysis"
    }


@dspy_worker("compliance_checker",
            signature="""document_type, extracted_entities, compliance_requirements -> 
                        compliance_status: str, missing_requirements: list[str], 
                        compliance_score: float, recommendations: list[str]""",
            tools=[validate_compliance_requirements],
            reasoning="react",
            max_iters=4,
            model="gemini/gemini-1.5-pro")
async def compliance_checker_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Check document compliance using ReAct reasoning."""
    # DSPy will reason about compliance and use tools to validate requirements
    compliance_status = context.get("compliance_status", "unknown")
    missing_requirements = context.get("missing_requirements", [])
    compliance_score = context.get("compliance_score", 0.0)
    recommendations = context.get("recommendations", [])
    
    # Determine next actions based on compliance
    next_actions = []
    if compliance_score < 0.8:
        next_actions.append("request_additional_documentation")
    if missing_requirements:
        next_actions.append("notify_missing_requirements")
    if compliance_score < 0.5:
        next_actions.append("reject_document")
    
    return {
        "compliance_status": compliance_status,
        "missing_requirements": missing_requirements,
        "compliance_score": compliance_score,
        "recommendations": recommendations,
        "next_actions": next_actions,
        "is_compliant": compliance_score >= 0.8 and not missing_requirements,
        "checked_at": datetime.utcnow().isoformat(),
        "stage": "compliance_check"
    }


@dspy_worker("fraud_detector",
            signature="""document_content, file_metadata, extracted_entities -> 
                        fraud_risk_level: str, fraud_indicators: list[str], 
                        risk_explanation: str, investigation_needed: bool""",
            tools=[check_fraud_indicators],  
            reasoning="react",
            max_iters=4,
            model="gemini/gemini-1.5-pro")
async def fraud_detector_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Detect potential fraud using advanced reasoning and analysis tools."""
    # DSPy will analyze patterns and use tools to detect fraud indicators
    fraud_risk_level = context.get("fraud_risk_level", "LOW")
    fraud_indicators = context.get("fraud_indicators", [])
    risk_explanation = context.get("risk_explanation", "")
    investigation_needed = context.get("investigation_needed", False)
    
    # Calculate numeric risk score
    risk_scores = {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8, "CRITICAL": 1.0}
    risk_score = risk_scores.get(fraud_risk_level, 0.0)
    
    # Determine actions based on risk level
    actions = []
    if fraud_risk_level in ["HIGH", "CRITICAL"]:
        actions.extend(["immediate_alert", "freeze_processing", "manual_investigation"])
    elif fraud_risk_level == "MEDIUM":
        actions.extend(["flag_for_review", "enhanced_verification"])
    
    return {
        "fraud_risk_level": fraud_risk_level,
        "fraud_indicators": fraud_indicators,
        "risk_explanation": risk_explanation,
        "risk_score": risk_score,
        "investigation_needed": investigation_needed,
        "recommended_actions": actions,
        "requires_immediate_attention": fraud_risk_level in ["HIGH", "CRITICAL"],
        "analyzed_at": datetime.utcnow().isoformat(),
        "stage": "fraud_detection"
    }


@dspy_worker("verification_decision_maker",
            signature="""identity_verification, financial_analysis, compliance_check, fraud_detection -> 
                        final_decision: str, decision_confidence: float, 
                        decision_reasoning: str, required_actions: list[str]""",
            reasoning="chain_of_thought",
            model="gemini/gemini-1.5-pro")
async def verification_decision_maker_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Make final verification decision based on all analysis results."""
    # DSPy will synthesize all verification results to make a final decision
    final_decision = context.get("final_decision", "PENDING")
    decision_confidence = context.get("decision_confidence", 0.0)
    decision_reasoning = context.get("decision_reasoning", "")
    required_actions = context.get("required_actions", [])
    
    # Map decision to status codes
    decision_mapping = {
        "APPROVED": "approved",
        "REJECTED": "rejected",
        "PENDING": "pending_review",
        "CONDITIONAL": "conditional_approval"
    }
    
    verification_status = decision_mapping.get(final_decision, "pending_review")
    
    # Add standard actions based on decision
    if final_decision == "APPROVED":
        required_actions.append("store_verification_result")
        required_actions.append("send_approval_notification")
    elif final_decision == "REJECTED":
        required_actions.append("store_rejection_result")
        required_actions.append("send_rejection_notification")
    elif final_decision == "PENDING":
        required_actions.append("queue_for_manual_review")
        required_actions.append("send_pending_notification")
    
    return {
        "final_decision": final_decision,
        "verification_status": verification_status,
        "decision_confidence": decision_confidence,
        "decision_reasoning": decision_reasoning,
        "required_actions": list(set(required_actions)),  # Remove duplicates
        "needs_human_review": decision_confidence < 0.8 or final_decision in ["PENDING", "CONDITIONAL"],
        "decided_at": datetime.utcnow().isoformat(),
        "stage": "final_decision"
    }


# ===========================================
# Operational & Notification Workers
# ===========================================

@worker("notification_dispatcher")
async def notification_dispatcher_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch notifications based on verification results."""
    verification_result = context.get("verification_result", {})
    notification_config = context.get("notification_config", {})
    
    recipients = notification_config.get("recipients", ["admin@example.com"])
    
    notifications_sent = []
    failed_notifications = []
    
    # Determine notification type based on result
    verification_status = verification_result.get("verification_status", "unknown")
    fraud_risk_level = verification_result.get("fraud_risk_level", "LOW")
    
    notification_type = "completion"
    if fraud_risk_level in ["HIGH", "CRITICAL"]:
        notification_type = "fraud_alert"
    elif verification_status == "rejected":
        notification_type = "rejection"
    elif not verification_result.get("is_compliant", True):
        notification_type = "compliance_failure"
    
    # Send notifications
    for recipient in recipients:
        try:
            notification_result = await send_verification_notification(
                recipient, verification_result, notification_type
            )
            if notification_result["success"]:
                notifications_sent.append({
                    "recipient": recipient,
                    "notification_id": notification_result["notification_id"],
                    "type": notification_type
                })
            else:
                failed_notifications.append({
                    "recipient": recipient,
                    "error": notification_result["error"]
                })
        except Exception as e:
            failed_notifications.append({
                "recipient": recipient,
                "error": str(e)
            })
    
    return {
        "notifications_sent": notifications_sent,
        "failed_notifications": failed_notifications,
        "notification_type": notification_type,
        "total_sent": len(notifications_sent),
        "total_failed": len(failed_notifications),
        "dispatched_at": datetime.utcnow().isoformat(),
        "stage": "notification_dispatch"
    }


@worker("result_archiver") 
async def result_archiver_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Archive verification results and clean up temporary files."""
    verification_result = context.get("verification_result", {})
    temp_files = context.get("temp_files", [])
    
    # Store verification result
    storage_result = await store_verification_result(verification_result)
    
    # Clean up temporary files
    cleanup_result = {"success": True, "cleaned_files": [], "failed_files": []}
    if temp_files:
        cleanup_result = cleanup_temporary_files(temp_files)
    
    return {
        "storage_result": storage_result,
        "cleanup_result": cleanup_result,
        "archive_success": storage_result["success"] and cleanup_result["success"],
        "result_id": storage_result.get("result_id"),
        "files_cleaned": len(cleanup_result.get("cleaned_files", [])),
        "archived_at": datetime.utcnow().isoformat(),
        "stage": "result_archiving"
    }


# ===========================================
# Compensation Workers (Error Handling)
# ===========================================

@worker("cleanup_failed_processing")
async def cleanup_failed_processing_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker to clean up after failed document processing."""
    document_id = context.get("document_id")
    temp_files = context.get("temp_files", [])
    error_details = context.get("error_details", {})
    
    # Clean up any temporary files
    cleanup_result = {"success": True, "cleaned_files": []}
    if temp_files:
        cleanup_result = cleanup_temporary_files(temp_files)
    
    # Log the failure
    failure_record = {
        "document_id": document_id,
        "failure_reason": error_details.get("error", "Unknown error"),
        "failed_stage": error_details.get("stage", "unknown"),
        "cleanup_performed": cleanup_result["success"],
        "failed_at": datetime.utcnow().isoformat()
    }
    
    # In production, store failure record in database
    print(f"🧹 Cleaned up failed processing for document {document_id}")
    
    return {
        "cleanup_completed": True,
        "cleanup_result": cleanup_result,
        "failure_record": failure_record,
        "compensated_at": datetime.utcnow().isoformat(),
        "stage": "cleanup_compensation"
    }


@worker("revert_verification_storage")
async def revert_verification_storage_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker to revert stored verification results."""
    result_id = context.get("result_id")
    document_id = context.get("document_id")
    
    # In production, remove the stored result from database
    # For this mock implementation, we'll just log the action
    
    print(f"↩️ Reverted verification storage for document {document_id} (result_id: {result_id})")
    
    return {
        "revert_completed": True,
        "result_id": result_id,
        "document_id": document_id,
        "reverted_at": datetime.utcnow().isoformat(),
        "stage": "storage_compensation"
    }


@worker("send_failure_notification")
async def send_failure_notification_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker to notify about processing failures."""
    document_id = context.get("document_id")
    error_details = context.get("error_details", {})
    notification_config = context.get("notification_config", {})
    
    recipients = notification_config.get("failure_recipients", ["admin@example.com"])
    
    failure_notification = {
        "document_id": document_id,
        "status": "processing_failed",
        "error": error_details.get("error", "Unknown error"),
        "stage": error_details.get("stage", "unknown"),
        "failed_at": datetime.utcnow().isoformat()
    }
    
    notifications_sent = []
    for recipient in recipients:
        try:
            notification_result = await send_verification_notification(
                recipient, failure_notification, "processing_failure"
            )
            if notification_result["success"]:
                notifications_sent.append(notification_result["notification_id"])
        except Exception as e:
            print(f"Failed to send failure notification to {recipient}: {e}")
    
    return {
        "failure_notifications_sent": len(notifications_sent),
        "notification_ids": notifications_sent,
        "notified_at": datetime.utcnow().isoformat(),
        "stage": "failure_notification_compensation"
    }