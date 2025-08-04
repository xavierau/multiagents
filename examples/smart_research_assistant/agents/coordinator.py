"""
Coordinator Agent - Orchestrates multi-agent workflow and routing decisions.

This agent analyzes user questions and coordinates the interaction between
specialized agents (Research, Analyst, Formatter) to provide comprehensive responses.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from typing import Dict, Any, List
import json
import asyncio

from multiagents.worker_sdk import dspy_worker
from config.gemini_config import get_coordinator_config


@dspy_worker(
    "coordinate_research",
    signature="user_question, context -> routing_decision, coordination_plan, requires_clarification",
    timeout=60,
    retry_attempts=2,
    model=get_coordinator_config().model
)
async def coordinate_research_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Coordinator Agent that analyzes user questions and creates coordination plans.
    
    This agent determines:
    1. Which specialized agents need to be involved
    2. The sequence of agent interactions
    3. Whether clarification is needed from the user
    4. How to synthesize the final response
    """
    user_question = context.get("user_question", "")
    existing_context = context.get("context", {})
    
    # Access the DSPy agent that was injected by the @dspy_worker decorator
    dspy_agent = context.get("_dspy_agent")
    
    if dspy_agent:
        try:
            # First, let LLM determine the intent and interaction type
            intent_signature = dspy_agent.create_signature(
                "user_input, context",
                "interaction_type, response_strategy, user_intent, requires_research"
            )
            
            intent_result = dspy_agent.predict(
                intent_signature,
                user_input=user_question,
                context=str(existing_context)
            )
            
            interaction_type = intent_result.get("interaction_type", "research")
            response_strategy = intent_result.get("response_strategy", "full_research")
            user_intent = intent_result.get("user_intent", "unknown")
            requires_research = intent_result.get("requires_research", "true").lower() in ["true", "yes", "1"]
            
            # If it's conversational, handle it directly
            if interaction_type.lower() in ["conversational", "greeting", "social", "casual"]:
                print(f"🤖 LLM detected conversational input: {interaction_type}")
                return {
                    "routing_decision": json.dumps({
                        "interaction_type": "conversational",
                        "response_strategy": "conversational_response",
                        "needs_research": False,
                        "needs_calculation": False,
                        "needs_clarification": False
                    }),
                    "coordination_plan": json.dumps({
                        "agents_required": ["conversational_agent"],
                        "estimated_steps": 1,
                        "complexity": "conversational"
                    }),
                    "requires_clarification": False,
                    "question_analysis": {
                        "original_question": user_question,
                        "detected_intent": interaction_type,
                        "user_intent": user_intent,
                        "processing_mode": "llm_conversational"
                    }
                }
            
            # For research requests, get detailed routing
            routing_signature = dspy_agent.create_signature(
                "research_question, context, user_intent", 
                "needs_research, needs_calculation, needs_clarification, complexity_level, agent_sequence, reasoning"
            )
            
            routing_result = dspy_agent.predict(
                routing_signature,
                research_question=user_question,
                context=str(existing_context),
                user_intent=user_intent
            )
            
            # Use LLM results
            needs_research = routing_result.get("needs_research", "true").lower() in ["true", "yes", "1"]
            needs_calculation = routing_result.get("needs_calculation", "false").lower() in ["true", "yes", "1"]
            needs_clarification = routing_result.get("needs_clarification", "false").lower() in ["true", "yes", "1"]
            complexity_level = routing_result.get("complexity_level", "medium")
            agent_sequence = routing_result.get("agent_sequence", "research,analyst,formatter")
            reasoning = routing_result.get("reasoning", "")
            
            print(f"🤖 LLM routing reasoning: {reasoning}")
            
        except Exception as e:
            print(f"DSPy prediction failed, using fallback logic: {e}")
            # Fallback to rule-based logic if DSPy fails
            needs_research, needs_calculation, needs_clarification, complexity_level, agent_sequence = _fallback_routing_logic(user_question)
    else:
        # Fallback if no DSPy agent available
        needs_research, needs_calculation, needs_clarification, complexity_level, agent_sequence = _fallback_routing_logic(user_question)
    
    # Create detailed coordination plan
    agents_needed = []
    if needs_research:
        agents_needed.append("research_agent")
    if needs_calculation:
        agents_needed.append("analyst_agent")
    agents_needed.append("formatter_agent")  # Always format the final response
    
    # Execution sequence
    execution_plan = {
        "agents_required": agents_needed,
        "parallel_execution": needs_research and needs_calculation,
        "requires_user_clarification": needs_clarification,
        "estimated_steps": len(agents_needed) + (1 if needs_clarification else 0),
        "complexity": complexity_level,
        "agent_sequence": agent_sequence.split(",") if agent_sequence else agents_needed
    }
    
    return {
        "routing_decision": json.dumps({
            "needs_research": needs_research,
            "needs_calculation": needs_calculation,
            "needs_clarification": needs_clarification,
            "complexity": complexity_level
        }),
        "coordination_plan": json.dumps(execution_plan),
        "requires_clarification": needs_clarification,
        "question_analysis": {
            "original_question": user_question,
            "detected_intent": _analyze_question_intent(user_question),
            "key_topics": _extract_key_topics(user_question),
            "processing_mode": "llm_enhanced" if dspy_agent else "rule_based"
        }
    }


@dspy_worker(
    "synthesize_findings",
    signature="research_findings, analysis_results, user_question -> synthesized_insights, recommendations, confidence_assessment",
    timeout=90,
    retry_attempts=2,
    model=get_coordinator_config().model
)
async def synthesize_findings_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesis Agent that combines research and analysis results into coherent insights.
    
    This agent creates a unified response by:
    1. Analyzing research findings for key themes
    2. Integrating analysis results and calculations
    3. Generating actionable recommendations
    4. Assessing overall confidence in findings
    """
    research_findings = context.get("research_findings", {})
    analysis_results = context.get("analysis_results", {})
    user_question = context.get("user_question", "")
    
    # Access the DSPy agent
    dspy_agent = context.get("_dspy_agent")
    
    if dspy_agent:
        try:
            # Create synthesis signature
            synthesis_signature = dspy_agent.create_signature(
                "research_data, analysis_data, original_question",
                "key_insights, synthesis_summary, recommendations, confidence_level"
            )
            
            # Prepare data for LLM
            research_str = _format_research_for_llm(research_findings) 
            analysis_str = _format_analysis_for_llm(analysis_results)
            
            # Get LLM synthesis
            synthesis_result = dspy_agent.predict(
                synthesis_signature,
                research_data=research_str,
                analysis_data=analysis_str,
                original_question=user_question
            )
            
            # Extract LLM results
            synthesized_insights = synthesis_result.get("synthesis_summary", "")
            key_insights = synthesis_result.get("key_insights", "").split(";") if synthesis_result.get("key_insights") else []
            recommendations = synthesis_result.get("recommendations", "").split(";") if synthesis_result.get("recommendations") else []
            confidence_level = synthesis_result.get("confidence_level", "medium")
            
        except Exception as e:
            print(f"DSPy synthesis failed, using fallback: {e}")
            # Fallback synthesis
            synthesized_insights, key_insights, recommendations, confidence_level = _fallback_synthesis(
                research_findings, analysis_results, user_question
            )
    else:
        # Fallback synthesis
        synthesized_insights, key_insights, recommendations, confidence_level = _fallback_synthesis(
            research_findings, analysis_results, user_question
        )
    
    return {
        "synthesized_insights": synthesized_insights,
        "research_findings": research_findings,  # Pass through for formatter
        "analysis_results": analysis_results,    # Pass through for formatter
        "key_insights": key_insights,
        "recommendations": recommendations,
        "synthesis_metadata": {
            "confidence_level": confidence_level,
            "synthesis_method": "llm_enhanced" if dspy_agent else "rule_based",
            "data_sources_integrated": len([x for x in [research_findings, analysis_results] if x]),
            "insights_generated": len(key_insights),
            "recommendations_count": len(recommendations)
        }
    }


def _fallback_routing_logic(user_question: str) -> tuple:
    """Fallback routing logic when DSPy is not available."""
    question_lower = user_question.lower().strip()
    
    # Check for greetings and simple conversational inputs
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    simple_responses = ['thanks', 'thank you', 'ok', 'okay', 'yes', 'no', 'bye', 'goodbye']
    
    if question_lower in greetings or any(greeting in question_lower for greeting in greetings):
        return False, False, False, "conversational", "conversational_response"
    
    if question_lower in simple_responses or any(response in question_lower for response in simple_responses):
        return False, False, False, "conversational", "conversational_response"
    
    # Check for very short/unclear inputs
    if len(question_lower) < 4 or question_lower in ['a', 'an', 'the', 'is', 'are', 'what', 'how']:
        return False, False, False, "conversational", "conversational_response"
    
    # Check if it's actually a research question
    research_indicators = [
        "what", "how", "why", "when", "where", "which", "who",
        "market", "stock", "trend", "data", "information", "recent", "current", 
        "news", "analysis", "research", "study", "report", "tell me", "explain",
        "analyze", "compare", "evaluate", "investigate", "find out"
    ]
    
    calculation_indicators = [
        "calculate", "roi", "return", "investment", "percent", "growth", 
        "statistics", "compare", "average", "total", "$", "compound", "interest",
        "math", "compute", "percentage", "profit", "loss"
    ]
    
    # Only mark as needing research if it contains research indicators AND is longer than a greeting
    needs_research = (
        len(question_lower) > 10 and  # Must be substantial
        any(indicator in question_lower for indicator in research_indicators)
    )
    
    needs_calculation = any(indicator in question_lower for indicator in calculation_indicators)
    
    needs_clarification = (
        needs_research and
        any(keyword in question_lower for keyword in [
            "best", "good", "recommend", "should", "which", "how much", "when"
        ]) and not any(keyword in question_lower for keyword in [
            "specific", "exactly", "precisely", "$", "year", "month"
        ])
    )
    
    # If neither research nor calculation is needed, treat as conversational
    if not needs_research and not needs_calculation:
        return False, False, False, "conversational", "conversational_response"
    
    # Determine complexity
    if needs_research and needs_calculation:
        complexity_level = "high"
    elif needs_research or needs_calculation:
        complexity_level = "medium"
    else:
        complexity_level = "low"
    
    # Agent sequence
    if needs_research and needs_calculation:
        agent_sequence = "research,analyst,formatter"
    elif needs_calculation:
        agent_sequence = "analyst,formatter"
    elif needs_research:
        agent_sequence = "research,formatter"
    else:
        agent_sequence = "formatter"
    
    return needs_research, needs_calculation, needs_clarification, complexity_level, agent_sequence


def _analyze_question_intent(question: str) -> str:
    """Analyze the intent behind the user's question."""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ["roi", "return", "investment", "profit"]):
        return "financial_analysis"
    elif any(word in question_lower for word in ["calculate", "compute", "math"]):
        return "calculation"
    elif any(word in question_lower for word in ["trend", "market", "analysis"]):
        return "market_research"
    elif any(word in question_lower for word in ["compare", "versus", "vs"]):
        return "comparative_analysis"
    else:
        return "general_inquiry"


def _extract_key_topics(question: str) -> List[str]:
    """Extract key topics from the question."""
    topics = []
    question_lower = question.lower()
    
    # Financial topics
    if any(word in question_lower for word in ["renewable", "solar", "wind"]):
        topics.append("renewable_energy")
    if any(word in question_lower for word in ["stock", "investment", "equity"]):
        topics.append("stocks")
    if any(word in question_lower for word in ["roi", "return"]):
        topics.append("returns")
    if any(word in question_lower for word in ["risk", "volatility"]):
        topics.append("risk_analysis")
    if any(word in question_lower for word in ["esg", "sustainable"]):
        topics.append("sustainability")
    
    return topics[:5]  # Limit to top 5 topics


def _format_research_for_llm(research_findings: Dict[str, Any]) -> str:
    """Format research findings for LLM consumption."""
    if not research_findings:
        return "No research data available"
    
    summary = research_findings.get("summary", "")
    key_insights = research_findings.get("key_insights", [])
    confidence = research_findings.get("confidence_level", "unknown")
    
    formatted = f"Research Summary: {summary}\n"
    if key_insights:
        formatted += f"Key Insights: {'; '.join(key_insights[:5])}\n"
    formatted += f"Research Confidence: {confidence}"
    
    return formatted


def _format_analysis_for_llm(analysis_results: Dict[str, Any]) -> str:
    """Format analysis results for LLM consumption."""
    if not analysis_results:
        return "No analysis data available"
    
    # Handle different analysis types
    if "roi_analysis" in str(analysis_results):
        return f"Financial Analysis: ROI calculations completed. Analysis confidence: {analysis_results.get('analysis_confidence', 'medium')}"
    elif "statistical_results" in str(analysis_results):
        return f"Statistical Analysis: Data analysis completed. Quality score: {analysis_results.get('data_quality_score', 'unknown')}"
    else:
        return f"Analysis completed with {analysis_results.get('calculation_metadata', {}).get('operations_performed', 0)} operations"


def _fallback_synthesis(research_findings: Dict[str, Any], analysis_results: Dict[str, Any], user_question: str) -> tuple:
    """Fallback synthesis when DSPy is not available."""
    insights = []
    recommendations = []
    
    # Extract insights from research
    if research_findings:
        research_insights = research_findings.get("key_insights", [])
        insights.extend(research_insights[:3])
    
    # Extract insights from analysis
    if analysis_results:
        if "calculations" in str(analysis_results):
            insights.append("Financial calculations provide quantitative insights")
        if "analysis_confidence" in analysis_results:
            confidence = analysis_results.get("analysis_confidence", "medium")
            insights.append(f"Analysis completed with {confidence} confidence")
    
    # Generate recommendations based on question type
    question_lower = user_question.lower()
    if "investment" in question_lower:
        recommendations.extend([
            "Consider diversification to manage risk",
            "Monitor market conditions regularly",
            "Consult with financial advisor for personalized advice"
        ])
    else:
        recommendations.extend([
            "Continue monitoring developments in this area",
            "Consider multiple data sources for comprehensive view"
        ])
    
    synthesized_summary = f"Analysis of '{user_question}' shows mixed indicators requiring careful consideration of multiple factors."
    confidence_level = "medium"
    
    return synthesized_summary, insights, recommendations, confidence_level


@dspy_worker(
    "handle_conversational_input",
    signature="user_input, context -> response, response_type, suggested_actions, follow_up_questions",
    timeout=30,
    retry_attempts=2,
    model=get_coordinator_config().model
)
async def handle_conversational_input_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM-driven conversational response handler.
    
    This agent provides intelligent conversational responses for:
    1. Greetings and pleasantries
    2. Simple acknowledgments 
    3. Help requests and guidance
    4. Unclear or ambiguous inputs
    """
    user_input = context.get("user_question", "").strip()
    existing_context = context.get("context", {})
    
    # Access DSPy agent for intelligent conversational responses
    dspy_agent = context.get("_dspy_agent")
    
    if dspy_agent:
        try:
            # Use LLM to generate contextual conversational response
            conversation_signature = dspy_agent.create_signature(
                "user_message, conversation_context",
                "friendly_response, response_tone, suggested_research_topics, next_actions, engagement_level"
            )
            
            conversation_result = dspy_agent.predict(
                conversation_signature,
                user_message=user_input,
                conversation_context=str(existing_context)
            )
            
            response = conversation_result.get("friendly_response", "")
            response_tone = conversation_result.get("response_tone", "friendly")
            suggested_topics = conversation_result.get("suggested_research_topics", "")
            next_actions = conversation_result.get("next_actions", "")
            engagement_level = conversation_result.get("engagement_level", "standard")
            
            # Format the response for better presentation
            if not response:
                response = _generate_default_greeting()
            
            # Add helpful context if needed
            if "help" in user_input.lower() or len(user_input) < 4:
                response += "\n\n" + _get_capability_summary()
            
        except Exception as e:
            print(f"LLM conversational response failed, using fallback: {e}")
            response, response_tone, suggested_topics, next_actions = _fallback_conversational_response(user_input)
            engagement_level = "fallback"
    else:
        response, response_tone, suggested_topics, next_actions = _fallback_conversational_response(user_input)
        engagement_level = "rule_based"
    
    # Generate suggested actions
    suggested_actions = next_actions.split(",") if next_actions else _generate_default_suggestions()
    suggested_research_topics = suggested_topics.split(",") if suggested_topics else []
    
    return {
        "formatted_response": response,
        "response_type": "conversational",
        "response_tone": response_tone,
        "suggested_actions": suggested_actions[:4],  # Limit to 4 actions
        "suggested_research_topics": suggested_research_topics[:3],  # Limit to 3 topics
        "conversation_metadata": {
            "response_method": "llm_enhanced" if dspy_agent else "rule_based",
            "engagement_level": engagement_level,
            "user_input_length": len(user_input),
            "interaction_type": "conversational"
        }
    }


def _generate_default_greeting() -> str:
    """Generate a default greeting response."""
    return (
        "Hello! 👋 I'm your Smart Research Assistant. I'm here to help you with:\n\n"
        "🔍 **Research & Analysis**\n"
        "• Market trends and insights\n"
        "• Investment opportunities and ROI analysis\n"
        "• Technology developments\n"
        "• Industry and competitive analysis\n\n"
        "📊 **Calculations & Data Analysis**\n"
        "• Financial calculations and modeling\n"
        "• Statistical analysis\n"
        "• Comparative assessments\n\n"
        "What would you like to explore today?"
    )


def _get_capability_summary() -> str:
    """Get a summary of assistant capabilities."""
    return (
        "💡 **How to use me:**\n"
        "• Ask specific research questions\n"
        "• Request financial calculations\n"
        "• Get market analysis and trends\n"
        "• Explore investment opportunities\n\n"
        "**Example questions:**\n"
        "• \"What's the ROI of renewable energy stocks?\"\n"
        "• \"Analyze the latest AI investment trends\"\n"
        "• \"Calculate compound interest on $5,000 at 7%\""
    )


def _generate_default_suggestions() -> List[str]:
    """Generate default action suggestions."""
    return [
        "Ask about investment opportunities",
        "Research market trends", 
        "Get help with calculations",
        "Explore technology insights"
    ]