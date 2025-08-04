"""
Console logger implementation for development and debugging.
"""
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, TextIO

from ..interfaces import ILogger, LogLevel


class ConsoleLogger(ILogger):
    """
    Console logger for development and debugging.
    Outputs structured logs to stdout/stderr with color support.
    """

    def __init__(self, 
                 json_format: bool = False,
                 include_metadata: bool = True,
                 min_level: LogLevel = LogLevel.INFO,
                 use_colors: bool = True,
                 error_stream: TextIO = None,
                 output_stream: TextIO = None):
        
        self.json_format = json_format
        self.include_metadata = include_metadata
        self.min_level = min_level
        self.use_colors = use_colors and sys.stdout.isatty()
        self.error_stream = error_stream or sys.stderr
        self.output_stream = output_stream or sys.stdout

        # ANSI color codes
        self.colors = {
            LogLevel.DEBUG: '\033[36m',      # Cyan
            LogLevel.INFO: '\033[32m',       # Green  
            LogLevel.WARNING: '\033[33m',    # Yellow
            LogLevel.ERROR: '\033[31m',      # Red
            LogLevel.CRITICAL: '\033[35m',   # Magenta
        }
        self.reset_color = '\033[0m'

    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on minimum level."""
        level_hierarchy = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        return level_hierarchy[level] >= level_hierarchy[self.min_level]

    def _get_output_stream(self, level: LogLevel) -> TextIO:
        """Get appropriate output stream based on log level."""
        if level in (LogLevel.ERROR, LogLevel.CRITICAL):
            return self.error_stream
        return self.output_stream

    def _format_level(self, level: LogLevel) -> str:
        """Format log level with color if enabled."""
        level_str = level.value
        if self.use_colors:
            color = self.colors.get(level, '')
            return f"{color}{level_str}{self.reset_color}"
        return level_str

    def _format_timestamp(self) -> str:
        """Format current timestamp."""
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"

    async def log(self, level: LogLevel, message: str, 
                  metadata: Optional[Dict[str, Any]] = None,
                  error: Optional[Exception] = None) -> None:
        """Log a message with metadata and error information."""
        if not self._should_log(level):
            return

        stream = self._get_output_stream(level)
        
        if self.json_format:
            # JSON format
            log_entry = {
                "timestamp": self._format_timestamp(),
                "level": level.value,
                "message": message,
                "component": "multiagents",
            }

            if self.include_metadata and metadata:
                log_entry["metadata"] = metadata

            if error:
                log_entry["error"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                }

            json_str = json.dumps(log_entry, default=str, ensure_ascii=False)
            print(json_str, file=stream)
        else:
            # Human-readable format
            timestamp = self._format_timestamp()
            level_str = self._format_level(level)
            
            # Base message
            output_parts = [f"[{timestamp}] {level_str} {message}"]
            
            # Add metadata
            if self.include_metadata and metadata:
                metadata_str = " | ".join([f"{k}={v}" for k, v in metadata.items()])
                output_parts.append(f" | {metadata_str}")
            
            # Add error information
            if error:
                error_str = f" | ERROR: {type(error).__name__}: {error}"
                output_parts.append(error_str)
            
            print("".join(output_parts), file=stream)

        # Ensure output is flushed
        stream.flush()

    async def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        await self.log(LogLevel.DEBUG, message, metadata=kwargs)

    async def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        await self.log(LogLevel.INFO, message, metadata=kwargs)

    async def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        await self.log(LogLevel.WARNING, message, metadata=kwargs)

    async def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message."""
        await self.log(LogLevel.ERROR, message, metadata=kwargs, error=error)

    async def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message."""
        await self.log(LogLevel.CRITICAL, message, metadata=kwargs, error=error)

    async def close(self) -> None:
        """Close logger and cleanup resources."""
        # Flush streams
        self.output_stream.flush()
        self.error_stream.flush()
        # No resources to clean up for console logger