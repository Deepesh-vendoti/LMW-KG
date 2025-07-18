"""
Logging and Observability Module for LangGraph Knowledge Graph System

Provides structured logging with time profiling for microservices.
Includes performance tracking, service monitoring, and error reporting.
"""

import logging
import time
import json
import functools
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.loader import config

class ServiceLogger:
    """Enhanced logger with service context and performance tracking."""
    
    def __init__(self, service_name: str, subsystem: str = None):
        self.service_name = service_name
        self.subsystem = subsystem
        self.logger = self._setup_logger()
        self.performance_data = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger with proper formatting."""
        logger = logging.getLogger(f"{self.subsystem}.{self.service_name}" if self.subsystem else self.service_name)
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler with structured format
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (if logs directory exists)
        logs_dir = Path(config.get('paths.logs', './logs'))
        if logs_dir.exists() or self._create_logs_dir(logs_dir):
            file_handler = logging.FileHandler(logs_dir / f"{self.service_name}.log")
            file_formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _create_logs_dir(self, logs_dir: Path) -> bool:
        """Create logs directory if it doesn't exist."""
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Warning: Could not create logs directory {logs_dir}: {e}")
            return False
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with service context and optional structured data."""
        if kwargs:
            context_str = " | " + " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = message + context_str
        
        self.logger.log(level, message)
    
    def start_operation(self, operation_name: str) -> str:
        """Start timing an operation. Returns operation ID."""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        self.performance_data[operation_id] = {
            'operation': operation_name,
            'start_time': time.time(),
            'service': self.service_name,
            'subsystem': self.subsystem
        }
        self.info(f"Started {operation_name}", operation_id=operation_id)
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, **metrics):
        """End timing an operation and log performance metrics."""
        if operation_id not in self.performance_data:
            self.warning(f"Operation ID {operation_id} not found in performance data")
            return
        
        operation_data = self.performance_data[operation_id]
        duration = time.time() - operation_data['start_time']
        
        operation_data.update({
            'end_time': time.time(),
            'duration_seconds': duration,
            'success': success,
            **metrics
        })
        
        status = "✅ Completed" if success else "❌ Failed"
        self.info(
            f"{status} {operation_data['operation']} in {duration:.2f}s",
            operation_id=operation_id,
            duration=f"{duration:.2f}s",
            **metrics
        )
        
        # Clean up completed operations
        del self.performance_data[operation_id]
    
    def log_state_transition(self, from_state: str, to_state: str, **context):
        """Log state transitions for debugging workflows."""
        self.info(f"State transition: {from_state} → {to_state}", **context)
    
    def log_error_with_context(self, error: Exception, operation: str = None, **context):
        """Log errors with full context for debugging."""
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'operation': operation
        }
        error_info.update(context)
        
        self.error(f"Error in {operation or 'operation'}: {error}", **error_info)

def timed_operation(operation_name: str = None):
    """Decorator to automatically time and log function execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get logger from self if it's a method
            logger = None
            if args and hasattr(args[0], 'logger') and isinstance(args[0].logger, ServiceLogger):
                logger = args[0].logger
            else:
                # Create a generic logger
                logger = ServiceLogger(func.__name__)
            
            op_name = operation_name or func.__name__
            operation_id = logger.start_operation(op_name)
            
            try:
                result = func(*args, **kwargs)
                logger.end_operation(operation_id, success=True)
                return result
            except Exception as e:
                logger.end_operation(operation_id, success=False, error=str(e))
                logger.log_error_with_context(e, operation=op_name)
                raise
        
        return wrapper
    return decorator

def get_service_logger(service_name: str, subsystem: str = None) -> ServiceLogger:
    """Factory function to create service loggers."""
    return ServiceLogger(service_name, subsystem)

# Convenience loggers for common subsystems
def get_content_logger(service_name: str) -> ServiceLogger:
    """Get logger for content subsystem services."""
    return ServiceLogger(service_name, "content")

def get_learner_logger(service_name: str) -> ServiceLogger:
    """Get logger for learner subsystem services."""
    return ServiceLogger(service_name, "learner")

def get_orchestrator_logger(service_name: str = "orchestrator") -> ServiceLogger:
    """Get logger for orchestrator components."""
    return ServiceLogger(service_name, "orchestrator")

# Global performance tracking
class PerformanceTracker:
    """Global performance tracking for the entire system."""
    
    def __init__(self):
        self.metrics = {}
        self.logger = get_service_logger("performance_tracker", "system")
    
    def record_metric(self, metric_name: str, value: float, unit: str = "", **tags):
        """Record a performance metric."""
        timestamp = datetime.now().isoformat()
        self.metrics[f"{metric_name}_{timestamp}"] = {
            'metric': metric_name,
            'value': value,
            'unit': unit,
            'timestamp': timestamp,
            'tags': tags
        }
        
        self.logger.info(f"Metric recorded: {metric_name} = {value} {unit}", **tags)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all recorded metrics."""
        return {
            'total_metrics': len(self.metrics),
            'metrics': list(self.metrics.values())
        }

# Global performance tracker instance
performance_tracker = PerformanceTracker() 