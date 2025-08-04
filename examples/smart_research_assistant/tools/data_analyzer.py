"""
Data analysis tools for statistical analysis and insights generation.
"""
from typing import List, Dict, Any, Tuple, Optional
import math
import statistics
from collections import Counter


class DataAnalyzer:
    """Comprehensive data analysis toolkit."""
    
    @staticmethod
    def analyze_numerical_data(data: List[float], data_name: str = "dataset") -> Dict[str, Any]:
        """
        Perform comprehensive analysis on numerical data.
        
        Args:
            data: List of numerical values
            data_name: Name/description of the dataset
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        if not data:
            return {"error": "Empty dataset provided"}
        
        try:
            n = len(data)
            
            # Basic statistics
            mean = statistics.mean(data)
            median = statistics.median(data)
            
            # Standard deviation and variance
            if n > 1:
                stdev = statistics.stdev(data)
                variance = statistics.variance(data)
            else:
                stdev = 0
                variance = 0
            
            # Range and quartiles
            sorted_data = sorted(data)
            q1 = DataAnalyzer._percentile(sorted_data, 25)
            q3 = DataAnalyzer._percentile(sorted_data, 75)
            iqr = q3 - q1
            
            # Outlier detection (using IQR method)
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = [x for x in data if x < lower_bound or x > upper_bound]
            
            # Distribution characteristics
            skewness = DataAnalyzer._calculate_skewness(data, mean, stdev)
            kurtosis = DataAnalyzer._calculate_kurtosis(data, mean, stdev)
            
            # Trend analysis (if data represents time series)
            trend = DataAnalyzer._analyze_trend(data)
            
            return {
                "dataset_name": data_name,
                "basic_stats": {
                    "count": n,
                    "mean": round(mean, 4),
                    "median": round(median, 4),
                    "mode": DataAnalyzer._calculate_mode(data),
                    "min": min(data),
                    "max": max(data),
                    "range": round(max(data) - min(data), 4)
                },
                "variability": {
                    "variance": round(variance, 4),
                    "standard_deviation": round(stdev, 4),
                    "coefficient_of_variation": round((stdev / mean) * 100, 2) if mean != 0 else None
                },
                "quartiles": {
                    "q1": round(q1, 4),
                    "q2_median": round(median, 4),
                    "q3": round(q3, 4),
                    "iqr": round(iqr, 4)
                },
                "outliers": {
                    "count": len(outliers),
                    "values": [round(x, 4) for x in outliers],
                    "percentage": round((len(outliers) / n) * 100, 2)
                },
                "distribution": {
                    "skewness": round(skewness, 4),
                    "skewness_interpretation": DataAnalyzer._interpret_skewness(skewness),
                    "kurtosis": round(kurtosis, 4),
                    "kurtosis_interpretation": DataAnalyzer._interpret_kurtosis(kurtosis)
                },
                "trend_analysis": trend
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}
    
    @staticmethod
    def _percentile(sorted_data: List[float], percentile: float) -> float:
        """Calculate percentile of sorted data."""
        if not sorted_data:
            return 0
        
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower_index = int(math.floor(index))
        upper_index = int(math.ceil(index))
        
        if lower_index == upper_index:
            return sorted_data[lower_index]
        
        # Linear interpolation
        weight = index - lower_index
        return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    @staticmethod
    def _calculate_mode(data: List[float]) -> Optional[float]:
        """Calculate mode of the data."""
        if not data:
            return None
        
        # Round to avoid floating point precision issues
        rounded_data = [round(x, 6) for x in data]
        counter = Counter(rounded_data)
        max_count = max(counter.values())
        
        # Return mode only if it appears more than once
        if max_count > 1:
            modes = [value for value, count in counter.items() if count == max_count]
            return modes[0] if len(modes) == 1 else None  # Return None for multimodal
        
        return None  # No mode if all values appear once
    
    @staticmethod
    def _calculate_skewness(data: List[float], mean: float, stdev: float) -> float:
        """Calculate skewness using the third moment."""
        if stdev == 0 or len(data) < 3:
            return 0
        
        n = len(data)
        skew_sum = sum(((x - mean) / stdev) ** 3 for x in data)
        return (n / ((n - 1) * (n - 2))) * skew_sum
    
    @staticmethod
    def _calculate_kurtosis(data: List[float], mean: float, stdev: float) -> float:
        """Calculate excess kurtosis using the fourth moment."""
        if stdev == 0 or len(data) < 4:
            return 0
        
        n = len(data)
        kurt_sum = sum(((x - mean) / stdev) ** 4 for x in data)
        return ((n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))) * kurt_sum - (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))
    
    @staticmethod
    def _interpret_skewness(skewness: float) -> str:
        """Interpret skewness value."""
        if abs(skewness) < 0.5:
            return "Approximately symmetric"
        elif skewness > 0.5:
            return "Right-skewed (positive skew)"
        else:
            return "Left-skewed (negative skew)"
    
    @staticmethod
    def _interpret_kurtosis(kurtosis: float) -> str:
        """Interpret kurtosis value."""
        if abs(kurtosis) < 0.5:
            return "Mesokurtic (normal-like)"
        elif kurtosis > 0.5:
            return "Leptokurtic (heavy-tailed)"
        else:
            return "Platykurtic (light-tailed)"
    
    @staticmethod
    def _analyze_trend(data: List[float]) -> Dict[str, Any]:
        """Analyze trend in the data."""
        if len(data) < 2:
            return {"trend": "insufficient_data"}
        
        # Simple linear trend analysis
        n = len(data)
        x_values = list(range(n))
        
        # Calculate correlation coefficient
        mean_x = statistics.mean(x_values)
        mean_y = statistics.mean(data)
        
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, data))
        
        sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
        sum_sq_y = sum((y - mean_y) ** 2 for y in data)
        
        if sum_sq_x == 0 or sum_sq_y == 0:
            correlation = 0
        else:
            correlation = numerator / math.sqrt(sum_sq_x * sum_sq_y)
        
        # Calculate slope
        if sum_sq_x != 0:
            slope = numerator / sum_sq_x
        else:
            slope = 0
        
        # Interpret trend
        if abs(correlation) < 0.3:
            trend_direction = "no clear trend"
        elif correlation > 0.3:
            trend_direction = "increasing trend"
        else:
            trend_direction = "decreasing trend"
        
        return {
            "trend": trend_direction,
            "correlation_coefficient": round(correlation, 4),
            "slope": round(slope, 4),
            "trend_strength": "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.3 else "weak"
        }
    
    @staticmethod
    def compare_datasets(dataset1: List[float], dataset2: List[float], 
                        name1: str = "Dataset 1", name2: str = "Dataset 2") -> Dict[str, Any]:
        """
        Compare two datasets statistically.
        
        Args:
            dataset1: First dataset
            dataset2: Second dataset
            name1: Name of first dataset
            name2: Name of second dataset
            
        Returns:
            Comparison analysis results
        """
        if not dataset1 or not dataset2:
            return {"error": "Both datasets must be non-empty"}
        
        try:
            # Basic statistics for both datasets
            stats1 = {
                "mean": statistics.mean(dataset1),
                "median": statistics.median(dataset1),
                "stdev": statistics.stdev(dataset1) if len(dataset1) > 1 else 0,
                "min": min(dataset1),
                "max": max(dataset1)
            }
            
            stats2 = {
                "mean": statistics.mean(dataset2),
                "median": statistics.median(dataset2),
                "stdev": statistics.stdev(dataset2) if len(dataset2) > 1 else 0,
                "min": min(dataset2),
                "max": max(dataset2)
            }
            
            # Differences
            mean_diff = stats2["mean"] - stats1["mean"]
            median_diff = stats2["median"] - stats1["median"]
            
            # Effect size (Cohen's d)
            pooled_stdev = math.sqrt(((len(dataset1) - 1) * stats1["stdev"]**2 + 
                                    (len(dataset2) - 1) * stats2["stdev"]**2) / 
                                   (len(dataset1) + len(dataset2) - 2))
            
            cohens_d = mean_diff / pooled_stdev if pooled_stdev != 0 else 0
            
            return {
                "dataset_comparison": {
                    name1: {
                        "count": len(dataset1),
                        "mean": round(stats1["mean"], 4),
                        "median": round(stats1["median"], 4),
                        "std_dev": round(stats1["stdev"], 4)
                    },
                    name2: {
                        "count": len(dataset2),
                        "mean": round(stats2["mean"], 4),
                        "median": round(stats2["median"], 4),
                        "std_dev": round(stats2["stdev"], 4)
                    }
                },
                "differences": {
                    "mean_difference": round(mean_diff, 4),
                    "median_difference": round(median_diff, 4),
                    "cohens_d": round(cohens_d, 4),
                    "effect_size": DataAnalyzer._interpret_cohens_d(cohens_d)
                },
                "summary": f"{name2} has {'higher' if mean_diff > 0 else 'lower'} values on average than {name1}"
            }
            
        except Exception as e:
            return {"error": f"Comparison failed: {e}"}
    
    @staticmethod
    def _interpret_cohens_d(cohens_d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"


# Convenience functions for agents
def analyze_data(numbers: List[float], dataset_name: str = "data") -> Dict[str, Any]:
    """Analyze numerical data and return comprehensive statistics."""
    return DataAnalyzer.analyze_numerical_data(numbers, dataset_name)


def compare_data(data1: List[float], data2: List[float], 
                name1: str = "Group 1", name2: str = "Group 2") -> Dict[str, Any]:
    """Compare two datasets statistically."""
    return DataAnalyzer.compare_datasets(data1, data2, name1, name2)


def generate_insights(analysis_result: Dict[str, Any]) -> List[str]:
    """Generate human-readable insights from analysis results."""
    if "error" in analysis_result:
        return [f"Analysis error: {analysis_result['error']}"]
    
    insights = []
    
    # Basic statistics insights
    if "basic_stats" in analysis_result:
        stats = analysis_result["basic_stats"]
        insights.append(f"Dataset contains {stats['count']} values with mean of {stats['mean']}")
        
        if stats.get('mode'):
            insights.append(f"Most common value: {stats['mode']}")
    
    # Variability insights
    if "variability" in analysis_result:
        var = analysis_result["variability"]
        cv = var.get("coefficient_of_variation")
        if cv:
            if cv < 15:
                insights.append("Data shows low variability (consistent values)")
            elif cv > 30:
                insights.append("Data shows high variability (dispersed values)")
            else:
                insights.append("Data shows moderate variability")
    
    # Outlier insights
    if "outliers" in analysis_result:
        outliers = analysis_result["outliers"]
        if outliers["count"] > 0:
            insights.append(f"Found {outliers['count']} outliers ({outliers['percentage']}% of data)")
    
    # Distribution insights
    if "distribution" in analysis_result:
        dist = analysis_result["distribution"]
        insights.append(f"Distribution is {dist['skewness_interpretation'].lower()}")
    
    # Trend insights
    if "trend_analysis" in analysis_result:
        trend = analysis_result["trend_analysis"]
        if trend.get("trend") != "no clear trend":
            strength = trend.get("trend_strength", "")
            insights.append(f"Data shows {strength} {trend['trend']}")
    
    return insights