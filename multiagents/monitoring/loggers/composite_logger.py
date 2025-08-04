"""
Composite logger that can write to multiple logger implementations.
"""
import asyncio
from typing import List, Optional, Dict, Any

from ..interfaces import ILogger, LogLevel


class CompositeLogger(ILogger):
    """
    Composite logger that forwards log messages to multiple logger implementations.
    Useful for logging to both file and console simultaneously.
    """

    def __init__(self, loggers: List[ILogger]):
        """
        Initialize composite logger with a list of logger implementations.
        
        Args:
            loggers: List of logger instances to forward messages to
        """
        if not loggers:
            raise ValueError("At least one logger must be provided")
        
        self.loggers = loggers

    async def log(self, level: LogLevel, message: str, 
                  metadata: Optional[Dict[str, Any]] = None,
                  error: Optional[Exception] = None) -> None:
        """Log message to all configured loggers."""
        # Log to all loggers concurrently
        tasks = []
        for logger in self.loggers:
            task = logger.log(level, message, metadata, error)
            tasks.append(task)
        
        # Wait for all loggers to complete
        await asyncio.gather(*tasks, return_exceptions=True)

    async def debug(self, message: str, **kwargs) -> None:
        """Log debug message to all loggers."""
        await self.log(LogLevel.DEBUG, message, metadata=kwargs)

    async def info(self, message: str, **kwargs) -> None:
        """Log info message to all loggers."""
        await self.log(LogLevel.INFO, message, metadata=kwargs)

    async def warning(self, message: str, **kwargs) -> None:
        """Log warning message to all loggers."""
        await self.log(LogLevel.WARNING, message, metadata=kwargs)

    async def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message to all loggers."""
        await self.log(LogLevel.ERROR, message, metadata=kwargs, error=error)

    async def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message to all loggers."""
        await self.log(LogLevel.CRITICAL, message, metadata=kwargs, error=error)

    async def close(self) -> None:
        """Close all loggers and cleanup resources."""
        close_tasks = []
        for logger in self.loggers:
            close_tasks.append(logger.close())
        
        # Wait for all loggers to close
        await asyncio.gather(*close_tasks, return_exceptions=True)

    def add_logger(self, logger: ILogger) -> None:
        """Add a new logger to the composite."""
        if logger not in self.loggers:
            self.loggers.append(logger)

    def remove_logger(self, logger: ILogger) -> bool:
        """Remove a logger from the composite."""
        try:
            self.loggers.remove(logger)
            return True
        except ValueError:
            return False

    def get_loggers(self) -> List[ILogger]:
        """Get list of all configured loggers."""
        return self.loggers.copy()