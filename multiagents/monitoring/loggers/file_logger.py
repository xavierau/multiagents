"""
File-based logger implementation with rotation and structured output.
"""
import json
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
import logging

from ..interfaces import ILogger, LogLevel


class FileLogger(ILogger):
    """
    File-based logger with rotation, JSON formatting, and async support.
    Default logger implementation for the MultiAgents framework.
    """

    def __init__(self, 
                 log_file_path: str = "./logs/multiagents.log",
                 max_bytes: int = 100 * 1024 * 1024,  # 100MB
                 backup_count: int = 5,
                 json_format: bool = True,
                 include_metadata: bool = True,
                 min_level: LogLevel = LogLevel.INFO):
        
        self.log_file_path = Path(log_file_path)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.json_format = json_format
        self.include_metadata = include_metadata
        self.min_level = min_level
        
        # Create log directory if it doesn't exist
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up rotating file handler
        self._setup_logger()
        
        # Queue for async logging
        self._log_queue = asyncio.Queue()
        self._writer_task = None
        self._running = False

    def _setup_logger(self) -> None:
        """Set up the internal logger with rotating file handler."""
        self.logger = logging.getLogger(f"multiagents_file_logger_{id(self)}")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create rotating file handler
        handler = RotatingFileHandler(
            filename=str(self.log_file_path),
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        # Set formatter
        if self.json_format:
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False

    async def _start_writer(self) -> None:
        """Start the async log writer task."""
        if self._writer_task is None or self._writer_task.done():
            self._running = True
            self._writer_task = asyncio.create_task(self._log_writer())

    async def _log_writer(self) -> None:
        """Async task that writes log entries from the queue."""
        while self._running or not self._log_queue.empty():
            try:
                # Get log entry from queue with timeout
                log_entry = await asyncio.wait_for(
                    self._log_queue.get(), 
                    timeout=1.0
                )
                
                # Write to file
                self._write_log_entry(log_entry)
                self._log_queue.task_done()
                
            except asyncio.TimeoutError:
                # Timeout is expected when queue is empty
                continue
            except Exception as e:
                # Log errors to stderr to avoid recursion
                print(f"Error in log writer: {e}", file=__import__('sys').stderr)

    def _write_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Write a log entry to the file."""
        level = log_entry["level"]
        message = log_entry["message"]
        
        if self.json_format:
            # Write as JSON
            json_entry = json.dumps(log_entry, default=str, ensure_ascii=False)
            getattr(self.logger, level.lower())(json_entry)
        else:
            # Write as formatted text
            metadata_str = ""
            if self.include_metadata and log_entry.get("metadata"):
                metadata_str = f" | {json.dumps(log_entry['metadata'], default=str)}"
            
            error_str = ""
            if log_entry.get("error"):
                error_str = f" | ERROR: {log_entry['error']}"
            
            full_message = f"{message}{metadata_str}{error_str}"
            getattr(self.logger, level.lower())(full_message)

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

    async def log(self, level: LogLevel, message: str, 
                  metadata: Optional[Dict[str, Any]] = None,
                  error: Optional[Exception] = None) -> None:
        """Log a message with metadata and error information."""
        if not self._should_log(level):
            return

        # Ensure writer is running
        await self._start_writer()

        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
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
                "traceback": self._format_exception(error)
            }

        # Add to queue for async writing
        try:
            self._log_queue.put_nowait(log_entry)
        except asyncio.QueueFull:
            # If queue is full, write directly (blocking)
            self._write_log_entry(log_entry)

    def _format_exception(self, error: Exception) -> str:
        """Format exception with traceback."""
        import traceback
        return ''.join(traceback.format_exception(
            type(error), error, error.__traceback__
        ))

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
        self._running = False
        
        # Wait for writer task to finish
        if self._writer_task and not self._writer_task.done():
            try:
                await asyncio.wait_for(self._writer_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._writer_task.cancel()
        
        # Close handlers
        for handler in self.logger.handlers:
            handler.close()

    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about the log file."""
        try:
            stat = self.log_file_path.stat()
            return {
                "log_file": str(self.log_file_path),
                "file_size_bytes": stat.st_size,
                "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "max_size_mb": round(self.max_bytes / (1024 * 1024), 2),
                "backup_count": self.backup_count,
                "json_format": self.json_format,
                "min_level": self.min_level.value,
                "queue_size": self._log_queue.qsize() if self._log_queue else 0,
                "writer_running": self._running,
            }
        except Exception as e:
            return {
                "error": f"Failed to get log stats: {e}",
                "log_file": str(self.log_file_path),
            }