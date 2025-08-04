"""
Test script to verify all tools work correctly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from tools.calculator import calculate, calculate_roi, calculate_compound_interest, calculate_statistics
from tools.web_search import web_search, search_for_context, get_market_data
from tools.data_analyzer import analyze_data, compare_data, generate_insights


def test_calculator():
    """Test calculator tool."""
    print("🧮 Testing Calculator Tool...")
    
    # Basic calculations
    result = calculate("2 + 2 * 3")
    print(f"  2 + 2 * 3 = {result}")
    assert result == "8", f"Expected 8, got {result}"
    
    # ROI calculation
    roi = calculate_roi(10000, 13000, 3)
    print(f"  ROI for $10k->$13k over 3 years: {roi['total_roi_percent']}%")
    assert roi['total_roi_percent'] == 30.0, f"Expected 30.0%, got {roi['total_roi_percent']}%"
    
    # Compound interest
    compound = calculate_compound_interest(1000, 5, 10)
    print(f"  $1000 at 5% for 10 years: ${compound['final_amount']}")
    
    # Statistics
    stats = calculate_statistics([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    print(f"  Stats for 1-10: mean={stats['mean']}, std_dev={stats['standard_deviation']}")
    
    print("  ✅ Calculator tests passed!")


def test_web_search():
    """Test web search tool."""
    print("🔍 Testing Web Search Tool...")
    
    # Search for renewable energy
    results = web_search("renewable energy stocks", max_results=3)
    print(f"  Found {len(results)} results for 'renewable energy stocks'")
    assert len(results) <= 3, f"Expected ≤3 results, got {len(results)}"
    assert results[0]['content'], "First result should have content"
    
    # Search with context
    context_results = search_for_context("solar investment", "renewable energy")
    print(f"  Context search returned {len(context_results)} results")
    
    # Market data
    market_data = get_market_data("TSLA")
    print(f"  TSLA market data: {market_data['price']}")
    assert market_data['symbol'] == "TSLA", f"Expected TSLA, got {market_data.get('symbol')}"
    
    print("  ✅ Web search tests passed!")


def test_data_analyzer():
    """Test data analyzer tool."""
    print("📊 Testing Data Analyzer Tool...")
    
    # Basic analysis
    test_data = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 100]  # Include outlier
    analysis = analyze_data(test_data, "test_dataset")
    print(f"  Analysis mean: {analysis['basic_stats']['mean']}")
    print(f"  Outliers detected: {analysis['outliers']['count']}")
    assert analysis['outliers']['count'] > 0, "Should detect outlier (100)"
    
    # Comparison
    data1 = [1, 2, 3, 4, 5]
    data2 = [6, 7, 8, 9, 10]
    comparison = compare_data(data1, data2, "Group A", "Group B")
    print(f"  Comparison mean difference: {comparison['differences']['mean_difference']}")
    assert comparison['differences']['mean_difference'] == 5.0, "Mean difference should be 5.0"
    
    # Insights
    insights = generate_insights(analysis)
    print(f"  Generated {len(insights)} insights")
    assert len(insights) > 0, "Should generate insights"
    
    print("  ✅ Data analyzer tests passed!")


def main():
    """Run all tool tests."""
    print("🧪 Testing Smart Research Assistant Tools\n")
    
    try:
        test_calculator()
        print()
        test_web_search()
        print()
        test_data_analyzer()
        
        print("\n✅ All tool tests PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Tool tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)