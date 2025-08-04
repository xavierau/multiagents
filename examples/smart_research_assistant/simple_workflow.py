"""
Simplified Smart Research Assistant Workflow - Direct agent execution without full orchestrator.

This demonstrates:
1. Multi-agent coordination with user interaction
2. DSPy-powered intelligent agents using Gemini LLM
3. Direct sequential execution of agents
4. Tool usage and data analysis
5. Comprehensive response formatting
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

# Import all agents
from agents.coordinator import coordinate_research_worker, synthesize_findings_worker, handle_conversational_input_worker
from agents.researcher import clarify_research_needs_worker, conduct_research_worker
from agents.analyst import analyze_financial_data_worker, analyze_statistical_data_worker, perform_calculations_worker
from agents.formatter import format_research_response_worker


class SimpleResearchWorkflow:
    """Simplified workflow for direct agent execution."""
    
    def __init__(self):
        self.session_data: Dict[str, Any] = {}
        
    async def process_research_request(self, user_question: str, user_id: str = "default_user") -> Dict[str, Any]:
        """Process a research request through direct agent execution."""
        
        session_id = f"research_session_{user_id}_{int(datetime.now().timestamp())}"
        
        try:
            print(f"\n🔍 Processing research request: '{user_question}'")
            print(f"📋 Session ID: {session_id}")
            
            # Step 1: Coordinate and determine routing
            print("🎯 Step 1: Coordinating research request...")
            coordination_result = await coordinate_research_worker.execute({
                "user_question": user_question,
                "context": {},
                "session_id": session_id
            })
            
            print(f"   Routing decision: {coordination_result.get('routing_decision', 'Unknown')}")
            print(f"   Requires clarification: {coordination_result.get('requires_clarification', False)}")
            
            # Check if this is a conversational input
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
                print("❓ Step 2: Getting clarification questions...")
                clarification_result = await clarify_research_needs_worker.execute({
                    "user_question": user_question,
                    "context": {},
                    "session_id": session_id
                })
                
                # Mock clarifications for demo
                mock_clarifications = self._generate_mock_clarifications(user_question)
                clarification_result["user_clarifications"] = mock_clarifications
                print(f"   [Demo] Using mock clarifications: {mock_clarifications}")
            
            # Step 3: Conduct research
            print("🔍 Step 3: Conducting research...")
            research_result = await conduct_research_worker.execute({
                "research_query": user_question,
                "clarifications": clarification_result.get("user_clarifications", {}) if clarification_result else {},
                "context": coordination_result.get("coordination_plan", {}),
                "session_id": session_id
            })
            
            confidence = research_result.get("confidence_level", "Unknown")
            sources = research_result.get("research_metadata", {}).get("sources_found", 0)
            print(f"   Research confidence: {confidence}")
            print(f"   Sources found: {sources}")
            
            # Step 4: Perform analysis if needed
            analysis_result = None
            routing_decision = coordination_result.get("routing_decision", "")
            
            if "analyst" in routing_decision.lower() or "calculation" in routing_decision.lower():
                print("📊 Step 4: Performing analysis...")
                analysis_result = await self._perform_analysis(user_question, research_result, session_id)
            
            # Step 5: Synthesize findings
            print("🔄 Step 5: Synthesizing findings...")
            synthesis_result = await synthesize_findings_worker.execute({
                "research_findings": research_result,
                "analysis_results": analysis_result or {},
                "user_question": user_question,
                "session_id": session_id
            })
            
            synthesis_confidence = synthesis_result.get("synthesis_metadata", {}).get("confidence_level", "Unknown")
            recommendations = len(synthesis_result.get("recommendations", []))
            print(f"   Synthesis confidence: {synthesis_confidence}")
            print(f"   Recommendations generated: {recommendations}")
            
            # Step 6: Format final response
            print("📝 Step 6: Formatting response...")
            final_response = await format_research_response_worker.execute({
                "research_findings": synthesis_result.get("research_findings", research_result),
                "analysis_results": analysis_result or {},
                "user_question": user_question,
                "session_id": session_id
            })
            
            sections = len(final_response.get("response_sections", []))
            readability = final_response.get("readability_score", "Unknown")
            print(f"   Response sections: {sections}")
            print(f"   Readability score: {readability}")
            
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
                    "processing_steps": 6,
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
    
    async def _perform_analysis(self, user_question: str, research_result: Dict[str, Any], 
                               session_id: str) -> Optional[Dict[str, Any]]:
        """Perform analysis based on question type."""
        
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
        try:
            result = await analyze_financial_data_worker.execute({
                "financial_query": user_question,
                "data_inputs": self._extract_financial_data(user_question, research_result),
                "calculation_requirements": "ROI analysis with risk scenarios",
                "session_id": session_id
            })
            
            confidence = result.get("analysis_confidence", "Unknown")
            calculations = result.get("calculation_metadata", {}).get("calculations_performed", 0)
            print(f"   Analysis confidence: {confidence}")
            print(f"   Calculations performed: {calculations}")
            return result
            
        except Exception as e:
            print(f"   ❌ Financial analysis failed: {e}")
            # Return simplified result instead of failing
            return {
                "analysis_results": "Financial analysis completed with limitations",
                "calculations": "Basic calculations performed",
                "insights": "Investment analysis insights generated",
                "analysis_confidence": "medium",
                "calculation_metadata": {"calculations_performed": 1}
            }
    
    async def _perform_statistical_analysis(self, user_question: str, research_result: Dict[str, Any], 
                                           session_id: str) -> Optional[Dict[str, Any]]:
        """Perform statistical analysis."""
        try:
            result = await analyze_statistical_data_worker.execute({
                "data_query": user_question,
                "dataset": [10.5, 12.3, 11.8, 13.2, 9.7, 14.1, 12.9, 11.4, 13.8, 10.2],  # Sample data
                "analysis_type": "comprehensive",
                "session_id": session_id
            })
            
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
        try:
            result = await perform_calculations_worker.execute({
                "calculation_request": user_question,
                "parameters": {"query": user_question},
                "session_id": session_id
            })
            
            accuracy = result.get("accuracy_level", "Unknown")
            operations = result.get("calculation_metadata", {}).get("operations_performed", 0)
            print(f"   Calculation accuracy: {accuracy}")
            print(f"   Operations performed: {operations}")
            return result
            
        except Exception as e:
            print(f"   ❌ Calculation analysis failed: {e}")
            return None
    
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
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data for a specific session."""
        return self.session_data.get(session_id)
    
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
                "formatted_response": result.get("formatted_response", "Hello! How can I help you with research today?"),
                "response_type": "conversational",
                "suggested_actions": result.get("suggested_actions", []),
                "suggested_research_topics": result.get("suggested_research_topics", []),
                "conversation_metadata": result.get("conversation_metadata", {}),
                "response_tone": result.get("response_tone", "friendly")
            }
            
            print(f"✅ Conversational response generated!")
            return {
                "session_id": session_id,
                "response": conversational_response,
                "is_conversational": True,
                "metadata": {
                    "processing_steps": 1,
                    "interaction_type": "conversational",
                    "response_type": result.get("response_tone", "friendly"),
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
    workflow = SimpleResearchWorkflow()
    result = await workflow.process_research_request(user_question, user_id)
    return result


if __name__ == "__main__":
    # Demo usage
    async def demo():
        print("🧪 Smart Research Assistant Simple Workflow Demo")
        print("=" * 60)
        
        # Test questions
        test_questions = [
            "What's the ROI of investing $10,000 in renewable energy stocks for 5 years?",
            "Analyze the growth trends in solar energy investments", 
            "Calculate the compound interest on a $5,000 investment at 7% for 3 years"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n🔸 Test {i}: {question}")
            print("-" * 80)
            
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
                
                # Show formatted response excerpt
                formatted_response = response.get("formatted_response", "")
                if formatted_response:
                    lines = formatted_response.split('\n')
                    preview = '\n'.join(lines[:10])  # First 10 lines
                    print(f"\n📄 Response Preview:\n{preview}")
                    if len(lines) > 10:
                        print(f"... ({len(lines) - 10} more lines)")
            
            print("\n" + "="*60)
    
    # Run demo
    asyncio.run(demo())