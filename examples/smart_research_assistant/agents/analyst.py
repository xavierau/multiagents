"""
Analyst Agent - Performs mathematical calculations and data analysis.

This agent specializes in:
1. Financial calculations (ROI, compound interest, etc.)
2. Statistical analysis of data
3. Mathematical operations and modeling
4. Insights generation from quantitative data
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from typing import Dict, Any, List, Optional
import json
import asyncio
import re

from multiagents.worker_sdk import dspy_worker
from config.gemini_config import get_analyst_config
from tools.calculator import (
    calculate, calculate_roi, calculate_compound_interest, calculate_statistics
)
from tools.data_analyzer import analyze_data, compare_data, generate_insights


@dspy_worker(
    "analyze_financial_data",
    signature="financial_query, data_inputs, calculation_requirements -> analysis_results, calculations, insights",
    timeout=60,
    retry_attempts=2,
    model=get_analyst_config().model
)
async def analyze_financial_data_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyst Agent for financial analysis and calculations.
    
    This agent performs comprehensive financial analysis including:
    - ROI calculations
    - Investment projections
    - Risk analysis
    - Comparative analysis between investment options
    """
    financial_query = context.get("financial_query", context.get("user_question", ""))
    data_inputs = context.get("data_inputs", {})
    calculation_requirements = context.get("calculation_requirements", {})
    
    # Extract calculation parameters from query
    calc_params = _extract_calculation_parameters(financial_query, data_inputs)
    
    # Perform various financial calculations
    calculations = await _perform_financial_calculations(calc_params)
    
    # Generate analysis insights
    analysis_insights = _generate_financial_insights(calculations, financial_query)
    
    # Calculate confidence and accuracy metrics
    analysis_metadata = _calculate_analysis_metadata(calculations)
    
    return {
        "analysis_results": json.dumps(analysis_insights),
        "calculations": json.dumps(calculations),
        "insights": json.dumps(analysis_insights.get("key_insights", [])),
        "financial_summary": analysis_insights.get("summary", ""),
        "calculation_accuracy": analysis_metadata.get("accuracy_level", "medium"),
        "analysis_confidence": analysis_metadata.get("confidence_level", "medium"),
        "calculation_metadata": {
            "calculations_performed": len(calculations),
            "data_sources_used": len(data_inputs) if data_inputs else 0,
            "analysis_type": _determine_analysis_type(financial_query)
        }
    }


@dspy_worker(
    "analyze_statistical_data",
    signature="data_query, dataset, analysis_type -> statistical_results, insights, recommendations",
    timeout=60,
    retry_attempts=2,
    model=get_analyst_config().model
)
async def analyze_statistical_data_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyst Agent for statistical data analysis.
    
    This agent performs comprehensive statistical analysis including:
    - Descriptive statistics
    - Trend analysis
    - Comparative analysis
    - Data quality assessment
    """
    data_query = context.get("data_query", context.get("user_question", ""))
    dataset = context.get("dataset", [])
    analysis_type = context.get("analysis_type", "comprehensive")
    
    # Process and validate dataset
    processed_data = _process_dataset(dataset, data_query)
    
    # Perform statistical analysis
    statistical_results = await _perform_statistical_analysis(processed_data, analysis_type)
    
    # Generate insights and recommendations
    insights = _generate_statistical_insights(statistical_results, data_query)
    recommendations = _generate_statistical_recommendations(statistical_results, insights)
    
    return {
        "statistical_results": json.dumps(statistical_results),
        "insights": json.dumps(insights),
        "recommendations": json.dumps(recommendations),
        "data_summary": statistical_results.get("basic_stats", {}),
        "trend_analysis": statistical_results.get("trend_analysis", {}),
        "data_quality_score": statistical_results.get("data_quality", "unknown"),
        "analysis_metadata": {
            "dataset_size": len(processed_data),
            "analysis_type": analysis_type,
            "outliers_detected": statistical_results.get("outliers", {}).get("count", 0),
            "statistical_significance": _assess_statistical_significance(statistical_results)
        }
    }


@dspy_worker(
    "perform_calculations",
    signature="calculation_request, parameters -> calculation_results, explanations",
    timeout=30,
    retry_attempts=2,
    model=get_analyst_config().model
)
async def perform_calculations_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyst Agent for general mathematical calculations.
    
    This agent handles various mathematical operations including:
    - Basic arithmetic
    - Complex mathematical expressions
    - Unit conversions
    - Mathematical modeling
    """
    calculation_request = context.get("calculation_request", context.get("user_question", ""))
    parameters = context.get("parameters", {})
    
    # Parse calculation requirements
    calc_requirements = _parse_calculation_requirements(calculation_request)
    
    # Perform calculations
    calculation_results = await _execute_calculations(calc_requirements, parameters)
    
    # Generate explanations
    explanations = _generate_calculation_explanations(calculation_results, calc_requirements)
    
    return {
        "calculation_results": json.dumps(calculation_results),
        "explanations": json.dumps(explanations),
        "primary_result": calculation_results.get("primary_result", ""),
        "calculation_steps": calculation_results.get("steps", []),
        "accuracy_level": calculation_results.get("accuracy", "high"),
        "calculation_metadata": {
            "operations_performed": len(calculation_results.get("operations", [])),
            "complexity_level": calc_requirements.get("complexity", "medium"),
            "calculation_type": calc_requirements.get("type", "general")
        }
    }


def _extract_calculation_parameters(query: str, data_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract calculation parameters from query and data inputs."""
    params = {
        "investment_amount": None,
        "timeframe_years": None,
        "expected_return": None,
        "risk_level": "medium",
        "calculation_type": "roi"
    }
    
    query_lower = query.lower()
    
    # Extract investment amount
    amount_matches = re.findall(r'[\$€£]?(\d+(?:,\d{3})*(?:\.\d{2})?)', query)
    if amount_matches:
        # Take the first number that looks like an investment amount
        amount_str = amount_matches[0].replace(',', '')
        try:
            params["investment_amount"] = float(amount_str)
        except ValueError:
            pass
    
    # Extract timeframe
    year_matches = re.findall(r'(\d+)\s*year', query_lower)
    if year_matches:
        try:
            params["timeframe_years"] = int(year_matches[0])
        except ValueError:
            pass
    
    # Extract return percentage
    return_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', query)
    if return_matches:
        try:
            params["expected_return"] = float(return_matches[0])
        except ValueError:
            pass
    
    # Override with data inputs if provided
    if data_inputs and isinstance(data_inputs, dict):
        params.update(data_inputs)
    
    # Set defaults based on context
    if not params["investment_amount"]:
        params["investment_amount"] = 10000  # Default $10k
    
    if not params["timeframe_years"]:
        params["timeframe_years"] = 5  # Default 5 years
    
    if not params["expected_return"]:
        if "renewable" in query_lower or "solar" in query_lower:
            params["expected_return"] = 8.5  # Historical renewable energy returns
        else:
            params["expected_return"] = 7.0  # Market average
    
    return params


async def _perform_financial_calculations(params: Dict[str, Any]) -> Dict[str, Any]:
    """Perform comprehensive financial calculations."""
    calculations = {}
    
    investment_amount = params.get("investment_amount", 10000)
    years = params.get("timeframe_years", 5)
    annual_return = params.get("expected_return", 7.0) / 100  # Convert to decimal
    
    # ROI calculation
    if investment_amount and years and annual_return:
        final_value = investment_amount * ((1 + annual_return) ** years)
        roi_result = calculate_roi(investment_amount, final_value, years)
        calculations["roi_analysis"] = roi_result
    
    # Compound interest calculation
    compound_result = calculate_compound_interest(
        investment_amount, 
        params.get("expected_return", 7.0), 
        years
    )
    calculations["compound_interest"] = compound_result
    
    # Risk-adjusted calculations
    risk_multiplier = {
        "low": 0.8,
        "medium": 1.0,
        "high": 1.3
    }.get(params.get("risk_level", "medium"), 1.0)
    
    adjusted_return = annual_return * risk_multiplier
    conservative_final = investment_amount * ((1 + adjusted_return * 0.7) ** years)
    optimistic_final = investment_amount * ((1 + adjusted_return * 1.3) ** years)
    
    calculations["risk_scenarios"] = {
        "conservative": calculate_roi(investment_amount, conservative_final, years),
        "optimistic": calculate_roi(investment_amount, optimistic_final, years)
    }
    
    # Inflation adjustment (assuming 3% inflation)
    inflation_rate = 0.03
    real_return = annual_return - inflation_rate
    inflation_adjusted_final = investment_amount * ((1 + real_return) ** years)
    calculations["inflation_adjusted"] = calculate_roi(investment_amount, inflation_adjusted_final, years)
    
    return calculations


def _generate_financial_insights(calculations: Dict[str, Any], query: str) -> Dict[str, Any]:
    """Generate insights from financial calculations."""
    insights = {
        "summary": "",
        "key_insights": [],
        "risk_assessment": "",
        "recommendations": []
    }
    
    roi_analysis = calculations.get("roi_analysis", {})
    compound_interest = calculations.get("compound_interest", {})
    risk_scenarios = calculations.get("risk_scenarios", {})
    
    # Summary
    if roi_analysis and not roi_analysis.get("error"):
        total_roi = roi_analysis.get("total_roi_percent", 0)
        annualized = roi_analysis.get("annualized_return_percent", 0)
        insights["summary"] = f"Investment shows {total_roi}% total return ({annualized}% annually)"
    
    # Key insights
    if compound_interest and not compound_interest.get("error"):
        interest_earned = compound_interest.get("interest_earned", 0)
        insights["key_insights"].append(f"Compound interest effect: ${interest_earned:,.2f} earned")
    
    if risk_scenarios:
        conservative = risk_scenarios.get("conservative", {})
        optimistic = risk_scenarios.get("optimistic", {})
        if conservative and optimistic:
            insights["key_insights"].append(
                f"Risk range: {conservative.get('total_roi_percent', 0):.1f}% to "
                f"{optimistic.get('total_roi_percent', 0):.1f}% total return"
            )
    
    # Risk assessment
    if roi_analysis:
        annual_return = roi_analysis.get("annualized_return_percent", 0)
        if annual_return > 12:
            insights["risk_assessment"] = "High return potential with elevated risk"
        elif annual_return > 8:
            insights["risk_assessment"] = "Moderate return with balanced risk"
        else:
            insights["risk_assessment"] = "Conservative return with lower risk"
    
    # Recommendations
    if roi_analysis:
        total_roi = roi_analysis.get("total_roi_percent", 0)
        if total_roi > 50:
            insights["recommendations"].append("Consider taking profits periodically")
        if total_roi > 0:
            insights["recommendations"].append("Monitor market conditions regularly")
        insights["recommendations"].append("Diversify across multiple investments")
    
    return insights


def _calculate_analysis_metadata(calculations: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate metadata about the analysis quality."""
    metadata = {
        "accuracy_level": "medium",
        "confidence_level": "medium",
        "completeness_score": 0
    }
    
    # Count successful calculations
    successful_calcs = 0
    total_calcs = len(calculations)
    
    for calc_name, calc_result in calculations.items():
        if isinstance(calc_result, dict) and not calc_result.get("error"):
            successful_calcs += 1
    
    if total_calcs > 0:
        success_rate = successful_calcs / total_calcs
        metadata["completeness_score"] = success_rate
        
        if success_rate >= 0.9:
            metadata["accuracy_level"] = "high"
            metadata["confidence_level"] = "high"
        elif success_rate >= 0.7:
            metadata["accuracy_level"] = "medium"
            metadata["confidence_level"] = "medium"
        else:
            metadata["accuracy_level"] = "low"
            metadata["confidence_level"] = "low"
    
    return metadata


def _determine_analysis_type(query: str) -> str:
    """Determine the type of analysis based on the query."""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["roi", "return", "investment"]):
        return "roi_analysis"
    elif any(word in query_lower for word in ["compound", "interest", "growth"]):
        return "compound_interest"
    elif any(word in query_lower for word in ["risk", "volatile", "safe"]):
        return "risk_analysis"
    elif any(word in query_lower for word in ["compare", "versus", "vs"]):
        return "comparative_analysis"
    else:
        return "general_financial"


def _process_dataset(dataset: List, query: str) -> List[float]:
    """Process and validate numerical dataset."""
    processed_data = []
    
    for item in dataset:
        if isinstance(item, (int, float)):
            processed_data.append(float(item))
        elif isinstance(item, str):
            # Try to extract numbers from strings
            try:
                # Remove common currency symbols and formatting
                cleaned = re.sub(r'[$,€£%]', '', item)
                processed_data.append(float(cleaned))
            except ValueError:
                continue
    
    # If no data provided, generate sample data based on query context
    if not processed_data:
        processed_data = _generate_sample_data(query)
    
    return processed_data


def _generate_sample_data(query: str) -> List[float]:
    """Generate sample data for demonstration purposes."""
    query_lower = query.lower()
    
    if "stock" in query_lower or "return" in query_lower:
        # Generate sample stock return data (monthly returns %)
        return [2.1, -1.5, 3.2, 0.8, -2.1, 4.3, 1.7, -0.9, 2.8, 1.2, 3.5, -1.8]
    elif "price" in query_lower or "cost" in query_lower:
        # Generate sample price data
        return [45.2, 47.1, 43.8, 49.2, 52.3, 48.7, 51.1, 53.4, 49.8, 46.2]
    else:
        # Generic sample data
        return [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]


async def _perform_statistical_analysis(data: List[float], analysis_type: str) -> Dict[str, Any]:
    """Perform comprehensive statistical analysis."""
    if not data:
        return {"error": "No data provided for analysis"}
    
    # Basic analysis
    analysis_result = analyze_data(data, "user_dataset")
    
    # Add trend analysis for time series data
    if len(data) > 2:
        trend_data = _calculate_trend_metrics(data)
        analysis_result["trend_analysis"] = trend_data
    
    # Add volatility analysis for financial data
    if analysis_type in ["financial", "stock", "investment"]:
        volatility_data = _calculate_volatility_metrics(data)
        analysis_result["volatility_analysis"] = volatility_data
    
    return analysis_result


def _calculate_trend_metrics(data: List[float]) -> Dict[str, Any]:
    """Calculate trend metrics for time series data."""
    if len(data) < 2:
        return {"trend": "insufficient_data"}
    
    # Simple trend calculation
    first_half = data[:len(data)//2]
    second_half = data[len(data)//2:]
    
    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)
    
    trend_change = ((second_avg - first_avg) / first_avg) * 100
    
    return {
        "trend_direction": "increasing" if trend_change > 2 else "decreasing" if trend_change < -2 else "stable",
        "trend_magnitude": abs(trend_change),
        "period_change_percent": round(trend_change, 2),
        "first_period_avg": round(first_avg, 2),
        "second_period_avg": round(second_avg, 2)
    }


def _calculate_volatility_metrics(data: List[float]) -> Dict[str, Any]:
    """Calculate volatility metrics for financial data."""
    if len(data) < 2:
        return {"volatility": "insufficient_data"}
    
    mean_val = sum(data) / len(data)
    variance = sum((x - mean_val) ** 2 for x in data) / len(data)
    volatility = (variance ** 0.5) / mean_val * 100 if mean_val != 0 else 0
    
    # Calculate maximum drawdown
    peak = data[0]
    max_drawdown = 0
    
    for value in data:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak if peak != 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
    
    return {
        "volatility_percent": round(volatility, 2),
        "max_drawdown_percent": round(max_drawdown * 100, 2),
        "volatility_level": "high" if volatility > 20 else "medium" if volatility > 10 else "low"
    }


def _generate_statistical_insights(results: Dict[str, Any], query: str) -> List[str]:
    """Generate insights from statistical analysis."""
    return generate_insights(results)


def _generate_statistical_recommendations(results: Dict[str, Any], insights: List[str]) -> List[str]:
    """Generate recommendations based on statistical analysis."""
    recommendations = []
    
    # Check for outliers
    outliers = results.get("outliers", {})
    if outliers.get("count", 0) > 0:
        recommendations.append("Investigate outliers for data quality issues")
    
    # Check distribution
    distribution = results.get("distribution", {})
    skewness_interp = distribution.get("skewness_interpretation", "")
    if "skewed" in skewness_interp:
        recommendations.append("Consider data transformation for skewed distribution")
    
    # Check trend
    trend = results.get("trend_analysis", {})
    if trend.get("trend_direction") == "increasing":
        recommendations.append("Monitor continued growth trajectory")
    elif trend.get("trend_direction") == "decreasing":
        recommendations.append("Investigate factors causing decline")
    
    # Check volatility
    volatility = results.get("volatility_analysis", {})
    if volatility.get("volatility_level") == "high":
        recommendations.append("High volatility detected - consider risk management")
    
    return recommendations[:3]  # Limit to top 3


def _assess_statistical_significance(results: Dict[str, Any]) -> str:
    """Assess statistical significance of results."""
    basic_stats = results.get("basic_stats", {})
    count = basic_stats.get("count", 0)
    
    if count >= 30:
        return "high"
    elif count >= 10:
        return "medium"
    else:
        return "low"


def _parse_calculation_requirements(request: str) -> Dict[str, Any]:
    """Parse calculation requirements from request."""
    request_lower = request.lower()
    
    requirements = {
        "type": "general",
        "complexity": "medium",
        "expressions": [],
        "operations": []
    }
    
    # Detect calculation type
    if any(word in request_lower for word in ["add", "sum", "plus", "+"]):
        requirements["type"] = "arithmetic"
        requirements["operations"].append("addition")
    
    if any(word in request_lower for word in ["multiply", "times", "*"]):
        requirements["operations"].append("multiplication")
    
    if any(word in request_lower for word in ["divide", "divided", "/"]):
        requirements["operations"].append("division")
    
    # Extract mathematical expressions
    # Look for expressions with numbers and operators
    expressions = re.findall(r'[\d\+\-\*/\(\)\.\s]+', request)
    requirements["expressions"] = [expr.strip() for expr in expressions if len(expr.strip()) > 3]
    
    # Determine complexity
    if len(requirements["expressions"]) > 2 or any(op in request for op in ["sqrt", "log", "exp", "sin", "cos"]):
        requirements["complexity"] = "high"
    elif len(requirements["expressions"]) > 1:
        requirements["complexity"] = "medium"
    else:
        requirements["complexity"] = "low"
    
    return requirements


async def _execute_calculations(requirements: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute calculations based on requirements."""
    results = {
        "operations": [],
        "primary_result": "",
        "steps": [],
        "accuracy": "high"
    }
    
    expressions = requirements.get("expressions", [])
    
    if expressions:
        for i, expr in enumerate(expressions):
            try:
                result = calculate(expr)
                operation = {
                    "expression": expr,
                    "result": result,
                    "step": i + 1
                }
                results["operations"].append(operation)
                results["steps"].append(f"Step {i + 1}: {expr} = {result}")
                
                if i == 0:  # First result is primary
                    results["primary_result"] = result
                    
            except Exception as e:
                results["operations"].append({
                    "expression": expr,
                    "error": str(e),
                    "step": i + 1
                })
                results["accuracy"] = "medium"
    
    # If no expressions found, try to extract numbers and perform basic operations
    if not results["operations"]:
        # Extract all numbers from the request
        numbers = re.findall(r'\d+(?:\.\d+)?', str(parameters))
        if len(numbers) >= 2:
            num1, num2 = float(numbers[0]), float(numbers[1])
            
            # Perform basic operations
            basic_ops = {
                "addition": num1 + num2,
                "subtraction": num1 - num2,
                "multiplication": num1 * num2,
                "division": num1 / num2 if num2 != 0 else "undefined"
            }
            
            for op_name, result in basic_ops.items():
                results["operations"].append({
                    "operation": op_name,
                    "operands": [num1, num2],
                    "result": result
                })
            
            results["primary_result"] = str(basic_ops["addition"])
    
    return results


def _generate_calculation_explanations(results: Dict[str, Any], requirements: Dict[str, Any]) -> List[str]:
    """Generate explanations for calculations performed."""
    explanations = []
    
    operations = results.get("operations", [])
    complexity = requirements.get("complexity", "medium")
    
    if operations:
        explanations.append(f"Performed {len(operations)} mathematical operations")
        
        if complexity == "high":
            explanations.append("Complex mathematical functions were evaluated")
        elif complexity == "medium":
            explanations.append("Standard arithmetic operations were performed")
        else:
            explanations.append("Basic calculations were completed")
    
    accuracy = results.get("accuracy", "high")
    if accuracy == "high":
        explanations.append("All calculations completed successfully with high precision")
    elif accuracy == "medium":
        explanations.append("Most calculations completed, some minor issues encountered")
    else:
        explanations.append("Calculations completed with limited precision")
    
    return explanations