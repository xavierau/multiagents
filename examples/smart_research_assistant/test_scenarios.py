"""
Comprehensive Test Scenarios for Smart Research Assistant.

This script runs a variety of test scenarios to validate the multi-agent workflow,
covering different question types, complexity levels, and edge cases.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

import asyncio
from typing import Dict, Any, List, Tuple
from datetime import datetime
import json

from simple_workflow import run_research_query


class TestScenarios:
    """Comprehensive test scenarios for the research assistant."""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def define_test_scenarios(self) -> List[Dict[str, Any]]:
        """Define comprehensive test scenarios."""
        return [
            # Financial Analysis Scenarios
            {
                "category": "Financial Analysis",
                "name": "ROI Calculation",
                "question": "What's the ROI of investing $15,000 in renewable energy stocks for 7 years?",
                "expected_features": ["financial_analysis", "roi_calculation", "renewable_energy_research"],
                "timeout": 90
            },
            {
                "category": "Financial Analysis", 
                "name": "Compound Interest",
                "question": "Calculate compound interest on $8,000 at 6.5% annually for 4 years",
                "expected_features": ["calculation", "compound_interest", "financial_math"],
                "timeout": 60
            },
            {
                "category": "Financial Analysis",
                "name": "Investment Comparison",
                "question": "Compare the risk-return profile of Tesla vs Apple stock investments",
                "expected_features": ["comparative_analysis", "stock_research", "risk_analysis"],
                "timeout": 120
            },
            
            # Market Research Scenarios
            {
                "category": "Market Research",
                "name": "Trend Analysis",
                "question": "Analyze growth trends in electric vehicle market for 2024-2025",
                "expected_features": ["trend_analysis", "market_research", "ev_industry"],
                "timeout": 120
            },
            {
                "category": "Market Research",
                "name": "ESG Investments",
                "question": "What are the best ESG investment opportunities in technology sector?",
                "expected_features": ["esg_research", "tech_sector", "investment_opportunities"],
                "timeout": 120
            },
            
            # Mathematical Calculations
            {
                "category": "Calculations",
                "name": "Present Value",
                "question": "Calculate present value of $50,000 received in 8 years at 4% discount rate",
                "expected_features": ["present_value", "financial_calculation", "time_value_money"],
                "timeout": 60
            },
            {
                "category": "Calculations",
                "name": "Break-even Analysis",
                "question": "Calculate break-even point for business with $25,000 fixed costs and $15 variable cost per unit, selling at $35",
                "expected_features": ["break_even", "business_analysis", "cost_analysis"],
                "timeout": 60
            },
            
            # General Research
            {
                "category": "General Research",
                "name": "Technology Research",
                "question": "Research the latest developments in quantum computing applications",
                "expected_features": ["technology_research", "quantum_computing", "innovation_analysis"],
                "timeout": 120
            },
            {
                "category": "General Research",
                "name": "Environmental Impact",
                "question": "Analyze environmental impact of cryptocurrency mining operations",
                "expected_features": ["environmental_analysis", "cryptocurrency", "sustainability"],
                "timeout": 120
            },
            
            # Complex Multi-step Scenarios
            {
                "category": "Complex Analysis",
                "name": "Multi-factor Investment",
                "question": "Analyze a $20,000 investment in clean energy ETFs considering ESG factors, 10-year timeline, and tax implications",
                "expected_features": ["multi_factor_analysis", "etf_research", "tax_analysis", "esg_factors"],
                "timeout": 150
            },
            
            # Edge Cases
            {
                "category": "Edge Cases",
                "name": "Very Simple Question",
                "question": "What is 2+2?",
                "expected_features": ["basic_calculation"],
                "timeout": 30
            },
            {
                "category": "Edge Cases",
                "name": "Ambiguous Question",
                "question": "Tell me about investments",
                "expected_features": ["clarification_needed", "general_investment_info"],
                "timeout": 90
            },
            {
                "category": "Edge Cases",
                "name": "Calculation with Context",
                "question": "If I invest $1000 monthly in an index fund, how much will I have in 20 years assuming 7% annual return?",
                "expected_features": ["monthly_investment", "future_value", "index_funds"],
                "timeout": 90
            }
        ]
    
    async def run_test_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test scenario."""
        print(f"\n🧪 Testing: {scenario['name']} ({scenario['category']})")
        print(f"   Question: {scenario['question']}")
        print(f"   ⏱️  Timeout: {scenario['timeout']}s")
        
        start_time = datetime.now()
        
        try:
            # Run the research query with timeout
            result = await asyncio.wait_for(
                run_research_query(scenario['question'], f"test_{scenario['name'].lower().replace(' ', '_')}"),
                timeout=scenario['timeout']
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Analyze result
            test_result = await self.analyze_test_result(scenario, result, duration)
            test_result['status'] = 'PASSED' if test_result['success'] else 'FAILED'
            
            if test_result['success']:
                self.passed_tests += 1
                print(f"   ✅ PASSED ({duration:.1f}s)")
            else:
                self.failed_tests += 1
                print(f"   ❌ FAILED ({duration:.1f}s)")
                print(f"      Reason: {test_result.get('failure_reason', 'Unknown')}")
            
            # Show key metrics
            if 'response' in result:
                response = result['response']
                executive_summary = response.get('executive_summary', '')
                sections = len(response.get('response_sections', []))
                print(f"   📊 Sections: {sections}, Summary: {executive_summary[:50]}...")
            
            return test_result
            
        except asyncio.TimeoutError:
            self.failed_tests += 1
            print(f"   ⏰ TIMEOUT after {scenario['timeout']}s")
            return {
                'scenario': scenario,
                'status': 'TIMEOUT',
                'success': False,
                'failure_reason': f"Test exceeded {scenario['timeout']} second timeout",
                'duration': scenario['timeout']
            }
            
        except Exception as e:
            self.failed_tests += 1
            print(f"   💥 ERROR: {str(e)}")
            return {
                'scenario': scenario,
                'status': 'ERROR', 
                'success': False,
                'failure_reason': f"Exception: {str(e)}",
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def analyze_test_result(self, scenario: Dict[str, Any], result: Dict[str, Any], duration: float) -> Dict[str, Any]:
        """Analyze test result and determine if it passed."""
        test_result = {
            'scenario': scenario,
            'result': result,
            'duration': duration,
            'success': True,
            'checks_passed': [],
            'checks_failed': [],
            'failure_reason': None
        }
        
        # Basic checks
        if 'error' in result:
            test_result['success'] = False
            test_result['failure_reason'] = f"Workflow error: {result['error']}"
            test_result['checks_failed'].append('no_errors')
            return test_result
        
        test_result['checks_passed'].append('no_errors')
        
        # Check response structure
        if 'response' not in result:
            test_result['success'] = False
            test_result['failure_reason'] = "Missing response in result"
            test_result['checks_failed'].append('has_response')
            return test_result
        
        test_result['checks_passed'].append('has_response')
        
        response = result['response']
        
        # Check for required response components
        required_components = ['formatted_response', 'executive_summary']
        for component in required_components:
            if component not in response or not response[component]:
                test_result['checks_failed'].append(f'has_{component}')
            else:
                test_result['checks_passed'].append(f'has_{component}')
        
        # Check response quality
        formatted_response = response.get('formatted_response', '')
        if len(formatted_response) < 100:
            test_result['checks_failed'].append('response_length')
        else:
            test_result['checks_passed'].append('response_length')
        
        # Check for sections
        sections = response.get('response_sections', [])
        if len(sections) < 3:
            test_result['checks_failed'].append('has_sections')
        else:
            test_result['checks_passed'].append('has_sections')
        
        # Check metadata
        metadata = result.get('metadata', {})
        if metadata.get('processing_steps', 0) < 3:
            test_result['checks_failed'].append('processing_steps')
        else:
            test_result['checks_passed'].append('processing_steps')
        
        # Category-specific checks
        if scenario['category'] == 'Financial Analysis':
            if 'roi' in scenario['question'].lower() or 'return' in scenario['question'].lower():
                if 'ROI' not in formatted_response and 'return' not in formatted_response.lower():
                    test_result['checks_failed'].append('financial_content')
                else:
                    test_result['checks_passed'].append('financial_content')
        
        elif scenario['category'] == 'Calculations':
            # Check if analysis was performed
            if not metadata.get('had_analysis', False):
                test_result['checks_failed'].append('had_analysis')
            else:
                test_result['checks_passed'].append('had_analysis')
        
        # Determine overall success
        if test_result['checks_failed']:
            test_result['success'] = False
            test_result['failure_reason'] = f"Failed checks: {', '.join(test_result['checks_failed'])}"
        
        return test_result
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n" + "="*80)
        print(f"🧪 TEST SUMMARY")
        print(f"="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        # Category breakdown
        category_stats = {}
        for result in self.test_results:
            category = result['scenario']['category']
            if category not in category_stats:
                category_stats[category] = {'passed': 0, 'failed': 0}
            
            if result['success']:
                category_stats[category]['passed'] += 1
            else:
                category_stats[category]['failed'] += 1
        
        print(f"\n📊 Results by Category:")
        print("-" * 50)
        for category, stats in category_stats.items():
            total = stats['passed'] + stats['failed']
            rate = (stats['passed'] / total * 100) if total > 0 else 0
            print(f"{category:20s} {stats['passed']:2d}/{total:2d} ({rate:5.1f}%)")
        
        # Failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print(f"\n❌ Failed Tests Details:")
            print("-" * 50)
            for result in failed_results:
                scenario = result['scenario']
                print(f"• {scenario['name']} ({scenario['category']})")
                print(f"  Reason: {result.get('failure_reason', 'Unknown')}")
                if 'checks_failed' in result:
                    print(f"  Failed Checks: {', '.join(result['checks_failed'])}")
        
        # Performance stats
        durations = [r['duration'] for r in self.test_results if 'duration' in r]
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            print(f"\n⏱️  Performance Stats:")
            print("-" * 30)
            print(f"Average Duration: {avg_duration:.1f}s")
            print(f"Fastest Test: {min_duration:.1f}s")
            print(f"Slowest Test: {max_duration:.1f}s")
        
        print(f"\n{'='*80}")
    
    async def run_all_tests(self, max_concurrent: int = 3):
        """Run all test scenarios with controlled concurrency."""
        scenarios = self.define_test_scenarios()
        
        print(f"🚀 Starting Smart Research Assistant Test Suite")
        print(f"📋 Total Scenarios: {len(scenarios)}")
        print(f"🔄 Max Concurrent: {max_concurrent}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Run tests in batches to control concurrency
        for i in range(0, len(scenarios), max_concurrent):
            batch_scenarios = scenarios[i:i + max_concurrent]
            
            print(f"\n🔄 Running batch {i//max_concurrent + 1}/{(len(scenarios)-1)//max_concurrent + 1}")
            
            # Run batch concurrently
            tasks = [self.run_test_scenario(scenario) for scenario in batch_scenarios]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Handle exceptions
                    self.failed_tests += 1
                    error_result = {
                        'scenario': batch_scenarios[j],
                        'status': 'EXCEPTION',
                        'success': False,
                        'failure_reason': f"Test exception: {str(result)}",
                        'duration': 0
                    }
                    self.test_results.append(error_result)
                else:
                    self.test_results.append(result)
            
            # Brief pause between batches
            if i + max_concurrent < len(scenarios):
                print(f"   ⏸️  Pausing 5s before next batch...")
                await asyncio.sleep(5)
        
        self.print_test_summary()
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file."""
        if filename is None:
            filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results_data = {
            'test_summary': {
                'total_tests': self.passed_tests + self.failed_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.failed_tests,
                'pass_rate': (self.passed_tests / (self.passed_tests + self.failed_tests) * 100) if (self.passed_tests + self.failed_tests) > 0 else 0,
                'timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        print(f"\n💾 Test results saved to: {filename}")


async def run_quick_test():
    """Run a quick subset of tests for faster validation."""
    quick_scenarios = [
        {
            "category": "Financial Analysis",
            "name": "Quick ROI",
            "question": "What's the ROI of investing $5,000 in tech stocks for 3 years?",
            "expected_features": ["financial_analysis", "roi_calculation"],
            "timeout": 60
        },
        {
            "category": "Calculations",
            "name": "Quick Calculation",
            "question": "Calculate 15% of $10,000",
            "expected_features": ["basic_calculation"],
            "timeout": 30
        },
        {
            "category": "General Research", 
            "name": "Quick Research",
            "question": "What are renewable energy trends?",
            "expected_features": ["trend_analysis"],
            "timeout": 60
        }
    ]
    
    print("🏃‍♂️ Running Quick Test Suite (3 scenarios)")
    print("="*50)
    
    test_runner = TestScenarios()
    
    for scenario in quick_scenarios:
        result = await test_runner.run_test_scenario(scenario)
        test_runner.test_results.append(result)
    
    test_runner.print_test_summary()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Research Assistant Test Suite")
    parser.add_argument("--quick", action="store_true", help="Run quick test suite (3 tests)")
    parser.add_argument("--concurrent", type=int, default=2, help="Max concurrent tests (default: 2)")
    parser.add_argument("--save", action="store_true", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    async def main():
        if args.quick:
            await run_quick_test()
        else:
            test_runner = TestScenarios()
            await test_runner.run_all_tests(max_concurrent=args.concurrent)
            
            if args.save:
                test_runner.save_results()
    
    asyncio.run(main())