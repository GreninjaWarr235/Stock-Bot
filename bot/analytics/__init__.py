"""
analytics package
=================
Analytics, reporting, and signal verification tools for Stock Bot.
"""

def view_recent_alerts(*args, **kwargs):
    from analytics.view_alerts import view_recent_alerts as _func
    return _func(*args, **kwargs)

def display_alerts_table(*args, **kwargs):
    from analytics.view_alerts import display_alerts_table as _func
    return _func(*args, **kwargs)

def evaluate_signal_performance(*args, **kwargs):
    from analytics.performance import evaluate_signal_performance as _func
    return _func(*args, **kwargs)

__all__ = [
    "view_recent_alerts",
    "display_alerts_table",
    "evaluate_signal_performance",
]
