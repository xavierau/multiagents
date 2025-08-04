"""
Formatter Agent - Creates well-structured responses for user consumption.

This agent specializes in:
1. Formatting complex data into readable responses
2. Creating structured presentations of findings
3. Generating executive summaries
4. Ensuring clarity and user-friendliness
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime

from multiagents.worker_sdk import dspy_worker
from config.gemini_config import get_formatter_config


@dspy_worker(
    "format_research_response",
    signature="research_findings, analysis_results, user_question -> formatted_response, executive_summary",
    timeout=45,
    retry_attempts=2,
    model=get_formatter_config().model
)
async def format_research_response_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formatter Agent for research and analysis responses.
    
    This agent creates comprehensive, well-structured responses that combine
    research findings and analysis results into a coherent, user-friendly format.
    """
    research_findings = context.get("research_findings", {})
    analysis_results = context.get("analysis_results", {})
    user_question = context.get("user_question", "")
    
    # Parse JSON strings if needed
    if isinstance(research_findings, str):
        try:
            research_findings = json.loads(research_findings)
        except (json.JSONDecodeError, TypeError):
            research_findings = {}
    
    if isinstance(analysis_results, str):
        try:
            analysis_results = json.loads(analysis_results)
        except (json.JSONDecodeError, TypeError):
            analysis_results = {}
    
    # Create structured response
    formatted_response = await _create_comprehensive_response(
        research_findings, analysis_results, user_question
    )
    
    # Generate executive summary
    executive_summary = _create_executive_summary(
        research_findings, analysis_results, user_question
    )
    
    # Add formatting metadata
    formatting_metadata = _create_formatting_metadata(
        formatted_response, research_findings, analysis_results
    )
    
    return {
        "formatted_response": formatted_response,
        "executive_summary": executive_summary,
        "response_sections": _extract_response_sections(formatted_response),
        "readability_score": formatting_metadata.get("readability_score", "medium"),
        "response_length": formatting_metadata.get("response_length", 0),
        "formatting_metadata": {
            "sections_count": formatting_metadata.get("sections_count", 0),
            "data_sources_cited": formatting_metadata.get("sources_cited", 0),
            "visual_elements": formatting_metadata.get("visual_elements", 0),
            "response_type": _determine_response_type(user_question)
        }
    }


@dspy_worker(
    "format_financial_analysis",
    signature="financial_data, calculations, query -> formatted_analysis, key_metrics",
    timeout=45,
    retry_attempts=2,
    model=get_formatter_config().model
)
async def format_financial_analysis_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formatter Agent for financial analysis responses.
    
    This agent specializes in formatting financial calculations and analysis
    into clear, actionable investment insights with proper context and disclaimers.
    """
    financial_data = context.get("financial_data", {})
    calculations = context.get("calculations", {})
    query = context.get("query", context.get("user_question", ""))
    
    # Parse JSON data if needed
    if isinstance(calculations, str):
        try:
            calculations = json.loads(calculations)
        except (json.JSONDecodeError, TypeError):
            calculations = {}
    
    # Create financial analysis response
    formatted_analysis = await _create_financial_analysis_response(
        financial_data, calculations, query
    )
    
    # Extract key metrics for quick reference
    key_metrics = _extract_key_financial_metrics(calculations)
    
    # Add financial disclaimers and context
    formatted_analysis_with_disclaimers = _add_financial_disclaimers(formatted_analysis)
    
    return {
        "formatted_analysis": formatted_analysis_with_disclaimers,
        "key_metrics": json.dumps(key_metrics),
        "investment_summary": key_metrics.get("summary", ""),
        "risk_disclosure": _generate_risk_disclosure(calculations),
        "action_items": _generate_action_items(calculations, query),
        "formatting_metadata": {
            "analysis_type": "financial",
            "calculations_included": len(calculations),
            "risk_level": _assess_risk_level(calculations),
            "confidence_level": _assess_confidence_level(calculations, financial_data)
        }
    }


async def _create_comprehensive_response(research_findings: Dict[str, Any], 
                                       analysis_results: Dict[str, Any],
                                       user_question: str) -> str:
    """Create a comprehensive, well-structured response."""
    
    sections = []
    
    # Introduction
    sections.append(_create_introduction_section(user_question))
    
    # Research Findings Section
    if research_findings:
        sections.append(_create_research_section(research_findings))
    
    # Analysis Results Section
    if analysis_results:
        sections.append(_create_analysis_section(analysis_results))
    
    # Synthesis and Insights Section
    sections.append(_create_insights_section(research_findings, analysis_results))
    
    # Recommendations Section
    sections.append(_create_recommendations_section(research_findings, analysis_results, user_question))
    
    # Conclusion
    sections.append(_create_conclusion_section(user_question, research_findings, analysis_results))
    
    return "\n\n".join(sections)


def _create_introduction_section(user_question: str) -> str:
    """Create an introduction section."""
    return f"""## Research Analysis Response

**Your Question:** {user_question}

Based on comprehensive research and analysis, here are the findings and insights:"""


def _create_research_section(research_findings: Dict[str, Any]) -> str:
    """Create the research findings section."""
    section = "## 🔍 Research Findings\n"
    
    # Summary
    summary = research_findings.get("summary", "")
    if summary:
        section += f"**Overview:** {summary}\n\n"
    
    # Key insights
    key_insights = research_findings.get("key_insights", [])
    if key_insights:
        section += "**Key Research Insights:**\n"
        for i, insight in enumerate(key_insights[:5], 1):  # Limit to 5 insights
            section += f"{i}. {insight}\n"
        section += "\n"
    
    # Topics covered
    topics = research_findings.get("topics_covered", [])
    if topics:
        section += f"**Research Areas Covered:** {', '.join(topics)}\n\n"
    
    # Data quality and confidence
    confidence = research_findings.get("confidence_level", "medium")
    section += f"**Research Confidence Level:** {confidence.title()}\n"
    
    return section


def _create_analysis_section(analysis_results: Dict[str, Any]) -> str:
    """Create the analysis results section."""
    section = "## 📊 Analysis Results\n"
    
    # Check if it's financial analysis
    if "roi_analysis" in analysis_results or "calculations" in analysis_results:
        return _create_financial_analysis_section(analysis_results)
    
    # Statistical analysis
    if "basic_stats" in analysis_results:
        return _create_statistical_analysis_section(analysis_results)
    
    # General analysis
    analysis_summary = analysis_results.get("summary", "")
    if analysis_summary:
        section += f"**Analysis Summary:** {analysis_summary}\n\n"
    
    return section


def _create_financial_analysis_section(analysis_results: Dict[str, Any]) -> str:
    """Create financial analysis section."""
    section = "## 💰 Financial Analysis\n"
    
    # ROI Analysis
    roi_analysis = analysis_results.get("roi_analysis", {})
    if roi_analysis and not roi_analysis.get("error"):
        section += "**Return on Investment (ROI):**\n"
        section += f"• Total ROI: {roi_analysis.get('total_roi_percent', 0)}%\n"
        section += f"• Annualized Return: {roi_analysis.get('annualized_return_percent', 0)}%\n"
        section += f"• Profit/Loss: ${roi_analysis.get('profit_loss', 0):,.2f}\n\n"
    
    # Compound Interest
    compound = analysis_results.get("compound_interest", {})
    if compound and not compound.get("error"):
        section += "**Compound Interest Analysis:**\n"
        section += f"• Final Amount: ${compound.get('final_amount', 0):,.2f}\n"
        section += f"• Interest Earned: ${compound.get('interest_earned', 0):,.2f}\n\n"
    
    # Risk Scenarios
    risk_scenarios = analysis_results.get("risk_scenarios", {})
    if risk_scenarios:
        section += "**Risk Scenario Analysis:**\n"
        conservative = risk_scenarios.get("conservative", {})
        optimistic = risk_scenarios.get("optimistic", {})
        
        if conservative:
            section += f"• Conservative Scenario: {conservative.get('total_roi_percent', 0)}% ROI\n"
        if optimistic:
            section += f"• Optimistic Scenario: {optimistic.get('total_roi_percent', 0)}% ROI\n"
        section += "\n"
    
    return section


def _create_statistical_analysis_section(analysis_results: Dict[str, Any]) -> str:
    """Create statistical analysis section."""
    section = "## 📈 Statistical Analysis\n"
    
    basic_stats = analysis_results.get("basic_stats", {})
    if basic_stats:
        section += "**Descriptive Statistics:**\n"
        section += f"• Dataset Size: {basic_stats.get('count', 0)} values\n"
        section += f"• Mean: {basic_stats.get('mean', 0):.2f}\n"
        section += f"• Median: {basic_stats.get('median', 0):.2f}\n"
        section += f"• Range: {basic_stats.get('min', 0):.2f} to {basic_stats.get('max', 0):.2f}\n\n"
    
    # Trend analysis
    trend = analysis_results.get("trend_analysis", {})
    if trend and trend.get("trend") != "insufficient_data":
        section += "**Trend Analysis:**\n"
        section += f"• Trend Direction: {trend.get('trend', 'Unknown').title()}\n"
        if trend.get("correlation_coefficient"):
            section += f"• Correlation Strength: {trend.get('trend_strength', 'Unknown').title()}\n"
        section += "\n"
    
    # Outliers
    outliers = analysis_results.get("outliers", {})
    if outliers.get("count", 0) > 0:
        section += f"**Data Quality Notes:**\n"
        section += f"• {outliers['count']} outliers detected ({outliers.get('percentage', 0)}% of data)\n\n"
    
    return section


def _create_insights_section(research_findings: Dict[str, Any], 
                           analysis_results: Dict[str, Any]) -> str:
    """Create insights and synthesis section."""
    section = "## 💡 Key Insights & Synthesis\n"
    
    insights = []
    
    # Extract insights from research
    research_insights = research_findings.get("key_insights", [])
    insights.extend(research_insights[:3])  # Top 3 research insights
    
    # Extract insights from analysis
    if "key_insights" in analysis_results:
        analysis_insights = analysis_results.get("key_insights", [])
        insights.extend(analysis_insights[:3])  # Top 3 analysis insights
    
    # Generate synthesis insights
    synthesis_insights = _generate_synthesis_insights(research_findings, analysis_results)
    insights.extend(synthesis_insights)
    
    if insights:
        for i, insight in enumerate(insights[:6], 1):  # Limit to 6 total insights
            section += f"{i}. {insight}\n"
    else:
        section += "Based on the available data, key patterns and trends have been identified.\n"
    
    section += "\n"
    return section


def _create_recommendations_section(research_findings: Dict[str, Any],
                                  analysis_results: Dict[str, Any],
                                  user_question: str) -> str:
    """Create recommendations section."""
    section = "## 🎯 Recommendations\n"
    
    recommendations = []
    
    # Extract existing recommendations
    if "recommendations" in research_findings:
        recommendations.extend(research_findings["recommendations"][:3])
    
    if "recommendations" in analysis_results:
        recommendations.extend(analysis_results["recommendations"][:3])
    
    # Generate contextual recommendations
    contextual_recs = _generate_contextual_recommendations(user_question, research_findings, analysis_results)
    recommendations.extend(contextual_recs)
    
    if recommendations:
        for i, rec in enumerate(recommendations[:5], 1):  # Limit to 5 recommendations
            section += f"{i}. {rec}\n"
    else:
        section += "1. Continue monitoring market conditions and trends\n"
        section += "2. Consider diversification to manage risk\n"
        section += "3. Review and adjust strategy based on performance\n"
    
    section += "\n"
    return section


def _create_conclusion_section(user_question: str, research_findings: Dict[str, Any],
                             analysis_results: Dict[str, Any]) -> str:
    """Create conclusion section."""
    section = "## 🎯 Conclusion\n"
    
    # Determine overall sentiment
    sentiment = _determine_overall_sentiment(research_findings, analysis_results)
    
    if "investment" in user_question.lower() or "roi" in user_question.lower():
        if sentiment == "positive":
            section += "Based on the research and analysis, this investment opportunity shows promising potential with favorable risk-adjusted returns."
        elif sentiment == "negative":
            section += "The analysis indicates some challenges and risks that should be carefully considered before proceeding."
        else:
            section += "The investment shows mixed signals requiring careful evaluation of personal risk tolerance and investment goals."
    else:
        section += "The comprehensive analysis provides valuable insights to inform your decision-making process."
    
    section += f"\n\n**Analysis completed on:** {datetime.now().strftime('%Y-%m-%d at %H:%M')}"
    
    return section


def _create_executive_summary(research_findings: Dict[str, Any],
                            analysis_results: Dict[str, Any],
                            user_question: str) -> str:
    """Create a concise executive summary."""
    summary_parts = []
    
    # Key finding
    if research_findings.get("summary"):
        summary_parts.append(f"Research shows: {research_findings['summary'][:100]}...")
    
    # Key analysis result
    if "roi_analysis" in analysis_results:
        roi = analysis_results["roi_analysis"]
        if not roi.get("error"):
            summary_parts.append(f"Analysis indicates {roi.get('total_roi_percent', 0)}% total ROI")
    
    # Overall recommendation
    sentiment = _determine_overall_sentiment(research_findings, analysis_results)
    if sentiment == "positive":
        summary_parts.append("Overall outlook is favorable")
    elif sentiment == "negative":
        summary_parts.append("Caution advised based on current analysis")
    else:
        summary_parts.append("Mixed signals require careful consideration")
    
    return ". ".join(summary_parts) + "."


async def _create_financial_analysis_response(financial_data: Dict[str, Any],
                                            calculations: Dict[str, Any],
                                            query: str) -> str:
    """Create specialized financial analysis response."""
    sections = []
    
    # Financial Overview
    sections.append("## 💰 Financial Analysis Overview\n")
    sections.append(f"**Analysis for:** {query}\n")
    
    # Investment Parameters
    if "roi_analysis" in calculations:
        roi = calculations["roi_analysis"]
        if not roi.get("error"):
            sections.append("**Investment Parameters:**")
            sections.append(f"• Initial Investment: ${roi.get('initial_investment', 0):,.2f}")
            sections.append(f"• Investment Period: {roi.get('years', 0)} years")
            sections.append(f"• Final Value: ${roi.get('final_value', 0):,.2f}\n")
    
    # Performance Metrics
    sections.append(_create_financial_analysis_section(calculations))
    
    # Risk Assessment
    sections.append(_create_risk_assessment_section(calculations))
    
    return "\n".join(sections)


def _create_risk_assessment_section(calculations: Dict[str, Any]) -> str:
    """Create risk assessment section."""
    section = "## ⚠️ Risk Assessment\n"
    
    risk_scenarios = calculations.get("risk_scenarios", {})
    if risk_scenarios:
        conservative = risk_scenarios.get("conservative", {})
        optimistic = risk_scenarios.get("optimistic", {})
        
        if conservative and optimistic:
            conservative_roi = conservative.get("total_roi_percent", 0)
            optimistic_roi = optimistic.get("total_roi_percent", 0)
            
            risk_range = optimistic_roi - conservative_roi
            
            section += f"**Risk-Return Profile:**\n"
            section += f"• Return Range: {conservative_roi:.1f}% to {optimistic_roi:.1f}%\n"
            section += f"• Risk Spread: {risk_range:.1f} percentage points\n"
            
            if risk_range > 30:
                section += "• Risk Level: High volatility expected\n"
            elif risk_range > 15:
                section += "• Risk Level: Moderate volatility expected\n"
            else:
                section += "• Risk Level: Low to moderate volatility expected\n"
    
    section += "\n"
    return section


def _extract_key_financial_metrics(calculations: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key financial metrics for quick reference."""
    metrics = {}
    
    roi_analysis = calculations.get("roi_analysis", {})
    if roi_analysis and not roi_analysis.get("error"):
        metrics.update({
            "total_roi": f"{roi_analysis.get('total_roi_percent', 0)}%",
            "annual_return": f"{roi_analysis.get('annualized_return_percent', 0)}%",
            "profit_loss": f"${roi_analysis.get('profit_loss', 0):,.2f}"
        })
    
    compound = calculations.get("compound_interest", {})
    if compound and not compound.get("error"):
        metrics["compound_interest"] = f"${compound.get('interest_earned', 0):,.2f}"
    
    # Create summary
    if metrics:
        if "total_roi" in metrics:
            metrics["summary"] = f"Investment shows {metrics['total_roi']} total return"
        else:
            metrics["summary"] = "Financial analysis completed"
    
    return metrics


def _add_financial_disclaimers(formatted_analysis: str) -> str:
    """Add appropriate financial disclaimers."""
    disclaimer = """
---
**Important Disclaimers:**
• This analysis is for informational purposes only and does not constitute financial advice
• Past performance does not guarantee future results
• All investments carry risk of loss
• Consult with a qualified financial advisor before making investment decisions
• Market conditions and regulations may affect actual returns
"""
    
    return formatted_analysis + disclaimer


def _generate_risk_disclosure(calculations: Dict[str, Any]) -> str:
    """Generate risk disclosure statement."""
    risk_factors = [
        "Market volatility may affect investment returns",
        "Economic conditions can impact performance",
        "Regulatory changes may affect investment outcomes"
    ]
    
    # Add specific risks based on calculations
    risk_scenarios = calculations.get("risk_scenarios", {})
    if risk_scenarios:
        conservative = risk_scenarios.get("conservative", {})
        if conservative and conservative.get("total_roi_percent", 0) < 0:
            risk_factors.append("Potential for negative returns in conservative scenarios")
    
    return "Risk factors include: " + "; ".join(risk_factors) + "."


def _generate_action_items(calculations: Dict[str, Any], query: str) -> List[str]:
    """Generate actionable next steps."""
    actions = []
    
    query_lower = query.lower()
    
    if "investment" in query_lower:
        actions.extend([
            "Review your risk tolerance and investment timeline",
            "Consider portfolio diversification strategies",
            "Monitor market conditions regularly"
        ])
    
    roi_analysis = calculations.get("roi_analysis", {})
    if roi_analysis and roi_analysis.get("total_roi_percent", 0) > 20:
        actions.append("Consider taking partial profits at milestones")
    
    return actions[:4]  # Limit to 4 actions


def _generate_synthesis_insights(research_findings: Dict[str, Any],
                               analysis_results: Dict[str, Any]) -> List[str]:
    """Generate synthesis insights combining research and analysis."""
    insights = []
    
    # Check for alignment between research and analysis
    research_confidence = research_findings.get("confidence_level", "medium")
    analysis_confidence = analysis_results.get("calculation_accuracy", "medium")
    
    if research_confidence == "high" and analysis_confidence == "high":
        insights.append("Both research and analysis support high confidence in findings")
    
    # Look for trend alignment
    research_summary = research_findings.get("summary", "").lower()
    if "growth" in research_summary and "roi_analysis" in analysis_results:
        roi = analysis_results["roi_analysis"]
        if roi.get("total_roi_percent", 0) > 15:
            insights.append("Research trends align with positive financial projections")
    
    return insights


def _generate_contextual_recommendations(user_question: str,
                                       research_findings: Dict[str, Any],
                                       analysis_results: Dict[str, Any]) -> List[str]:
    """Generate contextual recommendations based on question type."""
    recommendations = []
    question_lower = user_question.lower()
    
    if "renewable energy" in question_lower:
        recommendations.extend([
            "Consider ESG (Environmental, Social, Governance) factors in decision-making",
            "Monitor government policy changes affecting renewable energy sector"
        ])
    
    if "roi" in question_lower or "investment" in question_lower:
        roi_analysis = analysis_results.get("roi_analysis", {})
        if roi_analysis and roi_analysis.get("annualized_return_percent", 0) > 10:
            recommendations.append("High returns detected - verify assumptions and market conditions")
    
    return recommendations


def _determine_overall_sentiment(research_findings: Dict[str, Any],
                               analysis_results: Dict[str, Any]) -> str:
    """Determine overall sentiment of findings."""
    positive_indicators = 0
    negative_indicators = 0
    
    # Check research sentiment
    research_summary = research_findings.get("summary", "").lower()
    if any(word in research_summary for word in ["growth", "increase", "positive", "strong"]):
        positive_indicators += 1
    if any(word in research_summary for word in ["decline", "decrease", "negative", "weak"]):
        negative_indicators += 1
    
    # Check analysis sentiment
    roi_analysis = analysis_results.get("roi_analysis", {})
    if roi_analysis and not roi_analysis.get("error"):
        roi_percent = roi_analysis.get("total_roi_percent", 0)
        if roi_percent > 15:
            positive_indicators += 2
        elif roi_percent > 5:
            positive_indicators += 1
        elif roi_percent < 0:
            negative_indicators += 2
    
    if positive_indicators > negative_indicators:
        return "positive"
    elif negative_indicators > positive_indicators:
        return "negative"
    else:
        return "neutral"


def _create_formatting_metadata(formatted_response: str,
                               research_findings: Dict[str, Any],
                               analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Create metadata about the formatting."""
    return {
        "response_length": len(formatted_response),
        "sections_count": formatted_response.count("##"),
        "sources_cited": len(research_findings.get("sources", [])),
        "visual_elements": formatted_response.count("•") + formatted_response.count("**"),
        "readability_score": "high" if len(formatted_response) < 2000 else "medium"
    }


def _extract_response_sections(formatted_response: str) -> List[str]:
    """Extract section titles from formatted response."""
    import re
    sections = re.findall(r'## (.+)', formatted_response)
    return sections


def _determine_response_type(user_question: str) -> str:
    """Determine the type of response based on user question."""
    question_lower = user_question.lower()
    
    if any(word in question_lower for word in ["roi", "investment", "return", "profit"]):
        return "financial_analysis"
    elif any(word in question_lower for word in ["trend", "analysis", "data"]):
        return "analytical_report"
    elif any(word in question_lower for word in ["compare", "versus", "vs"]):
        return "comparative_analysis"
    else:
        return "general_research"


def _assess_risk_level(calculations: Dict[str, Any]) -> str:
    """Assess risk level based on calculations."""
    risk_scenarios = calculations.get("risk_scenarios", {})
    if risk_scenarios:
        conservative = risk_scenarios.get("conservative", {})
        optimistic = risk_scenarios.get("optimistic", {})
        
        if conservative and optimistic:
            conservative_roi = conservative.get("total_roi_percent", 0)
            optimistic_roi = optimistic.get("total_roi_percent", 0)
            risk_spread = optimistic_roi - conservative_roi
            
            if risk_spread > 30:
                return "high"
            elif risk_spread > 15:
                return "medium"
            else:
                return "low"
    
    return "medium"


def _assess_confidence_level(calculations: Dict[str, Any], 
                           financial_data: Dict[str, Any]) -> str:
    """Assess confidence level in analysis."""
    confidence_factors = 0
    
    # Check calculation completeness
    if calculations and len(calculations) > 2:
        confidence_factors += 1
    
    # Check for errors in calculations
    has_errors = any(calc.get("error") for calc in calculations.values() if isinstance(calc, dict))
    if not has_errors:
        confidence_factors += 1
    
    # Check data availability
    if financial_data and len(financial_data) > 0:
        confidence_factors += 1
    
    if confidence_factors >= 2:
        return "high"
    elif confidence_factors >= 1:
        return "medium"
    else:
        return "low"