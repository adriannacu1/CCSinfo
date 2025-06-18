#!/usr/bin/env python3
"""
Test the safe_strftime function to ensure it handles different datetime formats
"""
from datetime import datetime

def safe_strftime(datetime_obj, format_str='%H:%M:%S'):
    """Safely format datetime objects or strings to the specified format"""
    if not datetime_obj:
        return None
    
    # If it's already a string, try to parse it first
    if isinstance(datetime_obj, str):
        try:
            # Try to parse as datetime
            parsed_dt = datetime.strptime(datetime_obj, '%Y-%m-%d %H:%M:%S')
            return parsed_dt.strftime(format_str)
        except ValueError:
            try:
                # If that fails, try to extract time part if it contains space
                if ' ' in datetime_obj:
                    time_part = datetime_obj.split(' ')[1]
                    return time_part[:8]  # Return HH:MM:SS
                else:
                    return datetime_obj[:8]  # Assume it's already time format
            except:
                return str(datetime_obj)
    
    # If it's a datetime object, format it normally
    try:
        return datetime_obj.strftime(format_str)
    except AttributeError:
        return str(datetime_obj)

# Test cases
test_cases = [
    # Datetime object
    datetime.now(),
    
    # String datetime
    "2025-06-17 22:53:40",
    
    # String time only
    "14:30:25",
    
    # None value
    None,
    
    # Invalid string
    "invalid_datetime",
    
    # Different format string
    "2025-06-17 22:53:40",
]

print("Testing safe_strftime function:")
print("=" * 50)

for i, test_case in enumerate(test_cases):
    try:
        result = safe_strftime(test_case)
        print(f"Test {i+1}: {repr(test_case)} -> {repr(result)}")
    except Exception as e:
        print(f"Test {i+1}: {repr(test_case)} -> ERROR: {e}")

print("\nAll tests completed!")
