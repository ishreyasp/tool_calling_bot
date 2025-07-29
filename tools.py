import math
import re
import requests
from datetime import datetime
from typing import Dict, Any, List
import pytz
from urllib.parse import quote

def calculator_tool(expression: str) -> str:
    """
    Evaluate simple and complex mathematical expressions.
    
    Args:
        expression: Math expression like "2 + 3 * 4" or "sqrt(16)" or "sin(180)""
    
    Returns:
        String with the calculation result   
    """

    # Validate input
    if not expression or not expression.strip():
        return "Error: Expression cannot be empty or only whitespace"

    # Clean the expression
    expression = expression.strip().lower()

    # Define keywords for percentage calculations
    percentage_keywords = ["% of", "percent of", "percentage of"]
    
    # Handle percentage expressions like "15% of 847" or "15 percent of 847"
    for keyword in percentage_keywords:
        if keyword in expression:
            parts = expression.split(keyword)
            if len(parts) == 2:  
                try:
                    percent = float(parts[0].strip())
                    number = float(parts[1].strip())
                    result = (percent/100) * number
                    return f"{percent}% of {number} = {result}"
                except:
                    return "Error: Invalid percentage format"  
    
    # Replace common math functions and constants
    math_functions = {
        'sqrt': 'math.sqrt',
        'sin': 'math.sin', 
        'cos': 'math.cos',
        'tan': 'math.tan',
        'log': 'math.log',
        'pi': 'math.pi',
        'e': 'math.e'
    }
    
    # Replace function names with math module versions
    for func_name, math_func in math_functions.items():
        pattern = r'\b' + func_name + r'\b'
        expression = re.sub(pattern, math_func, expression)
    
    # Define safe operations
    safe_dict = {
        '__builtins__': {},
        'math': math,
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'pow': pow 
    }
    
    try:
        # Evaluate the expression safely
        result = eval(expression, safe_dict)
        
        # Format result nicely
        if isinstance(result, float):
            if result.is_integer():
                return f"{expression} = {int(result)}"
            else:
                # Round very small numbers to avoid floating point errors
                if abs(result) < 1e-10:
                    result = 0
                return f"{expression} = {result:.10g}"
        else:
            return f"{expression} = {result}"
    except SyntaxError:
        return f"Error: Invalid mathematical expression '{expression}'"    
    except ZeroDivisionError:
        return "Error: Division by zero is not allowed"
    except ValueError as e:
        if "math domain error" in str(e).lower():
            return "Error: Invalid input for math function (e.g., sqrt of negative number)"
        else:
            return f"Error: Invalid value in expression - {str(e)}"
    except NameError:
        return f"Error: Unknown function or variable in expression '{expression}'"
    except Exception as e:
        return f"Error: Cannot evaluate expression '{expression}' - {str(e)}"

def get_current_time(timezone: str = "UTC") -> str:
    """
    Get current time in specified timezone.
    
    Args:
        timezone (str): Timezone identifier.
    
    Returns:
        str: Formatted time string with timezone information and day of week.
    """

    # Validate timezone input
    if not timezone or not timezone.strip():
        timezone = "UTC"
    
    # Clean the timezone string
    timezone = timezone.strip()

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
            'IST': 'Asia/Kolkata',
            'BST': 'Europe/London',
            'PDT': 'US/Pacific',
            'EDT': 'US/Eastern'
        }
        
        # Convert to uppercase to match keys
        timezone = timezone_aliases.get(timezone.upper(), timezone)
        print(f"DEBUG: Resolved timezone: {timezone}")

        # Get timezone object
        try:
            tz = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            return f"Error: Unknown timezone '{timezone}"
        
        # Get current time in timezone
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        local_time = utc_now.astimezone(tz)
        
        # Format the time nicely
        formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        day_name = local_time.strftime("%A")
        
        return f"Current time in {timezone}: {formatted_time} ({day_name})"
        
    except Exception as e:
        return f"Error getting time for timezone '{timezone}': {str(e)}"