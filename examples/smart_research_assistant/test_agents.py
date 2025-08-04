"""
Test script for individual agents.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

import asyncio
from agents.coordinator import coordinate_research_worker, synthesize_findings_worker
from agents.researcher import clarify_research_needs_worker, conduct_research_worker
from agents.analyst import analyze_financial_data_worker, analyze_statistical_data_worker, perform_calculations_worker
from agents.formatter import format_research_response_worker, format_financial_analysis_worker


async def test_coordinator_agent():
    """Test the Coordinator Agent."""
    print("🎯 Testing Coordinator Agent...")
    
    # Test coordination
    context = {
        "user_question": "What's the ROI of investing in renewable energy stocks?",
        "context": {}
    }
    
    result = await coordinate_research_worker.execute(context)
    print(f"  Coordination decision: {result.get('routing_decision', 'N/A')}")
    print(f"  Requires clarification: {result.get('requires_clarification', False)}")
    print(f"  Question intent: {result.get('question_analysis', {}).get('detected_intent', 'Unknown')}")
    
    assert "routing_decision" in result
    print("  ✅ Coordinator agent test passed!")


async def test_research_agent():
    """Test the Research Agent.""" 
    print("🔍 Testing Research Agent...")
    
    # Test clarification phase
    context = {
        "user_question": "What are the best renewable energy investments?",
        "context": {}
    }
    
    clarification_result = await clarify_research_needs_worker.execute(context)
    print(f"  Clarification questions generated: {clarification_result.get('needs_clarification', False)}")
    print(f"  Research areas identified: {len(clarification_result.get('priority_areas', '[]'))}")
    
    # Test research phase
    research_context = {
        "research_query": "renewable energy stocks ROI analysis",
        "clarifications": {
            "timeframe": "5 years",
            "investment_amount": "$10,000-$25,000",
            "risk_tolerance": "moderate"
        },
        "context": {}
    }
    
    research_result = await conduct_research_worker.execute(research_context)
    print(f"  Research confidence: {research_result.get('confidence_level', 'Unknown')}")
    print(f"  Sources found: {research_result.get('research_metadata', {}).get('sources_found', 0)}")
    print(f"  Data quality: {research_result.get('data_quality', 'Unknown')}")
    
    assert "research_findings" in research_result
    print("  ✅ Research agent test passed!")


async def test_coordination_synthesis():
    """Test coordination and synthesis workflow."""
    print("🔄 Testing Agent Coordination...")
    
    # Mock research findings
    research_findings = {
        "summary": "Renewable energy stocks show strong growth potential",
        "key_insights": ["Solar sector up 25%", "Wind energy expanding"],
        "confidence_level": "high"
    }
    
    # Mock analysis results
    analysis_results = {
        "roi_calculation": {"total_roi_percent": 28.5, "annualized_return": 7.2},
        "summary": "Positive ROI projections based on market trends"
    }
    
    synthesis_context = {
        "research_findings": research_findings,
        "analysis_results": analysis_results,
        "user_question": "What's the ROI of renewable energy investments?"
    }
    
    synthesis_result = await synthesize_findings_worker.execute(synthesis_context)
    print(f"  Synthesis confidence: {synthesis_result.get('synthesis_metadata', {}).get('confidence_level', 'Unknown')}")
    print(f"  Recommendations generated: {len(synthesis_result.get('recommendations', []))}")
    
    assert "synthesized_insights" in synthesis_result
    print("  ✅ Coordination synthesis test passed!")


async def test_analyst_agent():
    """Test the Analyst Agent."""
    print("📊 Testing Analyst Agent...")
    
    # Test financial analysis
    financial_context = {
        "financial_query": "Calculate ROI for $10,000 investment over 5 years with 8% annual return",
        "data_inputs": "investment_amount: $10,000, timeframe: 5 years, expected_return: 8%",
        "calculation_requirements": "ROI analysis with risk scenarios"
    }
    
    financial_result = await analyze_financial_data_worker.execute(financial_context)
    print(f"  Financial analysis confidence: {financial_result.get('analysis_confidence', 'Unknown')}")
    print(f"  Calculations performed: {financial_result.get('calculation_metadata', {}).get('calculations_performed', 0)}")
    
    # Test statistical analysis
    statistical_context = {
        "data_query": "Analyze stock return data",
        "dataset": [2.1, -1.5, 3.2, 0.8, -2.1, 4.3, 1.7, -0.9, 2.8, 1.2],
        "analysis_type": "financial"
    }
    
    statistical_result = await analyze_statistical_data_worker.execute(statistical_context)
    print(f"  Statistical analysis outliers: {statistical_result.get('analysis_metadata', {}).get('outliers_detected', 0)}")
    print(f"  Data quality score: {statistical_result.get('data_quality_score', 'Unknown')}")
    
    assert "analysis_results" in financial_result
    assert "statistical_results" in statistical_result
    print("  ✅ Analyst agent test passed!")


async def test_formatter_agent():
    """Test the Formatter Agent."""
    print("📝 Testing Formatter Agent...")
    
    # Mock comprehensive data for formatting
    mock_research = {
        "summary": "Renewable energy stocks show strong growth potential",
        "key_insights": ["Solar sector up 25%", "Wind energy expanding globally"],
        "confidence_level": "high"
    }
    
    mock_analysis = {
        "roi_analysis": {
            "total_roi_percent": 35.0,
            "annualized_return_percent": 8.5,
            "profit_loss": 3500.0
        },
        "calculations": {"roi": "calculated"},
        "analysis_confidence": "high"
    }
    
    format_context = {
        "research_findings": mock_research,
        "analysis_results": mock_analysis,
        "user_question": "What's the ROI of renewable energy investments?"
    }
    
    format_result = await format_research_response_worker.execute(format_context)
    print(f"  Response sections: {len(format_result.get('response_sections', []))}")
    print(f"  Readability score: {format_result.get('readability_score', 'Unknown')}")
    print(f"  Response length: {format_result.get('response_length', 0)} characters")
    
    # Test financial formatting
    financial_format_context = {
        "calculations": mock_analysis,
        "query": "Investment analysis for renewable energy"
    }
    
    financial_format_result = await format_financial_analysis_worker.execute(financial_format_context)
    print(f"  Financial format confidence: {financial_format_result.get('formatting_metadata', {}).get('confidence_level', 'Unknown')}")
    
    assert "formatted_response" in format_result
    assert "formatted_analysis" in financial_format_result
    print("  ✅ Formatter agent test passed!")


async def main():
    """Run all agent tests."""
    print("🧪 Testing Smart Research Assistant Agents\n")
    
    try:
        await test_coordinator_agent()
        print()
        await test_research_agent()
        print()
        await test_analyst_agent()
        print()
        await test_formatter_agent()
        print()
        await test_coordination_synthesis()
        
        print("\n✅ All agent tests PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Agent tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)