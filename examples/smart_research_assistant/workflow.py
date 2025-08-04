"""
Smart Research Assistant Workflow - Orchestrates multiple DSPy agents for intelligent research.

This workflow demonstrates:
1. Multi-agent coordination with user interaction
2. DSPy-powered intelligent agents using Gemini LLM
3. Dynamic routing between specialized agents
4. Interactive clarification loops
5. Tool usage and data analysis
6. Comprehensive response formatting
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from typing import Dict, Any, List, Optional, Tuple
import asyncio
import json
from datetime import datetime

from multiagents.orchestrator import Orchestrator, WorkflowBuilder, WorkflowDefinition
from multiagents.event_bus import RedisEventBus
from multiagents.event_bus.redis_bus import RedisStateStore
from multiagents.worker_sdk.worker_manager import WorkerManager

# Import all agents
from agents.coordinator import coordinate_research_worker, synthesize_findings_worker, handle_conversational_input_worker
from agents.researcher import clarify_research_needs_worker, conduct_research_worker
from agents.analyst import analyze_financial_data_worker, analyze_statistical_data_worker, perform_calculations_worker
from agents.formatter import format_research_response_worker, format_financial_analysis_worker
from agents.conversational import conversational_response_worker

# Import configuration
from config.gemini_config import get_coordinator_config


class SmartResearchWorkflow:
    """Main orchestrator for the Smart Research Assistant workflow."""
    
    def __init__(self):
        self.orchestrator: Optional[Orchestrator] = None
        self.worker_manager: Optional[WorkerManager] = None
        self.event_bus: Optional[RedisEventBus] = None
        self.session_data: Dict[str, Any] = {}
        
    async def initialize(self) -> bool:
        """Initialize the workflow components."""
        try:
            print("🚀 Initializing Smart Research Assistant Workflow...")
            
            # Setup monitoring  
            from multiagents.monitoring.config import MonitoringConfig
            monitoring_config = MonitoringConfig()
            logger = monitoring_config.create_logger()
            
            # Initialize event bus
            self.event_bus = RedisEventBus(logger=logger)
            
            # Initialize worker manager and register workers
            self.worker_manager = WorkerManager(self.event_bus, logger=logger)
            await self._register_workers()
            
            # Initialize state store and orchestrator
            state_store = RedisStateStore()
            
            # Create a simple workflow definition
            workflow = WorkflowDefinition("smart_research_workflow")
            
            self.orchestrator = Orchestrator(
                workflow=workflow,
                event_bus=self.event_bus,
                state_store=state_store,
                logger=logger
            )
            
            print("✅ Smart Research Assistant Workflow initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize workflow: {e}")
            return False
    
    async def _register_workers(self):
        """Register all worker agents with the manager."""
        workers = [
            # Coordinator agents
            coordinate_research_worker,
            synthesize_findings_worker,
            
            # Research agents
            clarify_research_needs_worker,
            conduct_research_worker,
            
            # Analyst agents
            analyze_financial_data_worker,
            analyze_statistical_data_worker,
            perform_calculations_worker,
            
            # Formatter agents
            format_research_response_worker,
            format_financial_analysis_worker,
            
            # Conversational agents
            conversational_response_worker,
            handle_conversational_input_worker,
        ]
        
        for worker in workers:
            await self.worker_manager.register_worker(worker)
        
        print(f"📋 Registered {len(workers)} worker agents")
    
    async def process_research_request(self, user_question: str, user_id: str = "default_user") -> Dict[str, Any]:
        """Process a research request through the complete workflow."""
        
        session_id = f"research_session_{user_id}_{int(datetime.now().timestamp())}"
        
        try:
            print(f"\n🔍 Processing research request: '{user_question}'")
            print(f"📋 Session ID: {session_id}")
            
            # Step 1: Coordinate and determine routing
            coordination_result = await self._coordinate_request(user_question, session_id)
            
            if not coordination_result:
                return {"error": "Failed to coordinate research request"}
            
            # Check if this is a conversational input rather than a research request
            routing_decision = coordination_result.get("routing_decision", "")
            coordination_plan = coordination_result.get("coordination_plan", "")
            question_analysis = coordination_result.get("question_analysis", {})
            
            # Handle both string and dict formats for conversational detection
            routing_str = str(routing_decision)
            plan_str = str(coordination_plan)
            detected_intent = question_analysis.get("detected_intent", "")
            
            # Check multiple indicators for conversational intent
            is_conversational = (
                "conversational" in routing_str.lower() or
                "conversational" in plan_str.lower() or
                detected_intent in ["conversational", "greeting", "social", "casual"] or
                "conversational_response" in plan_str
            )
            
            if is_conversational:
                print("💬 Detected conversational input - providing conversational response")
                return await self._handle_conversational_input(user_question, session_id)
            
            # Step 2: Handle clarification if needed
            clarification_result = None
            if coordination_result.get("requires_clarification", False):
                clarification_result = await self._handle_clarification(user_question, session_id)
                if not clarification_result:
                    return {"error": "Failed to get research clarifications"}
            
            # Step 3: Conduct research based on routing decision
            research_result = await self._conduct_research(
                user_question, 
                coordination_result, 
                clarification_result, 
                session_id
            )
            
            if not research_result:
                return {"error": "Failed to conduct research"}
            
            # Step 4: Perform analysis if needed
            analysis_result = None
            routing_decision_str = str(routing_decision).lower()
            
            if "analyst" in routing_decision_str or "calculation" in routing_decision_str:
                analysis_result = await self._perform_analysis(
                    user_question, 
                    research_result, 
                    session_id
                )
            
            # Step 5: Synthesize findings
            synthesis_result = await self._synthesize_findings(
                user_question,
                research_result,
                analysis_result,
                session_id
            )
            
            # Step 6: Format final response
            final_response = await self._format_response(
                user_question,
                synthesis_result.get("research_findings", research_result),
                analysis_result,
                session_id
            )
            
            # Store session data
            self.session_data[session_id] = {
                "user_question": user_question,
                "coordination": coordination_result,
                "clarification": clarification_result,
                "research": research_result,
                "analysis": analysis_result,
                "synthesis": synthesis_result,
                "final_response": final_response,
                "completed_at": datetime.now().isoformat()
            }
            
            print(f"✅ Research request completed successfully!")
            return {
                "session_id": session_id,
                "response": final_response,
                "metadata": {
                    "processing_steps": len([x for x in [coordination_result, research_result, analysis_result, synthesis_result, final_response] if x]),
                    "had_clarification": clarification_result is not None,
                    "had_analysis": analysis_result is not None,
                    "completed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Error processing research request: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Workflow processing failed: {str(e)}"}
    
    async def _handle_conversational_input(self, user_question: str, session_id: str) -> Dict[str, Any]:
        """Handle conversational inputs like greetings, thanks, etc."""
        print("💬 Processing conversational input...")
        
        context = {
            "user_question": user_question,
            "context": {},
            "session_id": session_id
        }
        
        try:
            result = await handle_conversational_input_worker.execute(context)
            
            # Format as a simple response
            conversational_response = {
                "formatted_response": result.get("response", "Hello! How can I help you with research today?"),
                "response_type": "conversational",
                "suggested_actions": result.get("suggested_actions", []),
                "suggested_research_topics": result.get("suggested_research_topics", []),
                "conversation_metadata": result.get("conversation_metadata", {})
            }
            
            print(f"✅ Conversational response generated!")
            return {
                "session_id": session_id,
                "response": conversational_response,
                "is_conversational": True,
                "metadata": {
                    "processing_steps": 1,
                    "interaction_type": "conversational",
                    "response_type": result.get("response_type", "greeting"),
                    "completed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Conversational processing failed: {e}")
            # Fallback conversational response
            fallback_response = {
                "formatted_response": (
                    "Hello! 👋 I'm your Smart Research Assistant.\n\n"
                    "I can help you with research, analysis, and insights on topics like:\n"
                    "• Market trends and investments\n"
                    "• Technology developments\n"
                    "• Financial calculations\n"
                    "• Data analysis\n\n"
                    "What would you like to explore today?"
                ),
                "response_type": "conversational",
                "suggested_actions": [
                    "Ask about market trends",
                    "Request investment analysis", 
                    "Get help with calculations",
                    "Explore technology insights"
                ]
            }
            
            return {
                "session_id": session_id,
                "response": fallback_response,
                "is_conversational": True,
                "metadata": {
                    "processing_steps": 1,
                    "interaction_type": "conversational",
                    "response_type": "fallback_greeting",
                    "completed_at": datetime.now().isoformat()
                }
            }
    
    async def _coordinate_request(self, user_question: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Step 1: Coordinate and route the request."""
        print("🎯 Step 1: Coordinating research request...")
        
        context = {
            "user_question": user_question,
            "context": {},
            "session_id": session_id
        }
        
        try:
            result = await coordinate_research_worker.execute(context)
            print(f"   Routing decision: {result.get('routing_decision', 'Unknown')}")
            print(f"   Requires clarification: {result.get('requires_clarification', False)}")
            return result
        except Exception as e:
            print(f"   ❌ Coordination failed: {e}")
            return None
    
    async def _handle_clarification(self, user_question: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Step 2: Handle clarification if needed."""
        print("❓ Step 2: Getting clarification questions...")
        
        context = {
            "user_question": user_question,
            "context": {},
            "session_id": session_id
        }
        
        try:
            result = await clarify_research_needs_worker.execute(context)
            clarification_questions = result.get("clarification_questions", "")
            
            if clarification_questions:
                print(f"   Questions to clarify:")
                if isinstance(clarification_questions, str):
                    questions = [q.strip() for q in clarification_questions.split('\n') if q.strip()]
                else:
                    questions = clarification_questions
                
                for i, question in enumerate(questions[:3], 1):  # Limit to 3 questions
                    print(f"   {i}. {question}")
                
                # For demo purposes, provide some default answers
                # In real implementation, this would be interactive
                mock_clarifications = self._generate_mock_clarifications(user_question)
                result["user_clarifications"] = mock_clarifications
                print(f"   [Demo] Using mock clarifications: {mock_clarifications}")
            
            return result
        except Exception as e:
            print(f"   ❌ Clarification failed: {e}")
            return None
    
    async def _conduct_research(self, user_question: str, coordination_result: Dict[str, Any], 
                              clarification_result: Optional[Dict[str, Any]], session_id: str) -> Optional[Dict[str, Any]]:
        """Step 3: Conduct research based on coordination results."""
        print("🔍 Step 3: Conducting research...")
        
        context = {
            "research_query": user_question,
            "clarifications": clarification_result.get("user_clarifications", {}) if clarification_result else {},
            "context": coordination_result.get("coordination_plan", {}),
            "session_id": session_id
        }
        
        try:
            result = await conduct_research_worker.execute(context)
            confidence = result.get("confidence_level", "Unknown")
            sources = result.get("research_metadata", {}).get("sources_found", 0)
            print(f"   Research confidence: {confidence}")
            print(f"   Sources found: {sources}")
            return result
        except Exception as e:
            print(f"   ❌ Research failed: {e}")
            return None
    
    async def _perform_analysis(self, user_question: str, research_result: Dict[str, Any], 
                               session_id: str) -> Optional[Dict[str, Any]]:
        """Step 4: Perform analysis if needed."""
        print("📊 Step 4: Performing analysis...")
        
        # Determine analysis type based on question
        if any(keyword in user_question.lower() for keyword in ["roi", "return", "investment", "profit", "financial"]):
            return await self._perform_financial_analysis(user_question, research_result, session_id)
        elif any(keyword in user_question.lower() for keyword in ["data", "statistics", "trend", "analysis"]):
            return await self._perform_statistical_analysis(user_question, research_result, session_id)
        else:
            return await self._perform_calculation_analysis(user_question, research_result, session_id)
    
    async def _perform_financial_analysis(self, user_question: str, research_result: Dict[str, Any], 
                                         session_id: str) -> Optional[Dict[str, Any]]:
        """Perform financial analysis."""
        context = {
            "financial_query": user_question,
            "data_inputs": self._extract_financial_data(user_question, research_result),
            "calculation_requirements": "ROI analysis with risk scenarios",
            "session_id": session_id
        }
        
        try:
            result = await analyze_financial_data_worker.execute(context)
            confidence = result.get("analysis_confidence", "Unknown")
            calculations = result.get("calculation_metadata", {}).get("calculations_performed", 0)
            print(f"   Analysis confidence: {confidence}")
            print(f"   Calculations performed: {calculations}")
            return result
        except Exception as e:
            print(f"   ❌ Financial analysis failed: {e}")
            # Return a simplified result instead of failing completely
            return {
                "analysis_results": "{}",
                "calculations": "{}",
                "insights": "[]",
                "analysis_confidence": "low",
                "calculation_metadata": {"calculations_performed": 0}
            }
    
    async def _perform_statistical_analysis(self, user_question: str, research_result: Dict[str, Any], 
                                           session_id: str) -> Optional[Dict[str, Any]]:
        """Perform statistical analysis."""
        context = {
            "data_query": user_question,
            "dataset": self._extract_dataset(research_result),
            "analysis_type": "comprehensive",
            "session_id": session_id
        }
        
        try:
            result = await analyze_statistical_data_worker.execute(context)
            outliers = result.get("analysis_metadata", {}).get("outliers_detected", 0)
            quality = result.get("data_quality_score", "Unknown")
            print(f"   Data quality: {quality}")
            print(f"   Outliers detected: {outliers}")
            return result
        except Exception as e:
            print(f"   ❌ Statistical analysis failed: {e}")
            return None
    
    async def _perform_calculation_analysis(self, user_question: str, research_result: Dict[str, Any], 
                                           session_id: str) -> Optional[Dict[str, Any]]:
        """Perform general calculations."""
        context = {
            "calculation_request": user_question,
            "parameters": self._extract_calculation_parameters(user_question, research_result),
            "session_id": session_id
        }
        
        try:
            result = await perform_calculations_worker.execute(context)
            accuracy = result.get("accuracy_level", "Unknown")
            operations = result.get("calculation_metadata", {}).get("operations_performed", 0)
            print(f"   Calculation accuracy: {accuracy}")
            print(f"   Operations performed: {operations}")
            return result
        except Exception as e:
            print(f"   ❌ Calculation analysis failed: {e}")
            return None
    
    async def _synthesize_findings(self, user_question: str, research_result: Dict[str, Any], 
                                  analysis_result: Optional[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
        """Step 5: Synthesize research and analysis findings."""
        print("🔄 Step 5: Synthesizing findings...")
        
        context = {
            "research_findings": research_result,
            "analysis_results": analysis_result or {},
            "user_question": user_question,
            "session_id": session_id
        }
        
        try:
            result = await synthesize_findings_worker.execute(context)
            confidence = result.get("synthesis_metadata", {}).get("confidence_level", "Unknown")
            recommendations = len(result.get("recommendations", []))
            print(f"   Synthesis confidence: {confidence}")
            print(f"   Recommendations generated: {recommendations}")
            return result
        except Exception as e:
            print(f"   ❌ Synthesis failed: {e}")
            # Return research findings as fallback
            return {"research_findings": research_result, "analysis_results": analysis_result or {}}
    
    async def _format_response(self, user_question: str, research_findings: Dict[str, Any], 
                              analysis_results: Optional[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
        """Step 6: Format the final response."""
        print("📝 Step 6: Formatting response...")
        
        context = {
            "research_findings": research_findings,
            "analysis_results": analysis_results or {},
            "user_question": user_question,
            "session_id": session_id
        }
        
        try:
            result = await format_research_response_worker.execute(context)
            sections = len(result.get("response_sections", []))
            readability = result.get("readability_score", "Unknown")
            print(f"   Response sections: {sections}")
            print(f"   Readability score: {readability}")
            return result
        except Exception as e:
            print(f"   ❌ Response formatting failed: {e}")
            # Return basic formatted response
            return {
                "formatted_response": f"Research completed for: {user_question}\n\nFindings: {research_findings.get('summary', 'Research completed')}",
                "executive_summary": f"Analysis completed for user question about {user_question}",
                "response_sections": ["Introduction", "Findings", "Conclusion"],
                "readability_score": "medium"
            }
    
    def _generate_mock_clarifications(self, user_question: str) -> Dict[str, str]:
        """Generate mock clarifications for demo purposes."""
        question_lower = user_question.lower()
        
        if "investment" in question_lower or "roi" in question_lower:
            return {
                "timeframe": "5 years",
                "investment_amount": "$10,000-$25,000",
                "risk_tolerance": "moderate",
                "investment_goals": "long-term growth"
            }
        elif "renewable energy" in question_lower:
            return {
                "energy_type": "solar and wind",
                "geographic_focus": "US market",
                "investment_timeframe": "5-10 years"
            }
        else:
            return {
                "scope": "comprehensive analysis",
                "timeframe": "current data",
                "detail_level": "detailed"
            }
    
    def _extract_financial_data(self, user_question: str, research_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data from question and research."""
        # Parse question for financial parameters
        import re
        
        data = {}
        
        # Extract investment amount
        amount_matches = re.findall(r'[\$€£]?([\d,]+(?:\.\d{2})?)', user_question)
        if amount_matches:
            try:
                amount_str = amount_matches[0].replace(',', '')
                data["investment_amount"] = float(amount_str)
            except ValueError:
                pass
        
        # Extract timeframe
        year_matches = re.findall(r'(\d+)\s*year', user_question.lower())
        if year_matches:
            try:
                data["timeframe_years"] = int(year_matches[0])
            except ValueError:
                pass
        
        # Extract return percentage
        return_matches = re.findall(r'(\d+(?:\.\d+)?)%', user_question)
        if return_matches:
            try:
                data["expected_return"] = float(return_matches[0])
            except ValueError:
                pass
        
        return data
    
    def _extract_dataset(self, research_result: Dict[str, Any]) -> List[float]:
        """Extract numerical dataset from research results."""
        # Generate sample data for demonstration
        return [10.5, 12.3, 11.8, 13.2, 9.7, 14.1, 12.9, 11.4, 13.8, 10.2]
    
    def _extract_calculation_parameters(self, user_question: str, research_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract calculation parameters."""
        return {
            "query": user_question,
            "research_context": research_result.get("summary", "")
        }
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data for a specific session."""
        return self.session_data.get(session_id)
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.worker_manager:
            await self.worker_manager.shutdown()
        if self.event_bus:
            await self.event_bus.disconnect()
        print("🧹 Workflow cleanup completed")


# Convenience function for easy workflow execution
async def run_research_query(user_question: str, user_id: str = "demo_user") -> Dict[str, Any]:
    """
    Convenience function to run a single research query.
    
    Args:
        user_question: The research question to process
        user_id: User identifier for session tracking
        
    Returns:
        Dict containing the research results
    """
    workflow = SmartResearchWorkflow()
    
    if not await workflow.initialize():
        return {"error": "Failed to initialize workflow"}
    
    try:
        result = await workflow.process_research_request(user_question, user_id)
        return result
    finally:
        await workflow.cleanup()


if __name__ == "__main__":
    # Demo usage
    async def demo():
        print("🧪 Smart Research Assistant Workflow Demo")
        print("=" * 50)
        
        # Test questions
        test_questions = [
            "What's the ROI of investing $10,000 in renewable energy stocks for 5 years?",
            "Analyze the growth trends in solar energy investments",
            "Calculate the compound interest on a $5,000 investment at 7% for 3 years"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n🔸 Test {i}: {question}")
            print("-" * 70)
            
            result = await run_research_query(question, f"test_user_{i}")
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Session: {result['session_id']}")
                response = result.get("response", {})
                if "executive_summary" in response:
                    print(f"📋 Summary: {response['executive_summary']}")
                
                metadata = result.get("metadata", {})
                print(f"📊 Steps: {metadata.get('processing_steps', 0)}")
                print(f"❓ Had clarification: {metadata.get('had_clarification', False)}")
                print(f"📈 Had analysis: {metadata.get('had_analysis', False)}")
    
    # Run demo
    asyncio.run(demo())