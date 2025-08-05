"""
Document Processing Tools
========================

Reusable tools for document verification workflow.
These tools handle file operations, OCR, database lookups, and API integrations.
"""

import asyncio
import base64
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import httpx
from PIL import Image
import fitz  # PyMuPDF

from multiagents import tool


# ===========================================
# File Processing Tools
# ===========================================

@tool("validate_document_format")
def validate_document_format(file_path: str, allowed_formats: List[str] = None) -> Dict[str, Any]:
    """Validate document format and extract basic metadata."""
    if allowed_formats is None:
        allowed_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.doc', '.docx', '.txt']
    
    path = Path(file_path)
    
    if not path.exists():
        return {
            "valid": False,
            "error": "File does not exist",
            "file_path": file_path
        }
    
    file_extension = path.suffix.lower()
    file_size = path.stat().st_size
    
    # Check format
    if file_extension not in allowed_formats:
        return {
            "valid": False,
            "error": f"Unsupported format: {file_extension}",
            "supported_formats": allowed_formats,
            "file_path": file_path
        }
    
    # Check file size (max 50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    if file_size > max_size:
        return {
            "valid": False,
            "error": f"File too large: {file_size} bytes (max: {max_size})",
            "file_path": file_path
        }
    
    # Calculate file hash for duplicate detection
    with open(file_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    return {
        "valid": True,
        "file_path": file_path,
        "file_extension": file_extension,
        "file_size": file_size,
        "file_hash": file_hash,
        "validated_at": datetime.utcnow().isoformat()
    }


@tool("extract_text_from_pdf")
def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract text content from PDF document."""
    try:
        doc = fitz.open(file_path)
        text_content = ""
        page_count = len(doc)
        
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            text_content += page.get_text()
        
        doc.close()
        
        # Basic text analysis
        word_count = len(text_content.split())
        char_count = len(text_content)
        
        return {
            "success": True,
            "text_content": text_content,
            "page_count": page_count,
            "word_count": word_count,
            "char_count": char_count,
            "extracted_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"PDF extraction failed: {str(e)}",
            "file_path": file_path
        }


@tool("perform_ocr")
async def perform_ocr(file_path: str) -> Dict[str, Any]:
    """Perform OCR on image documents using mock OCR service."""
    # Mock OCR implementation - in production, use services like:
    # - Google Cloud Vision API
    # - AWS Textract
    # - Azure Computer Vision
    # - Tesseract OCR
    
    try:
        # Validate image file
        img = Image.open(file_path)
        width, height = img.size
        
        # Simulate OCR processing time
        await asyncio.sleep(1.0)
        
        # Mock OCR results based on filename patterns
        filename = Path(file_path).name.lower()
        
        if "license" in filename or "driver" in filename:
            ocr_text = """
            DRIVER LICENSE
            State of California
            
            Name: JOHN DOE
            DOB: 01/15/1985
            License No: D1234567
            Address: 123 Main St, Anytown, CA 90210
            Expires: 01/15/2025
            Class: C
            """
        elif "passport" in filename:
            ocr_text = """
            PASSPORT
            United States of America
            
            Name: JANE SMITH
            Passport No: 123456789
            DOB: 03/22/1990
            Place of Birth: New York, NY
            Issue Date: 05/10/2020
            Expiration: 05/10/2030
            """
        elif "bank" in filename or "statement" in filename:
            ocr_text = """
            BANK STATEMENT
            National Bank
            
            Account Holder: JOHN DOE
            Account Number: ****5678
            Statement Period: 01/01/2024 - 01/31/2024
            
            Beginning Balance: $2,500.00
            Ending Balance: $3,250.00
            """
        elif "tax" in filename or "w2" in filename:
            ocr_text = """
            Form W-2 Wage and Tax Statement
            
            Employee: JOHN DOE
            SSN: ***-**-1234
            Employer: Tech Company Inc
            
            Wages: $75,000.00
            Federal Tax Withheld: $12,500.00
            Year: 2023
            """
        else:
            ocr_text = f"Sample OCR text extracted from {filename}"
        
        # Calculate confidence score based on image quality
        confidence = min(0.95, 0.7 + (min(width, height) / 2000) * 0.25)
        
        return {
            "success": True,
            "ocr_text": ocr_text.strip(),
            "confidence": confidence,
            "image_dimensions": {"width": width, "height": height},
            "processing_time": 1.0,
            "extracted_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"OCR processing failed: {str(e)}",
            "file_path": file_path
        }


# ===========================================
# Document Analysis Tools
# ===========================================

@tool("extract_document_entities")
def extract_document_entities(text_content: str, document_type: str = "general") -> Dict[str, Any]:
    """Extract structured entities from document text using pattern matching."""
    entities = {}
    
    try:
        # Date patterns
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{2,4}\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text_content, re.IGNORECASE))
        entities["dates"] = list(set(dates))
        
        # SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        entities["ssn"] = re.findall(ssn_pattern, text_content)
        
        # Phone patterns
        phone_patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\b\d{10}\b'
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text_content))
        entities["phone_numbers"] = list(set(phones))
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities["emails"] = re.findall(email_pattern, text_content)
        
        # Address patterns (simplified)
        address_pattern = r'\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln)'
        entities["addresses"] = re.findall(address_pattern, text_content, re.IGNORECASE)
        
        # Document-specific patterns
        if document_type == "drivers_license":
            license_pattern = r'License\s*No:?\s*([A-Z0-9]+)'
            entities["license_number"] = re.findall(license_pattern, text_content, re.IGNORECASE)
            
            class_pattern = r'Class:?\s*([A-Z]+)'
            entities["license_class"] = re.findall(class_pattern, text_content, re.IGNORECASE)
            
        elif document_type == "passport":
            passport_pattern = r'Passport\s*No:?\s*([A-Z0-9]+)'
            entities["passport_number"] = re.findall(passport_pattern, text_content, re.IGNORECASE)
            
        elif document_type == "bank_statement":
            account_pattern = r'Account\s*Number:?\s*([*\d]+)'
            entities["account_number"] = re.findall(account_pattern, text_content, re.IGNORECASE)
            
            balance_pattern = r'\$[\d,]+\.\d{2}'
            entities["monetary_amounts"] = re.findall(balance_pattern, text_content)
        
        return {
            "success": True,
            "entities": entities,
            "entity_count": sum(len(v) if isinstance(v, list) else 1 for v in entities.values()),
            "extracted_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Entity extraction failed: {str(e)}"
        }


# ===========================================
# Verification & Validation Tools
# ===========================================

@tool("verify_document_against_database")
async def verify_document_against_database(document_data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
    """Verify document information against mock government/institutional databases."""
    # Mock database verification - in production, integrate with:
    # - DMV databases for driver's licenses
    # - Passport verification services
    # - Bank verification APIs
    # - Credit reporting agencies
    
    await asyncio.sleep(0.5)  # Simulate API call delay
    
    try:
        entities = document_data.get("entities", {})
        verification_results = {}
        
        if document_type == "drivers_license":
            license_numbers = entities.get("license_number", [])
            if license_numbers:
                # Mock DMV verification
                verification_results["license_valid"] = True
                verification_results["license_status"] = "active"
                verification_results["verified_against"] = "DMV_DATABASE"
            else:
                verification_results["license_valid"] = False
                verification_results["error"] = "No license number found"
                
        elif document_type == "passport":
            passport_numbers = entities.get("passport_number", [])
            if passport_numbers:
                # Mock passport verification
                verification_results["passport_valid"] = True
                verification_results["passport_status"] = "valid"
                verification_results["verified_against"] = "STATE_DEPARTMENT"
            else:
                verification_results["passport_valid"] = False
                verification_results["error"] = "No passport number found"
                
        elif document_type == "bank_statement":
            account_numbers = entities.get("account_number", [])
            if account_numbers:
                # Mock bank verification
                verification_results["account_valid"] = True
                verification_results["account_status"] = "active"
                verification_results["verified_against"] = "BANK_API"
            else:
                verification_results["account_valid"] = False
                verification_results["error"] = "No account number found"
        
        # General verification checks
        dates = entities.get("dates", [])
        if dates:
            verification_results["has_valid_dates"] = True
            verification_results["date_check"] = "passed"
        
        return {
            "success": True,
            "verification_results": verification_results,
            "verified_at": datetime.utcnow().isoformat(),
            "confidence_score": 0.85  # Mock confidence
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Database verification failed: {str(e)}"
        }


@tool("check_fraud_indicators")
def check_fraud_indicators(document_data: Dict[str, Any], file_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze document for potential fraud indicators."""
    try:
        fraud_indicators = []
        risk_score = 0.0
        
        # Check file metadata for tampering signs
        if file_metadata.get("file_size", 0) < 1000:  # Very small file
            fraud_indicators.append("Unusually small file size")
            risk_score += 0.2
            
        # Check OCR confidence
        ocr_confidence = document_data.get("confidence", 1.0)
        if ocr_confidence < 0.7:
            fraud_indicators.append("Low OCR confidence - possible image manipulation")
            risk_score += 0.3
            
        # Check for suspicious patterns in extracted text
        text_content = document_data.get("ocr_text", "") or document_data.get("text_content", "")
        
        # Look for inconsistent formatting
        if len(set(re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text_content))) > 3:
            fraud_indicators.append("Multiple date formats detected")
            risk_score += 0.1
            
        # Check for missing standard fields
        entities = document_data.get("entities", {})
        if not entities.get("dates"):
            fraud_indicators.append("No dates found in document")
            risk_score += 0.2
            
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "HIGH"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        return {
            "success": True,
            "fraud_indicators": fraud_indicators,
            "risk_score": min(risk_score, 1.0),
            "risk_level": risk_level,
            "requires_manual_review": risk_score >= 0.5,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Fraud analysis failed: {str(e)}"
        }


@tool("validate_compliance_requirements")
def validate_compliance_requirements(document_data: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Validate document against compliance requirements."""
    try:
        compliance_results = {}
        missing_requirements = []
        
        entities = document_data.get("entities", {})
        required_fields = requirements.get("required_fields", [])
        
        # Check required fields
        for field in required_fields:
            if field == "dates" and not entities.get("dates"):
                missing_requirements.append("Valid dates")
            elif field == "ssn" and not entities.get("ssn"):
                missing_requirements.append("Social Security Number")
            elif field == "addresses" and not entities.get("addresses"):
                missing_requirements.append("Address information")
            elif field == "phone_numbers" and not entities.get("phone_numbers"):
                missing_requirements.append("Phone number")
                
        # Check document age requirements
        max_age_days = requirements.get("max_document_age_days", 90)
        dates = entities.get("dates", [])
        if dates:
            # For simplicity, assume the first date is the document date
            # In production, you'd use more sophisticated date parsing
            compliance_results["document_age_check"] = "passed"
        else:
            missing_requirements.append("Document date for age verification")
            
        # Check signature requirements
        if requirements.get("signature_required", False):
            # Mock signature detection - in production, use image processing
            text_content = document_data.get("ocr_text", "") or document_data.get("text_content", "")
            if "signature" not in text_content.lower():
                missing_requirements.append("Digital or physical signature")
        
        compliance_score = 1.0 - (len(missing_requirements) / max(len(required_fields), 1))
        
        return {
            "success": True,
            "compliance_results": compliance_results,
            "missing_requirements": missing_requirements,
            "compliance_score": compliance_score,
            "is_compliant": len(missing_requirements) == 0,
            "validated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Compliance validation failed: {str(e)}"
        }


# ===========================================
# Database & Storage Tools
# ===========================================

@tool("store_verification_result")
async def store_verification_result(verification_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store verification results in database."""
    try:
        # Mock database storage - in production, use proper database
        db_path = "/tmp/document_verification.db"
        
        # Initialize database if needed
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT,
                file_path TEXT,
                verification_status TEXT,
                fraud_risk_level TEXT,
                compliance_score REAL,
                created_at TEXT,
                data TEXT
            )
        ''')
        
        # Insert verification result
        cursor.execute('''
            INSERT INTO verification_results 
            (document_id, file_path, verification_status, fraud_risk_level, compliance_score, created_at, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            verification_data.get("document_id"),
            verification_data.get("file_path"),
            verification_data.get("status"),
            verification_data.get("fraud_risk_level"),
            verification_data.get("compliance_score"),
            datetime.utcnow().isoformat(),
            json.dumps(verification_data)
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "result_id": result_id,
            "stored_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Database storage failed: {str(e)}"
        }


@tool("send_verification_notification")
async def send_verification_notification(recipient: str, verification_result: Dict[str, Any], notification_type: str = "completion") -> Dict[str, Any]:
    """Send notification about verification results."""
    try:
        # Mock notification service - in production, integrate with:
        # - Email services (SendGrid, AWS SES)
        # - SMS services (Twilio, AWS SNS)
        # - Slack/Teams webhooks
        # - Push notification services
        
        await asyncio.sleep(0.2)  # Simulate sending delay
        
        status = verification_result.get("status", "unknown")
        file_path = verification_result.get("file_path", "unknown")
        
        if notification_type == "completion":
            message = f"Document verification completed for {file_path}. Status: {status}"
        elif notification_type == "fraud_alert":
            message = f"FRAUD ALERT: High-risk document detected - {file_path}"
        elif notification_type == "compliance_failure":
            message = f"Compliance check failed for document {file_path}"
        else:
            message = f"Document verification update: {status}"
            
        print(f"📧 Notification sent to {recipient}: {message}")
        
        return {
            "success": True,
            "notification_id": f"NOTIF-{datetime.now().timestamp():.0f}",
            "recipient": recipient,
            "message": message,
            "notification_type": notification_type,
            "sent_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Notification failed: {str(e)}"
        }


# ===========================================
# Cleanup & Maintenance Tools
# ===========================================

@tool("cleanup_temporary_files")
def cleanup_temporary_files(file_paths: List[str]) -> Dict[str, Any]:
    """Clean up temporary files created during processing."""
    try:
        cleaned_files = []
        failed_files = []
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path) and "/tmp/" in file_path:
                    os.remove(file_path)
                    cleaned_files.append(file_path)
            except Exception as e:
                failed_files.append({"file": file_path, "error": str(e)})
        
        return {
            "success": True,
            "cleaned_files": cleaned_files,
            "failed_files": failed_files,
            "cleaned_count": len(cleaned_files),
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Cleanup failed: {str(e)}"
        }