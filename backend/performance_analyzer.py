import time
import functools
import pandas as pd
from collections import defaultdict

# Global timing storage
timing_data = defaultdict(list)

def time_function(module_name):
    """Decorator to measure function execution time"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            timing_data[f"{module_name}.{func.__name__}"].append(elapsed)
            return result
        return wrapper
    return decorator

def get_performance_report():
    """Generate performance report sorted by time"""
    report = []
    for func_name, times in timing_data.items():
        total = sum(times)
        avg = total / len(times)
        count = len(times)
        report.append({
            'Module/Function': func_name,
            'Total Time (s)': round(total, 3),
            'Avg Time (s)': round(avg, 3),
            'Call Count': count
        })
    
    df = pd.DataFrame(report)
    df = df.sort_values('Total Time (s)', ascending=False)
    return df

def clear_timing_data():
    """Clear all timing data"""
    timing_data.clear()
