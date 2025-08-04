"""
Research Agent - Conducts comprehensive research with interactive clarification.

This agent specializes in:
1. Asking clarifying questions to understand research needs
2. Conducting comprehensive web research using Google Custom Search
3. Synthesizing information from multiple sources
4. Providing confidence assessments and source tracking
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from typing import Dict, Any, List, Optional
import json
import asyncio

from multiagents.worker_sdk import dspy_worker
from config.gemini_config import get_researcher_config
from tools.web_search import search_web, search_news, get_research_sources


@dspy_worker(
    "clarify_research_needs",
    signature="user_question, context -> clarification_questions, research_plan, priority_areas",
    timeout=45,
    retry_attempts=2,
    model=get_researcher_config().model
)
async def clarify_research_needs_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Research Agent Phase 1: Clarifies research requirements and scope.
    
    Analyzes the user's question to determine:
    1. What specific information is needed
    2. What aspects require clarification
    3. Research scope and priorities
    4. Data sources to target
    """
    user_question = context.get("user_question", "")
    existing_context = context.get("context", {})
    
    # Access DSPy agent
    dspy_agent = context.get("_dspy_agent")
    
    if dspy_agent:
        try:
            # Use LLM to generate clarification questions
            clarification_signature = dspy_agent.create_signature(
                "research_question, context",
                "needs_clarification, clarification_questions, research_scope, key_areas, search_terms"
            )
            
            clarification_result = dspy_agent.predict(
                clarification_signature,
                research_question=user_question,
                context=str(existing_context)
            )
            
            # Parse LLM results
            needs_clarification = clarification_result.get("needs_clarification", "false").lower() in ["true", "yes", "1"]
            clarification_questions = clarification_result.get("clarification_questions", "")
            research_scope = clarification_result.get("research_scope", "")
            key_areas = clarification_result.get("key_areas", "").split(",") if clarification_result.get("key_areas") else []
            search_terms = clarification_result.get("search_terms", "").split(",") if clarification_result.get("search_terms") else []
            
        except Exception as e:
            print(f"DSPy clarification failed, using fallback: {e}")
            needs_clarification, clarification_questions, research_scope, key_areas, search_terms = _fallback_clarification_logic(user_question)
    else:
        needs_clarification, clarification_questions, research_scope, key_areas, search_terms = _fallback_clarification_logic(user_question)
    
    # Create research plan
    research_plan = {
        "search_terms": search_terms or _generate_search_terms(user_question),
        "target_sources": _identify_target_sources(user_question),
        "research_depth": "comprehensive" if any(term in user_question.lower() for term in ["analyze", "detailed", "comprehensive"]) else "focused",
        "time_sensitivity": "recent" if any(term in user_question.lower() for term in ["latest", "recent", "current", "2024", "2025"]) else "general",
        "priority_areas": key_areas or _extract_priority_areas(user_question)
    }
    
    return {
        "needs_clarification": needs_clarification,
        "clarification_questions": clarification_questions,
        "research_plan": json.dumps(research_plan),
        "priority_areas": json.dumps(key_areas or _extract_priority_areas(user_question)),
        "search_strategy": {
            "primary_terms": search_terms[:3] if search_terms else _generate_search_terms(user_question)[:3],
            "research_method": "llm_guided" if dspy_agent else "rule_based",
            "scope": research_scope or "comprehensive_analysis"
        }
    }


@dspy_worker(
    "conduct_research", 
    signature="research_query, clarifications, context -> research_findings, key_insights, confidence_level",
    timeout=120,
    retry_attempts=2,
    model=get_researcher_config().model
)
async def conduct_research_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Research Agent Phase 2: Conducts comprehensive research using real web search.
    
    Performs actual research by:
    1. Using Google Custom Search API for real web results
    2. Analyzing multiple sources for comprehensive coverage
    3. Synthesizing findings using LLM capabilities
    4. Providing confidence assessments and source tracking
    """
    research_query = context.get("research_query", context.get("user_question", ""))
    clarifications = context.get("clarifications", {})
    existing_context = context.get("context", {})
    
    # Extract research parameters from clarifications
    timeframe = clarifications.get("timeframe", "current")
    investment_amount = clarifications.get("investment_amount", "")
    risk_tolerance = clarifications.get("risk_tolerance", "moderate")
    geographic_focus = clarifications.get("geographic_focus", "global")
    
    # Generate comprehensive search terms
    search_terms = _generate_comprehensive_search_terms(research_query, clarifications)
    
    # Conduct actual web research
    research_sources = []
    total_sources_found = 0
    
    print(f"🔍 Conducting real web research for: {research_query}")
    
    # Primary research - general search
    for term in search_terms[:3]:  # Limit to prevent too many API calls
        try:
            results = search_web(term, num_results=3)
            research_sources.extend(results)
            total_sources_found += len(results)
            print(f"   📄 Found {len(results)} sources for '{term}'")
        except Exception as e:
            print(f"   ❌ Search failed for '{term}': {e}")
    
    # News research for recent developments
    if "recent" in timeframe.lower() or any(term in research_query.lower() for term in ["latest", "current", "2024", "2025"]):
        try:
            news_results = search_news(research_query, num_results=2)
            research_sources.extend(news_results)
            total_sources_found += len(news_results)
            print(f"   📰 Found {len(news_results)} news sources")
        except Exception as e:
            print(f"   ❌ News search failed: {e}")
    
    # Use DSPy to synthesize research findings
    dspy_agent = context.get("_dspy_agent")
    
    if dspy_agent and research_sources:
        try:
            # Prepare research data for LLM analysis
            sources_text = _format_sources_for_llm(research_sources)
            
            # Create research synthesis signature
            synthesis_signature = dspy_agent.create_signature(
                "original_query, research_sources, clarifications",
                "research_summary, key_insights, confidence_assessment, topic_coverage"
            )
            
            # Get LLM synthesis of research
            synthesis_result = dspy_agent.predict(
                synthesis_signature,
                original_query=research_query,
                research_sources=sources_text,
                clarifications=str(clarifications)
            )
            
            # Extract LLM results
            research_summary = synthesis_result.get("research_summary", "")
            key_insights = synthesis_result.get("key_insights", "").split(";") if synthesis_result.get("key_insights") else []
            confidence_level = synthesis_result.get("confidence_assessment", "medium")
            topic_coverage = synthesis_result.get("topic_coverage", "")
            
            print(f"   🧠 LLM synthesis completed - {len(key_insights)} insights generated")
            
        except Exception as e:
            print(f"   ❌ LLM synthesis failed, using fallback: {e}")
            research_summary, key_insights, confidence_level, topic_coverage = _fallback_research_synthesis(
                research_query, research_sources, clarifications
            )
    else:
        print(f"   ⚠️  Using fallback synthesis (no LLM or sources)")
        research_summary, key_insights, confidence_level, topic_coverage = _fallback_research_synthesis(
            research_query, research_sources, clarifications
        )
    
    # Create comprehensive research findings
    research_findings = {
        "summary": research_summary,
        "key_insights": key_insights,
        "sources": [
            {
                "title": source.get("title", ""),
                "url": source.get("url", ""),
                "domain": source.get("domain", ""),
                "snippet": source.get("snippet", "")[:200] + "..." if len(source.get("snippet", "")) > 200 else source.get("snippet", ""),
                "source_type": source.get("source", "web_search")
            }
            for source in research_sources[:10]  # Limit for response size
        ],
        "topics_covered": topic_coverage.split(",") if topic_coverage else _extract_topics_from_sources(research_sources),
        "research_metadata": {
            "sources_found": total_sources_found,
            "search_terms_used": search_terms,
            "research_method": "llm_enhanced" if dspy_agent else "rule_based",
            "geographic_focus": geographic_focus,
            "timeframe": timeframe,
            "search_strategy": "comprehensive_multi_source"
        }
    }
    
    return {
        "research_findings": json.dumps(research_findings),
        "summary": research_summary,
        "key_insights": key_insights,
        "confidence_level": confidence_level,
        "data_quality": "high" if total_sources_found >= 5 else "medium" if total_sources_found >= 2 else "low",
        "research_metadata": research_findings["research_metadata"]
    }


def _fallback_clarification_logic(user_question: str) -> tuple:
    """Fallback clarification logic when DSPy is not available."""
    question_lower = user_question.lower()
    
    # Determine if clarification is needed
    needs_clarification = any(term in question_lower for term in [
        "best", "good", "recommend", "should", "which", "how much", "when"
    ]) and not any(term in question_lower for term in [
        "specific", "exactly", "precisely", "$", "year", "month"
    ])
    
    # Generate clarification questions based on question type
    clarification_questions = ""
    if needs_clarification:
        if "investment" in question_lower:
            clarification_questions = "What is your investment timeframe? What is your risk tolerance? What investment amount are you considering?"
        elif "analysis" in question_lower:
            clarification_questions = "What specific aspects would you like analyzed? What timeframe should be considered? Are there particular metrics of interest?"
        else:
            clarification_questions = "Could you provide more specific details about your requirements? What particular aspects are most important to you?"
    
    # Research scope
    if "comprehensive" in question_lower or "detailed" in question_lower:
        research_scope = "comprehensive_analysis"
    elif "quick" in question_lower or "brief" in question_lower:
        research_scope = "focused_summary"
    else:
        research_scope = "balanced_research"
    
    # Key areas and search terms
    key_areas = _extract_priority_areas(user_question)
    search_terms = _generate_search_terms(user_question)
    
    return needs_clarification, clarification_questions, research_scope, key_areas, search_terms


def _generate_search_terms(question: str) -> List[str]:
    """Generate search terms from the user question."""
    terms = []
    question_lower = question.lower()
    
    # Extract key financial terms
    if any(term in question_lower for term in ["investment", "stock", "roi"]):
        if "renewable" in question_lower:
            terms.extend(["renewable energy stocks", "clean energy investment", "ESG renewable portfolio"])
        elif "tech" in question_lower:
            terms.extend(["technology stocks ROI", "tech investment returns", "FAANG stock analysis"])
        else:
            terms.extend(["investment analysis", "stock market returns", "portfolio performance"])
    
    # Market research terms
    if any(term in question_lower for term in ["trend", "market", "growth"]):
        if "solar" in question_lower or "renewable" in question_lower:
            terms.extend(["solar energy market trends", "renewable energy growth", "clean energy statistics"])
        else:
            terms.extend(["market analysis", "industry trends", "growth projections"])
    
    # ESG and sustainability
    if any(term in question_lower for term in ["esg", "sustainable", "green"]):
        terms.extend(["ESG investment opportunities", "sustainable investing", "green finance"])
    
    # Technology and innovation
    if any(term in question_lower for term in ["ai", "quantum", "technology"]):
        terms.extend(["artificial intelligence trends", "quantum computing developments", "tech innovation"])
    
    # Default terms if nothing specific found
    if not terms:
        # Extract main keywords from question
        words = question.split()
        key_words = [word for word in words if len(word) > 3 and word.lower() not in ["what", "how", "when", "where", "why", "the", "and", "or"]]
        terms.extend(key_words[:3])
    
    return terms[:5]  # Limit to 5 terms


def _generate_comprehensive_search_terms(research_query: str, clarifications: Dict[str, Any]) -> List[str]:
    """Generate comprehensive search terms including clarifications."""
    base_terms = _generate_search_terms(research_query)
    
    # Add clarification-specific terms
    additional_terms = []
    
    if clarifications.get("timeframe"):
        timeframe = clarifications["timeframe"]
        if "5 year" in timeframe or "long-term" in timeframe:
            additional_terms.append(f"{research_query} long term analysis")
    
    if clarifications.get("investment_amount"):
        amount = clarifications["investment_amount"]
        if "$" in amount:
            additional_terms.append(f"{research_query} investment strategy")
    
    if clarifications.get("geographic_focus"):
        geo = clarifications["geographic_focus"]
        additional_terms.append(f"{research_query} {geo} market")
    
    # Combine and deduplicate
    all_terms = base_terms + additional_terms
    return list(set(all_terms))[:8]  # Limit to prevent too many API calls


def _identify_target_sources(question: str) -> List[str]:
    """Identify target sources based on question type."""
    sources = ["general_web"]
    question_lower = question.lower()
    
    if any(term in question_lower for term in ["investment", "stock", "financial"]):
        sources.extend(["financial_news", "investment_sites", "market_data"])
    
    if any(term in question_lower for term in ["research", "study", "analysis"]):
        sources.extend(["academic_sources", "research_reports"])
    
    if any(term in question_lower for term in ["latest", "recent", "current"]):
        sources.extend(["news_sites", "press_releases"])
    
    return sources


def _extract_priority_areas(question: str) -> List[str]:
    """Extract priority research areas from the question."""
    areas = []
    question_lower = question.lower()
    
    if "renewable" in question_lower:
        areas.append("renewable_energy")
    if "investment" in question_lower or "roi" in question_lower:
        areas.append("financial_analysis")
    if "market" in question_lower or "trend" in question_lower:
        areas.append("market_research")
    if "risk" in question_lower:
        areas.append("risk_assessment")
    if "growth" in question_lower:
        areas.append("growth_analysis")
    
    return areas or ["general_research"]


def _format_sources_for_llm(sources: List[Dict[str, Any]]) -> str:
    """Format research sources for LLM analysis."""
    if not sources:
        return "No sources available"
    
    formatted_sources = []
    for i, source in enumerate(sources[:8], 1):  # Limit to prevent token overflow
        formatted_sources.append(
            f"Source {i}: {source.get('title', 'Unknown Title')}\n"
            f"Domain: {source.get('domain', 'unknown')}\n"
            f"Content: {source.get('snippet', 'No content available')[:300]}...\n"
        )
    
    return "\n".join(formatted_sources)


def _fallback_research_synthesis(research_query: str, sources: List[Dict[str, Any]], clarifications: Dict[str, Any]) -> tuple:
    """Fallback research synthesis when LLM is not available."""
    
    # Create basic summary
    num_sources = len(sources)
    if num_sources > 0:
        # Extract key information from sources
        key_themes = set()
        for source in sources:
            snippet = source.get("snippet", "").lower()
            if "growth" in snippet:
                key_themes.add("growth trends")
            if "return" in snippet or "roi" in snippet:
                key_themes.add("investment returns")
            if "risk" in snippet:
                key_themes.add("risk factors")
            if "market" in snippet:
                key_themes.add("market analysis")
        
        research_summary = f"Research on '{research_query}' analyzed {num_sources} sources covering {', '.join(list(key_themes)[:3])}."
        
        # Generate basic insights from sources
        key_insights = []
        for source in sources[:5]:  # Top 5 sources
            snippet = source.get("snippet", "")
            if snippet and len(snippet) > 50:
                # Extract the first sentence as an insight
                sentences = snippet.split('. ')
                if sentences and len(sentences[0]) > 20:
                    key_insights.append(sentences[0])
        
        confidence_level = "high" if num_sources >= 5 else "medium" if num_sources >= 2 else "low"
        topic_coverage = ",".join(list(key_themes)) if key_themes else "general_analysis"
        
    else:
        research_summary = f"Limited research data available for '{research_query}'. Using general knowledge and analysis patterns."
        key_insights = [
            "Research indicates mixed market conditions requiring careful analysis",
            "Multiple factors should be considered for comprehensive evaluation",
            "Current market dynamics suggest cautious optimism"
        ]
        confidence_level = "low"
        topic_coverage = "general_analysis"
    
    return research_summary, key_insights, confidence_level, topic_coverage


def _extract_topics_from_sources(sources: List[Dict[str, Any]]) -> List[str]:
    """Extract topics covered from research sources."""
    topics = set()
    
    for source in sources:
        title = source.get("title", "").lower()
        snippet = source.get("snippet", "").lower()
        combined_text = title + " " + snippet
        
        # Extract common financial/research topics
        if any(term in combined_text for term in ["renewable", "solar", "wind"]):
            topics.add("renewable_energy")
        if any(term in combined_text for term in ["investment", "stock", "equity"]):
            topics.add("investments")
        if any(term in combined_text for term in ["market", "trading", "finance"]):
            topics.add("market_analysis")
        if any(term in combined_text for term in ["technology", "tech", "innovation"]):
            topics.add("technology")
        if any(term in combined_text for term in ["growth", "trend", "forecast"]):
            topics.add("growth_trends")
        if any(term in combined_text for term in ["risk", "volatility", "uncertainty"]):
            topics.add("risk_analysis")
    
    return list(topics) if topics else ["general_research"]