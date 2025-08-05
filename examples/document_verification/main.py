"""
Document Verification Workflow - Main Application
================================================

Comprehensive document verification system demonstrating:
- Multi-stage document processing pipeline
- DSPy-powered intelligent analysis workers
- Real-time monitoring and observability
- Error handling with compensation patterns
- Production-ready architecture

Usage:
    python main.py [--workflow-type full] [--document-path path/to/doc.pdf]
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import dspy

# Add the multiagents package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from multiagents.orchestrator import Orchestrator
from multiagents.event_bus.redis_bus import RedisEventBus
from multiagents.worker_sdk import WorkerManager
from multiagents.core.factory import create_simple_framework
from multiagents.monitoring import (
    MonitoringConfig, EventMonitor, WorkerMonitor, MetricsCollector
)

# Import our workflow and workers
from workflow import (
    create_document_verification_workflow,
    create_identity_only_workflow,
    create_financial_only_workflow,
    create_batch_verification_workflow,
    get_workflow_by_type,
    create_test_context
)
from workers import (
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


def configure_dspy():
    """Configure DSPy with Gemini LLM."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  Warning: GOOGLE_API_KEY not found. DSPy workers will use mock responses.")
        print("   Set GOOGLE_API_KEY environment variable for real AI-powered analysis.")
        return False
    
    try:
        lm = dspy.LM(model="gemini/gemini-1.5-pro", api_key=api_key)
        dspy.configure(lm=lm)
        print("✅ DSPy configured with Gemini Pro")
        return True
    except Exception as e:
        print(f"❌ Failed to configure DSPy: {e}")
        return False


def create_sample_documents():
    """Create sample documents for testing."""
    sample_docs_dir = Path(__file__).parent / "sample_documents"
    sample_docs_dir.mkdir(exist_ok=True)
    
    # Create a simple text document for testing
    drivers_license_path = sample_docs_dir / "sample_drivers_license.txt"
    if not drivers_license_path.exists():
        drivers_license_content = """
DRIVER LICENSE
State of California

Name: JANE DOE
DOB: 03/15/1990
License No: D7654321
Address: 456 Oak Street, San Francisco, CA 94102
Expires: 03/15/2026
Class: C
Restrictions: None
        """.strip()
        
        with open(drivers_license_path, 'w') as f:
            f.write(drivers_license_content)
        print(f"📄 Created sample document: {drivers_license_path}")
    
    # Create a bank statement document
    bank_statement_path = sample_docs_dir / "sample_bank_statement.txt"
    if not bank_statement_path.exists():
        bank_statement_content = """
FIRST NATIONAL BANK
Monthly Statement

Account Holder: JANE DOE
Account Number: ****7890
Statement Period: 10/01/2024 - 10/31/2024

Beginning Balance: $3,450.00
Total Deposits: $2,500.00
Total Withdrawals: $1,850.00
Ending Balance: $4,100.00

Transactions:
10/01/2024 - Direct Deposit - ACME Corp - $2,500.00
10/05/2024 - Debit Purchase - Grocery Store - $125.50
10/10/2024 - ATM Withdrawal - $200.00
10/15/2024 - Online Transfer - Savings Account - $500.00
        """.strip()
        
        with open(bank_statement_path, 'w') as f:
            f.write(bank_statement_content)
        print(f"📄 Created sample document: {bank_statement_path}")
    
    return [str(drivers_license_path), str(bank_statement_path)]


async def monitor_workflow_progress(orchestrator: Orchestrator, transaction_id: str) -> Dict[str, Any]:
    """Monitor workflow progress with detailed status reporting."""
    print(f"\n📊 Monitoring Document Verification Workflow: {transaction_id}")
    print("=" * 70)
    
    completed_states = {"completed", "failed", "compensated", "cancelled"}
    last_step = None
    step_timings = {}
    
    while True:
        try:
            status = await orchestrator.get_status(transaction_id)
            current_step = status['current_step']
            
            # Track step transitions
            if current_step != last_step and current_step:
                step_timings[current_step] = datetime.now()
                if last_step:
                    duration = step_timings[current_step] - step_timings[last_step]
                    print(f"⏱️  Step '{last_step}' completed in {duration.total_seconds():.2f}s")
                
                print(f"🔄 Processing: {current_step}")
                last_step = current_step
            
            # Show detailed status
            print(f"\r📍 State: {status['state']} | Step: {current_step or 'N/A'} | "
                  f"Completed: {len(status['step_results'])}", end="")
            
            if status['error']:
                print(f"\n❌ Error detected: {status['error']}")
            
            # Check if workflow is complete
            if status['state'] in completed_states:
                print(f"\n\n✅ Workflow completed with state: {status['state']}")
                
                # Show step results
                if status['step_results']:
                    print("\n📋 Step Results:")
                    print("-" * 50)
                    for step, result in status['step_results'].items():
                        success = result.get('success', True)
                        stage = result.get('stage', step)
                        status_icon = "✅" if success else "❌"
                        print(f"{status_icon} {stage}: {step}")
                        
                        # Show key metrics for each step
                        if 'verification_confidence' in result:
                            print(f"   Confidence: {result['verification_confidence']:.2f}")
                        if 'compliance_score' in result:
                            print(f"   Compliance: {result['compliance_score']:.2f}")
                        if 'risk_level' in result:
                            print(f"   Risk Level: {result['risk_level']}")
                        if 'final_decision' in result:
                            print(f"   Decision: {result['final_decision']}")
                
                return status
            
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"\n❌ Error monitoring workflow: {e}")
            break
    
    return {}


async def run_document_verification(
    document_path: str,
    workflow_type: str = "full",
    compliance_requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run document verification workflow with specified parameters."""
    
    print(f"🚀 Starting Document Verification")
    print(f"📄 Document: {document_path}")
    print(f"🔧 Workflow: {workflow_type}")
    print("=" * 70)
    
    # Create framework components
    workflow = get_workflow_by_type(workflow_type)
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    # Get monitoring components
    event_monitor = event_bus.event_monitor
    worker_monitor = worker_manager.worker_monitor
    metrics_collector = event_bus.metrics_collector
    logger = event_bus.monitoring_logger
    
    try:
        # Start framework
        print("📡 Starting event bus...")
        await event_bus.start()
        
        print("👷 Registering workers...")
        
        # Register all workers
        workers_to_register = [
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
        ]
        
        for worker in workers_to_register:
            worker_manager.register(worker)
        
        print(f"✓ Registered {len(workers_to_register)} workers")
        
        # Start workers and orchestrator
        await worker_manager.start()
        print("🎯 Starting orchestrator...")
        await orchestrator.start()
        
        # Prepare context
        context = {
            "file_path": document_path,
            "compliance_requirements": compliance_requirements or {
                "required_fields": ["dates", "addresses"],
                "max_document_age_days": 90,
                "signature_required": False
            },
            "notification_config": {
                "recipients": ["reviewer@example.com"],
                "failure_recipients": ["alerts@example.com"]
            },
            "processing_options": {
                "enable_ocr": True,
                "fraud_check_level": "standard",
                "auto_approve_threshold": 0.85
            }
        }
        
        # Execute workflow
        print("🔄 Executing verification workflow...")
        transaction_id = await orchestrator.execute_workflow(
            workflow.get_id(),
            context
        )
        
        print(f"✓ Workflow started with transaction ID: {transaction_id}")
        
        # Monitor progress
        final_status = await monitor_workflow_progress(orchestrator, transaction_id)
        
        # Generate comprehensive report
        await generate_verification_report(
            final_status, event_monitor, worker_monitor, metrics_collector, transaction_id
        )
        
        return final_status
        
    except KeyboardInterrupt:
        print("\n⚠️  Workflow interrupted by user")
        return {"state": "interrupted"}
    except Exception as e:
        print(f"\n❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return {"state": "failed", "error": str(e)}
    finally:
        # Cleanup
        print("\n🧹 Cleaning up framework components...")
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()
        if logger:
            await logger.close()
        print("✓ Cleanup complete")


async def generate_verification_report(
    workflow_status: Dict[str, Any],
    event_monitor: EventMonitor,
    worker_monitor: WorkerMonitor, 
    metrics_collector: MetricsCollector,
    transaction_id: str
):
    """Generate a comprehensive verification report."""
    print("\n" + "=" * 70)
    print("📊 DOCUMENT VERIFICATION REPORT")
    print("=" * 70)
    
    # Workflow Summary
    print("🔍 WORKFLOW SUMMARY")
    print("-" * 30)
    print(f"Transaction ID: {transaction_id}")
    print(f"Final State: {workflow_status.get('state', 'unknown')}")
    print(f"Steps Completed: {len(workflow_status.get('step_results', {}))}")
    
    if workflow_status.get('error'):
        print(f"Error: {workflow_status['error']}")
    
    # Extract key verification results
    step_results = workflow_status.get('step_results', {})
    
    # Document Classification Results
    if 'document_classification' in step_results:
        classification = step_results['document_classification']
        print(f"\n📄 DOCUMENT ANALYSIS")
        print("-" * 30)
        print(f"Document Type: {classification.get('document_type', 'unknown')}")
        print(f"Classification Confidence: {classification.get('confidence', 0):.2f}")
        print(f"Manual Review Required: {classification.get('needs_manual_review', False)}")
    
    # Verification Results
    verification_sections = [
        ('identity_verification', '🆔 IDENTITY VERIFICATION'),
        ('financial_analysis', '💰 FINANCIAL ANALYSIS'),
        ('compliance_check', '📋 COMPLIANCE CHECK'),
        ('fraud_detection', '🚨 FRAUD DETECTION')
    ]
    
    for step_key, section_title in verification_sections:
        if step_key in step_results:
            result = step_results[step_key]
            print(f"\n{section_title}")
            print("-" * 30)
            
            if step_key == 'identity_verification':
                print(f"Identity Verified: {result.get('identity_verified', False)}")
                print(f"Verification Confidence: {result.get('verification_confidence', 0):.2f}")
                
            elif step_key == 'financial_analysis':
                print(f"Risk Level: {result.get('risk_level', 'unknown')}")
                print(f"Risk Score: {result.get('risk_score', 0):.2f}")
                print(f"Anomalies Detected: {len(result.get('anomalies_detected', []))}")
                
            elif step_key == 'compliance_check':
                print(f"Compliance Status: {result.get('compliance_status', 'unknown')}")
                print(f"Compliance Score: {result.get('compliance_score', 0):.2f}")
                print(f"Missing Requirements: {len(result.get('missing_requirements', []))}")
                
            elif step_key == 'fraud_detection':
                print(f"Fraud Risk Level: {result.get('fraud_risk_level', 'unknown')}")
                print(f"Risk Score: {result.get('risk_score', 0):.2f}")
                print(f"Fraud Indicators: {len(result.get('fraud_indicators', []))}")
    
    # Final Decision
    if 'verification_decision' in step_results:
        decision = step_results['verification_decision']
        print(f"\n🎯 FINAL DECISION")
        print("-" * 30)
        print(f"Decision: {decision.get('final_decision', 'unknown')}")
        print(f"Confidence: {decision.get('decision_confidence', 0):.2f}")
        print(f"Human Review Required: {decision.get('needs_human_review', False)}")
    
    # System Performance Metrics
    print(f"\n⚡ SYSTEM PERFORMANCE")
    print("-" * 30)
    
    try:
        # Event metrics
        event_metrics = await event_monitor.get_event_metrics(time_window_minutes=10)
        print(f"Total Events: {event_metrics.get('total_events', 0)}")
        print(f"Event Success Rate: {event_metrics.get('success_rate', 0):.1f}%")
        
        # Worker performance
        worker_summary = await worker_monitor.get_worker_performance_summary(time_window_minutes=10)
        print(f"Worker Commands: {worker_summary['aggregated_metrics']['total_commands']}")
        print(f"Worker Success Rate: {worker_summary['aggregated_metrics']['average_success_rate']:.1f}%")
        
        # System resources
        system_metrics = await metrics_collector.get_system_metrics(time_window_minutes=10)
        print(f"System Metrics Collected: {len(system_metrics.get('system_metrics', {}))}")
        
    except Exception as e:
        print(f"Could not retrieve performance metrics: {e}")
    
    print("\n" + "=" * 70)


async def run_batch_verification(document_paths: list[str]):
    """Run batch verification on multiple documents."""
    print(f"🔄 Starting Batch Document Verification")
    print(f"📄 Processing {len(document_paths)} documents")
    
    results = []
    for i, document_path in enumerate(document_paths, 1):
        print(f"\n📋 Processing document {i}/{len(document_paths)}: {Path(document_path).name}")
        result = await run_document_verification(document_path, "full")
        results.append({
            "document_path": document_path,
            "result": result
        })
    
    # Batch summary
    print(f"\n📊 BATCH VERIFICATION SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for r in results if r["result"].get("state") == "completed")
    failed = len(results) - successful
    
    print(f"Total Processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful/len(results)*100):.1f}%")
    
    return results


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Document Verification Workflow")
    parser.add_argument(
        "--workflow-type",
        choices=["full", "identity_only", "financial_only", "batch"],
        default="full",
        help="Type of verification workflow to run"
    )
    parser.add_argument(
        "--document-path",
        help="Path to document to verify (if not provided, uses sample documents)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all sample documents in batch mode"
    )
    parser.add_argument(
        "--create-samples",
        action="store_true",
        help="Create sample documents for testing"
    )
    
    args = parser.parse_args()
    
    print("🔐 Document Verification System")
    print("=" * 50)
    
    # Check Redis connection
    print("⚠️  Make sure Redis is running on localhost:6379")
    print("   You can start it with: redis-server")
    
    # Configure DSPy
    has_gemini = configure_dspy()
    if not has_gemini:
        print("ℹ️  Running with mock responses for demonstration")
    
    # Create sample documents if requested or if none exist
    if args.create_samples or not args.document_path:
        sample_paths = create_sample_documents()
        if not args.document_path:
            args.document_path = sample_paths[0]
    
    try:
        if args.batch:
            # Run batch verification
            sample_paths = create_sample_documents()
            asyncio.run(run_batch_verification(sample_paths))
        else:
            # Run single document verification
            if not args.document_path:
                print("❌ No document path provided. Use --document-path or --create-samples")
                sys.exit(1)
            
            asyncio.run(run_document_verification(
                args.document_path,
                args.workflow_type
            ))
            
    except KeyboardInterrupt:
        print("\n⚠️  Application interrupted by user")
    except Exception as e:
        print(f"\n❌ Application failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()