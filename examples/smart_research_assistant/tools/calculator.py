"""
Calculator tool for mathematical operations and financial calculations.
"""
import ast
import operator
import re
from typing import Dict, Any, Union, List
import math
from decimal import Decimal, getcontext

# Set precision for financial calculations
getcontext().prec = 10


class SafeCalculator:
    """Safe calculator that evaluates mathematical expressions."""
    
    # Allowed operators
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.BitXor: operator.xor,
        ast.USub: operator.neg,
    }
    
    # Allowed functions
    functions = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'sqrt': math.sqrt,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'pow': pow,
    }
    
    def evaluate(self, expression: str) -> float:
        """Safely evaluate a mathematical expression."""
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Parse the expression
            node = ast.parse(expression, mode='eval')
            
            # Evaluate the AST
            result = self._eval_node(node.body)
            
            return float(result)
            
        except Exception as e:
            raise ValueError(f"Invalid mathematical expression: {e}")
    
    def _eval_node(self, node) -> Union[float, int]:
        """Recursively evaluate AST nodes."""
        if isinstance(node, ast.Constant):  # Numbers
            return node.value
        elif isinstance(node, ast.Name):  # Variables (constants only)
            if node.id == 'pi':
                return math.pi
            elif node.id == 'e':
                return math.e
            else:
                raise ValueError(f"Unknown variable: {node.id}")
        elif isinstance(node, ast.BinOp):  # Binary operations
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):  # Unary operations
            operand = self._eval_node(node.operand)
            op = self.operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
            return op(operand)
        elif isinstance(node, ast.Call):  # Function calls
            func_name = node.func.id
            if func_name not in self.functions:
                raise ValueError(f"Unsupported function: {func_name}")
            
            args = [self._eval_node(arg) for arg in node.args]
            return self.functions[func_name](*args)
        else:
            raise ValueError(f"Unsupported AST node: {type(node)}")


def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.
    
    Args:
        expression: Mathematical expression as string
        
    Returns:
        String representation of the result
    """
    try:
        calculator = SafeCalculator()
        result = calculator.evaluate(expression)
        
        # Format result nicely
        if result == int(result):
            return str(int(result))
        else:
            return f"{result:.6g}"  # Remove trailing zeros
            
    except Exception as e:
        return f"Error: {e}"


def calculate_roi(initial_investment: float, final_value: float, years: float) -> Dict[str, Any]:
    """
    Calculate Return on Investment (ROI) and annualized return.
    
    Args:
        initial_investment: Initial investment amount
        final_value: Final investment value
        years: Investment period in years
        
    Returns:
        Dictionary with ROI calculations
    """
    try:
        if initial_investment <= 0:
            return {"error": "Initial investment must be positive"}
        
        if years <= 0:
            return {"error": "Years must be positive"}
        
        # Total ROI percentage
        total_roi = ((final_value - initial_investment) / initial_investment) * 100
        
        # Annualized return (CAGR)
        if final_value > 0:
            annualized_return = (pow(final_value / initial_investment, 1 / years) - 1) * 100
        else:
            annualized_return = -100  # Total loss
        
        # Profit/Loss
        profit_loss = final_value - initial_investment
        
        return {
            "initial_investment": initial_investment,
            "final_value": final_value,
            "years": years,
            "total_roi_percent": round(total_roi, 2),
            "annualized_return_percent": round(annualized_return, 2),
            "profit_loss": round(profit_loss, 2),
            "total_return_multiple": round(final_value / initial_investment, 2)
        }
        
    except Exception as e:
        return {"error": f"ROI calculation error: {e}"}


def calculate_compound_interest(principal: float, rate: float, years: float, 
                               compound_frequency: int = 12) -> Dict[str, Any]:
    """
    Calculate compound interest.
    
    Args:
        principal: Initial principal amount
        rate: Annual interest rate (as percentage)
        years: Investment period in years
        compound_frequency: How many times per year interest compounds (default: 12 monthly)
        
    Returns:
        Dictionary with compound interest calculations
    """
    try:
        if principal <= 0:
            return {"error": "Principal must be positive"}
        
        if years < 0:
            return {"error": "Years cannot be negative"}
        
        # Convert percentage to decimal
        annual_rate = rate / 100
        
        # Compound interest formula: A = P(1 + r/n)^(nt)
        final_amount = principal * pow(1 + annual_rate / compound_frequency, 
                                     compound_frequency * years)
        
        # Interest earned
        interest_earned = final_amount - principal
        
        return {
            "principal": principal,
            "annual_rate_percent": rate,
            "years": years,
            "compound_frequency": compound_frequency,
            "final_amount": round(final_amount, 2),
            "interest_earned": round(interest_earned, 2),
            "total_roi_percent": round((interest_earned / principal) * 100, 2)
        }
        
    except Exception as e:
        return {"error": f"Compound interest calculation error: {e}"}


def calculate_statistics(numbers: List[float]) -> Dict[str, Any]:
    """
    Calculate basic statistics for a list of numbers.
    
    Args:
        numbers: List of numerical values
        
    Returns:
        Dictionary with statistical calculations
    """
    try:
        if not numbers:
            return {"error": "Empty list provided"}
        
        n = len(numbers)
        total = sum(numbers)
        mean = total / n
        
        # Sort for median calculation
        sorted_nums = sorted(numbers)
        
        # Median
        if n % 2 == 0:
            median = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
        else:
            median = sorted_nums[n//2]
        
        # Standard deviation
        variance = sum((x - mean) ** 2 for x in numbers) / n
        std_dev = math.sqrt(variance)
        
        return {
            "count": n,
            "sum": round(total, 2),
            "mean": round(mean, 2),
            "median": round(median, 2),
            "min": min(numbers),
            "max": max(numbers),
            "range": round(max(numbers) - min(numbers), 2),
            "variance": round(variance, 2),
            "standard_deviation": round(std_dev, 2)
        }
        
    except Exception as e:
        return {"error": f"Statistics calculation error: {e}"}