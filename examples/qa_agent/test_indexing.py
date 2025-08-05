"""
Test the codebase indexing system without requiring API keys
"""
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dspy_workers import get_codebase_indexer


def test_codebase_indexing():
    """Test the codebase indexing functionality."""
    
    print("🚀 Testing Codebase Indexing System")
    print("=" * 50)
    
    # Get the indexer
    print("🔍 Initializing codebase indexer...")
    indexer = get_codebase_indexer()
    
    print(f"✅ Successfully indexed {len(indexer.index)} entities from the codebase")
    print()
    
    # Test different search queries
    test_queries = [
        "worker decorator",
        "WorkflowBuilder", 
        "orchestrator",
        "event bus",
        "dspy_worker",
        "monitoring"
    ]
    
    for query in test_queries:
        print(f"🔍 Searching for: '{query}'")
        results = indexer.search(query, max_results=5)
        
        if results:
            print(f"   Found {len(results)} relevant results:")
            for i, result in enumerate(results[:3], 1):
                item = result["item"]
                print(f"   {i}. **{item['name']}** ({item['file']}) - Score: {result['score']}")
                if "docstring" in item and item["docstring"]:
                    doc_preview = item["docstring"][:100].replace('\n', ' ')
                    print(f"      └─ {doc_preview}...")
                print()
        else:
            print("   No results found")
            print()
    
    # Show some statistics
    entity_types = {}
    for item in indexer.index.values():
        entity_type = item.get("type", "unknown")
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    print("📊 Indexing Statistics:")
    for entity_type, count in sorted(entity_types.items()):
        print(f"   - {entity_type.title()}: {count}")
    
    print(f"\n🎯 The indexer can search through {len(indexer.index)} code entities")
    print("   including functions, classes, files, and documentation!")


def show_sample_entities():
    """Show some sample indexed entities."""
    print("\n" + "=" * 50)
    print("📋 Sample Indexed Entities")
    print("=" * 50)
    
    indexer = get_codebase_indexer()
    
    # Show samples by type
    samples_by_type = {}
    for key, item in indexer.index.items():
        entity_type = item.get("type", "unknown")
        if entity_type not in samples_by_type:
            samples_by_type[entity_type] = []
        if len(samples_by_type[entity_type]) < 3:
            samples_by_type[entity_type].append((key, item))
    
    for entity_type, samples in samples_by_type.items():
        print(f"\n🔹 {entity_type.title()} Examples:")
        for key, item in samples:
            print(f"   • {item['name']} - {item['file']}")
            if "docstring" in item and item["docstring"]:
                doc_preview = item["docstring"][:80].replace('\n', ' ').strip()
                if doc_preview:
                    print(f"     └─ {doc_preview}...")


if __name__ == "__main__":
    try:
        test_codebase_indexing()
        show_sample_entities()
        
        print("\n🎉 Codebase indexing test completed successfully!")
        print("💡 This system can answer questions about the MultiAgents framework")
        print("   by searching through all Python files, classes, functions, and docs!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()