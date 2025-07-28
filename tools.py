import ast
import math
import operator
import re
import requests
from datetime import datetime
from typing import Dict, Any
import pytz
from urllib.parse import quote

def calculator_tool(expression: str) -> str:
    """
    Safely evaluate mathematical expressions.
    
    Args:
        expression: Math expression like "2 + 3 * 4" or "sqrt(16)"
    
    Returns:
        String with the calculation result
    """
    if not expression or not expression.strip():
        return "Error: Empty expression provided"
    
    try:
        # Clean the expression
        expression = expression.strip()
        
        # Replace common math functions and constants
        replacements = {
            'sqrt': 'math.sqrt',
            'sin': 'math.sin', 
            'cos': 'math.cos',
            'tan': 'math.tan',
            'log': 'math.log',
            'ln': 'math.log',
            'log10': 'math.log10',
            'pi': 'math.pi',
            'e': 'math.e',
            '^': '**'  # Handle exponentiation
        }
        
        for old, new in replacements.items():
            expression = re.sub(r'\b' + old + r'\b', new, expression)
        
        # Define safe operations
        safe_dict = {
            '__builtins__': {},
            'math': math,
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum
        }
        
        # Parse and evaluate safely
        node = ast.parse(expression, mode='eval')
        
        # Check for dangerous operations
        for node_item in ast.walk(node):
            if isinstance(node_item, ast.Call):
                if hasattr(node_item.func, 'id') and node_item.func.id not in ['abs', 'round', 'min', 'max', 'sum']:
                    # Allow math functions
                    continue
            elif isinstance(node_item, ast.Name):
                if node_item.id not in safe_dict and not node_item.id.startswith('math.'):
                    raise ValueError(f"Unsafe operation: {node_item.id}")
        
        result = eval(compile(node, '<string>', 'eval'), safe_dict)
        
        # Format the result nicely
        if isinstance(result, float):
            if result.is_integer():
                return f"{expression} = {int(result)}"
            else:
                return f"{expression} = {result:.10g}"
        else:
            return f"{expression} = {result}"
            
    except SyntaxError:
        return f"Error: Invalid mathematical expression '{expression}'"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"

def get_current_time(timezone: str = "UTC") -> str:
    """
    Get current time in specified timezone.
    
    Args:
        timezone: Timezone string like "UTC", "US/Eastern", "Asia/Tokyo"
    
    Returns:
        Formatted time string with timezone info
    """
    if not timezone:
        timezone = "UTC"
    
    try:
        # Handle common timezone aliases
        timezone_aliases = {
            'EST': 'US/Eastern',
            'PST': 'US/Pacific', 
            'CST': 'US/Central',
            'MST': 'US/Mountain',
            'JST': 'Asia/Tokyo',
            'GMT': 'GMT',
            'CET': 'Europe/Paris',
            'IST': 'Asia/Kolkata'
        }
        
        timezone = timezone_aliases.get(timezone, timezone)
        
        # Get timezone object
        try:
            tz = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            # Try to find similar timezones
            suggestions = [tz for tz in pytz.all_timezones if timezone.lower() in tz.lower()][:3]
            suggestion_text = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
            return f"Error: Unknown timezone '{timezone}'.{suggestion_text}"
        
        # Get current time in timezone
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        local_time = utc_now.astimezone(tz)
        
        # Format the time nicely
        formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        day_name = local_time.strftime("%A")
        
        return f"Current time in {timezone}: {formatted_time} ({day_name})"
        
    except Exception as e:
        return f"Error getting time for timezone '{timezone}': {str(e)}"
