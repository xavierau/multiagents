"""
Real Workflow Example with DSPy and Tools
=========================================

A complete workflow example that uses real DSPy with Gemini LM and actual tools.
Demonstrates a content creation pipeline with research, writing, and review stages.
"""

import asyncio
import os
import json
from typing import List, Dict, Any
from multiagents import WorkflowBuilder, dspy_worker, tool, Orchestrator
from multiagents.event_bus import RedisEventBus
import dspy


def configure_dspy():
    """Configure DSPy with Gemini LM."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable required.\n"
            "Get your API key from: https://aistudio.google.com/app/apikey\n"
            "Then set it: export GOOGLE_API_KEY='your-api-key-here'"
        )
    
    lm = dspy.LM(model="gemini/gemini-1.5-flash", api_key=api_key)
    dspy.configure(lm=lm)
    print("✅ DSPy configured with Gemini 1.5 Flash")


# =======================
# Real Tools for Content Creation Pipeline
# =======================

@tool("research_topic")
async def research_topic(topic: str, depth: str = "moderate") -> Dict[str, Any]:
    """Research a topic and gather key information."""
    # In a real implementation, this could use:
    # - Wikipedia API
    # - Google Custom Search API  
    # - Academic databases
    # - Internal knowledge bases
    
    # Mock research data based on common topics
    research_data = {
        "artificial intelligence": {
            "definition": "AI is the simulation of human intelligence in machines",
            "key_concepts": ["machine learning", "deep learning", "neural networks", "natural language processing"],
            "applications": ["healthcare", "finance", "transportation", "entertainment"],
            "trends": ["generative AI", "large language models", "multimodal AI"],
            "challenges": ["bias", "explainability", "safety", "ethics"]
        },
        "python programming": {
            "definition": "Python is a high-level, interpreted programming language",
            "key_concepts": ["object-oriented", "dynamic typing", "interpreted", "cross-platform"],
            "applications": ["web development", "data science", "automation", "AI/ML"],
            "trends": ["async programming", "type hints", "data classes", "pattern matching"],
            "challenges": ["performance", "packaging", "version compatibility"]
        },
        "climate change": {
            "definition": "Long-term shifts in global temperatures and weather patterns",
            "key_concepts": ["greenhouse gases", "carbon footprint", "renewable energy", "sustainability"],
            "applications": ["policy making", "technology development", "lifestyle changes"],
            "trends": ["carbon neutrality", "green technology", "climate adaptation"],
            "challenges": ["global coordination", "economic transition", "public awareness"]
        }
    }
    
    # Find best match for topic
    topic_lower = topic.lower()
    research_result = None
    
    for key, data in research_data.items():
        if key in topic_lower or any(word in topic_lower for word in key.split()):
            research_result = data
            break
    
    # Default research if no match found
    if not research_result:
        research_result = {
            "definition": f"Research topic: {topic}",
            "key_concepts": ["concept1", "concept2", "concept3"],
            "applications": ["application1", "application2"],
            "trends": ["trend1", "trend2"],
            "challenges": ["challenge1", "challenge2"]
        }
    
    # Add metadata
    research_result.update({
        "topic": topic,
        "research_depth": depth,
        "sources": ["Academic papers", "Industry reports", "Expert interviews"],
        "confidence": 0.85,
        "last_updated": "2024-01-01"
    })
    
    print(f"🔬 Researched topic: '{topic}' -> {len(research_result['key_concepts'])} concepts found")
    return research_result


@tool("fact_check")
async def fact_check(content: str, topic: str) -> Dict[str, Any]:
    """Fact-check content against reliable sources."""
    # In a real implementation, this could:
    # - Use fact-checking APIs
    # - Compare against verified databases
    # - Run automated verification checks
    # - Flag questionable claims
    
    await asyncio.sleep(0.2)  # Simulate fact-checking time
    
    # Mock fact-checking logic
    word_count = len(content.split())
    fact_check_result = {
        "accuracy_score": 0.92,  # Mock high accuracy
        "verified_claims": max(3, word_count // 50),
        "questionable_claims": max(0, word_count // 200),
        "sources_checked": ["Wikipedia", "Academic databases", "Government sites"],
        "confidence": 0.88,
        "recommendations": []
    }
    
    # Add recommendations based on "analysis"
    if fact_check_result["questionable_claims"] > 0:
        fact_check_result["recommendations"].append("Review questionable claims with additional sources")
    if fact_check_result["accuracy_score"] < 0.9:
        fact_check_result["recommendations"].append("Consider additional fact verification")
    
    print(f"✅ Fact-checked content: {fact_check_result['accuracy_score']:.1%} accuracy")
    return fact_check_result


@tool("seo_optimize")
def seo_optimize(content: str, target_keywords: List[str]) -> Dict[str, Any]:
    """Optimize content for SEO."""
    # In a real implementation, this could:
    # - Analyze keyword density
    # - Suggest meta descriptions
    # - Check readability scores
    # - Recommend internal/external links
    
    word_count = len(content.split())
    
    # Mock SEO analysis
    keyword_density = {}
    for keyword in target_keywords:
        appearances = content.lower().count(keyword.lower())
        keyword_density[keyword] = (appearances / word_count) * 100 if word_count > 0 else 0
    
    seo_result = {
        "seo_score": 78,  # Mock score out of 100
        "keyword_density": keyword_density,
        "readability_score": 72,
        "word_count": word_count,
        "recommendations": [
            "Add more internal links",
            "Include meta description",
            "Optimize heading structure"
        ],
        "target_keywords": target_keywords,
        "estimated_traffic_potential": "medium"
    }
    
    print(f"🎯 SEO optimized: Score {seo_result['seo_score']}/100")
    return seo_result


@tool("save_content")
async def save_content(content: str, title: str, metadata: Dict[str, Any]) -> Dict[str, str]:
    """Save content to storage system."""
    # In a real implementation, this could:
    # - Save to database
    # - Upload to CMS
    # - Store in file system
    # - Trigger publishing pipeline
    
    await asyncio.sleep(0.1)  # Simulate save operation
    
    # Mock save operation
    content_id = f"content_{hash(title) % 10000:04d}"
    file_path = f"./content/{content_id}.md"
    
    # In a real system, you'd actually save the file
    print(f"💾 Content saved: {title} -> {content_id}")
    
    return {
        "content_id": content_id,
        "file_path": file_path,
        "status": "saved",
        "url": f"https://example.com/content/{content_id}"
    }


# =======================
# DSPy Workers for Content Creation Pipeline
# =======================

@dspy_worker("topic_researcher",
            signature="topic: str, requirements: str -> research_summary: str, key_points: list[str], sources: list[str]",
            tools=[research_topic],
            reasoning="react",
            max_iters=3,
            model="gemini/gemini-1.5-flash")
async def research_topic_worker(context: dict) -> dict:
    """Research a topic thoroughly using available tools and LLM analysis."""
    research_summary = context.get('research_summary', '')
    key_points = context.get('key_points', [])
    sources = context.get('sources', [])
    
    return {
        "research_complete": True,
        "summary_length": len(research_summary.split()) if research_summary else 0,
        "key_points_count": len(key_points),
        "sources_count": len(sources),
        "research_quality": "comprehensive" if len(key_points) >= 5 else "basic"
    }


@dspy_worker("content_writer",
            signature="topic: str, research_data: str, target_audience: str, content_type: str -> content: str, title: str, outline: list[str]",
            reasoning="chain_of_thought",
            model="gemini/gemini-1.5-flash")
async def write_content_worker(context: dict) -> dict:
    """Write content based on research data and requirements."""
    content = context.get('content', '')
    title = context.get('title', '')
    outline = context.get('outline', [])
    
    return {
        "content_created": True,
        "title": title,
        "content_length": len(content.split()) if content else 0,
        "outline_sections": len(outline),
        "content_type": context.get('content_type', 'article'),
        "target_audience": context.get('target_audience', 'general')
    }


@dspy_worker("content_reviewer",
            signature="content: str, title: str, quality_criteria: str -> review_score: float, feedback: str, approved: bool, improvements: list[str]",
            tools=[fact_check, seo_optimize],
            reasoning="react",
            max_iters=4,
            model="gemini/gemini-1.5-flash")
async def review_content_worker(context: dict) -> dict:
    """Review content for quality, accuracy, and SEO optimization."""
    review_score = context.get('review_score', 0.0)
    feedback = context.get('feedback', '')
    approved = context.get('approved', False)
    improvements = context.get('improvements', [])
    
    return {
        "review_complete": True,
        "quality_score": review_score,
        "content_approved": approved,
        "feedback_provided": bool(feedback),
        "improvements_suggested": len(improvements),
        "review_criteria_met": review_score >= 0.8
    }


@dspy_worker("content_publisher",
            signature="content: str, title: str, metadata: dict -> publication_status: str, content_url: str, publication_date: str",
            tools=[save_content],
            reasoning="predict",
            model="gemini/gemini-1.5-flash")
async def publish_content_worker(context: dict) -> dict:
    """Publish approved content to the platform."""
    publication_status = context.get('publication_status', 'draft')
    content_url = context.get('content_url', '')
    publication_date = context.get('publication_date', '')
    
    return {
        "publication_complete": True,
        "status": publication_status,
        "url": content_url,
        "published_date": publication_date,
        "ready_for_distribution": publication_status == 'published'
    }


# =======================
# Content Creation Workflow
# =======================

async def create_content_creation_workflow():
    """Create a complete content creation workflow."""
    
    workflow = (WorkflowBuilder()
        .add_step("research", "topic_researcher")
        .add_step("write", "content_writer") 
        .add_step("review", "content_reviewer")
        .add_step("publish", "content_publisher")
        .set_initial_context({
            "topic": "The Future of Artificial Intelligence in Healthcare",
            "requirements": "Write a comprehensive article about AI in healthcare, focusing on current applications and future potential",
            "target_audience": "healthcare professionals and technology enthusiasts", 
            "content_type": "educational article",
            "quality_criteria": "accurate, well-researched, engaging, SEO-optimized"
        })
        .build()
    )
    
    return workflow


async def run_content_creation_demo():
    """Run the complete content creation workflow demo."""
    print("🚀 Real Content Creation Workflow with DSPy")
    print("=" * 60)
    
    try:
        # Configure DSPy
        configure_dspy()
        
        # Create event bus (in-memory for demo)
        print("\n📡 Setting up event infrastructure...")
        event_bus = RedisEventBus(host="localhost", port=6379, db=1)
        
        # Create orchestrator
        orchestrator = Orchestrator(event_bus)
        
        # Register workers
        print("👷 Registering workers...")
        await orchestrator.register_worker(research_topic_worker)
        await orchestrator.register_worker(write_content_worker)
        await orchestrator.register_worker(review_content_worker)
        await orchestrator.register_worker(publish_content_worker)
        
        # Create workflow
        print("📋 Creating content creation workflow...")
        workflow = await create_content_creation_workflow()
        
        # Execute workflow
        print("🎬 Starting content creation process...")
        print("-" * 40)
        
        result = await orchestrator.execute_workflow(workflow)
        
        print("\n✅ Workflow completed successfully!")
        print(f"Result: {result}")
        
        # Show workflow statistics
        print("\n📊 Workflow Statistics:")
        print(f"• Research completed: {result.get('research_complete', False)}")
        print(f"• Content created: {result.get('content_created', False)}")
        print(f"• Review completed: {result.get('review_complete', False)}")
        print(f"• Publication completed: {result.get('publication_complete', False)}")
        
        if result.get('content_length'):
            print(f"• Content length: {result['content_length']} words")
        if result.get('quality_score'):
            print(f"• Quality score: {result['quality_score']:.1%}")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if 'event_bus' in locals():
            await event_bus.disconnect()


async def run_simple_worker_demo():
    """Run a simple demo of individual workers without full workflow."""
    print("🧪 Simple Worker Demo (Individual Testing)")
    print("=" * 50)
    
    try:
        configure_dspy()
        
        # Test individual workers
        print("\n1. Testing Topic Researcher...")
        research_result = await research_topic_worker.execute({
            "topic": "artificial intelligence",
            "requirements": "basic research on AI applications"
        })
        print(f"Research result: {research_result}")
        
        print("\n2. Testing Content Writer...")
        write_result = await write_content_worker.execute({
            "topic": "AI in Healthcare",
            "research_data": "AI has many applications in healthcare including diagnosis, treatment planning, and drug discovery.",
            "target_audience": "healthcare professionals",
            "content_type": "article"
        })
        print(f"Writing result: {write_result}")
        
        print("\n✅ Individual worker testing completed!")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Worker testing failed: {e}")


if __name__ == "__main__":
    print("Real Content Creation Workflow with DSPy")
    print("Using actual Gemini LM and realistic tools")
    print("\nRequired: GOOGLE_API_KEY environment variable")
    print("Optional: Redis server for full workflow (will fallback to simple demo)")
    
    import sys
    
    # Check if user wants full workflow or simple demo
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        try:
            asyncio.run(run_simple_worker_demo())
        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted by user")
    else:
        try:
            asyncio.run(run_content_creation_demo())
        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted by user")
        except Exception as e:
            print(f"\n⚠️ Full workflow demo failed, trying simple demo...")
            print("💡 Run with --simple flag to skip workflow orchestration")
            try:
                asyncio.run(run_simple_worker_demo())
            except Exception as simple_e:
                print(f"❌ Simple demo also failed: {simple_e}")