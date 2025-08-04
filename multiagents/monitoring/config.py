"""
Configuration system for monitoring and logging.
"""
import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field

from .interfaces import LogLevel, ILogger
from .loggers import FileLogger, ConsoleLogger, CompositeLogger


@dataclass
class LoggingConfig:
    """Configuration for logging system."""
    default_logger: str = "composite"  # "file", "console", "composite"
    level: LogLevel = LogLevel.INFO
    json_format: bool = True
    include_metadata: bool = True
    
    # File logger settings
    file_path: str = "./logs/multiagents.log"
    max_size_mb: int = 100
    backup_count: int = 5
    
    # Console logger settings
    use_colors: bool = True
    
    # Composite logger settings (when using both file and console)
    console_min_level: LogLevel = LogLevel.WARNING


@dataclass 
class EventMonitoringConfig:
    """Configuration for event monitoring."""
    enabled: bool = True
    max_trace_history: int = 10000
    cleanup_interval_minutes: int = 60
    trace_retention_hours: int = 24
    track_performance: bool = True


@dataclass
class WorkerMonitoringConfig:
    """Configuration for worker monitoring."""
    enabled: bool = True
    health_check_interval_seconds: int = 30
    metrics_retention_hours: int = 24
    max_metrics_per_worker: int = 1000


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""
    enabled: bool = True
    collection_interval_seconds: int = 60
    retention_days: int = 7
    export_format: str = "json"  # "json", "prometheus"


@dataclass
class MonitoringConfig:
    """Complete monitoring configuration."""
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    event_monitoring: EventMonitoringConfig = field(default_factory=EventMonitoringConfig)
    worker_monitoring: WorkerMonitoringConfig = field(default_factory=WorkerMonitoringConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'MonitoringConfig':
        """Create config from dictionary."""
        # Parse logging config
        logging_data = config_dict.get("logging", {})
        if "level" in logging_data and isinstance(logging_data["level"], str):
            logging_data["level"] = LogLevel(logging_data["level"])
        if "console_min_level" in logging_data and isinstance(logging_data["console_min_level"], str):
            logging_data["console_min_level"] = LogLevel(logging_data["console_min_level"])
        
        logging_config = LoggingConfig(**logging_data)
        
        # Parse other configs  
        event_monitoring_config = EventMonitoringConfig(**config_dict.get("event_monitoring", {}))
        worker_monitoring_config = WorkerMonitoringConfig(**config_dict.get("worker_monitoring", {}))
        metrics_config = MetricsConfig(**config_dict.get("metrics", {}))
        
        return cls(
            logging=logging_config,
            event_monitoring=event_monitoring_config,
            worker_monitoring=worker_monitoring_config,
            metrics=metrics_config
        )

    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'MonitoringConfig':
        """Load configuration from YAML or JSON file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                config_dict = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                config_dict = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        return cls.from_dict(config_dict)

    @classmethod
    def from_env(cls, prefix: str = "MULTIAGENT_") -> 'MonitoringConfig':
        """Load configuration from environment variables."""
        config_dict = {
            "logging": {},
            "event_monitoring": {},
            "worker_monitoring": {},
            "metrics": {}
        }
        
        # Map environment variables to config
        env_mappings = {
            f"{prefix}LOG_LEVEL": ("logging", "level"),
            f"{prefix}LOG_FILE": ("logging", "file_path"),
            f"{prefix}LOG_FORMAT": ("logging", "json_format"),
            f"{prefix}LOG_MAX_SIZE_MB": ("logging", "max_size_mb"),
            f"{prefix}LOG_BACKUP_COUNT": ("logging", "backup_count"),
            f"{prefix}EVENT_MONITORING_ENABLED": ("event_monitoring", "enabled"),
            f"{prefix}EVENT_MAX_HISTORY": ("event_monitoring", "max_trace_history"),
            f"{prefix}EVENT_CLEANUP_INTERVAL": ("event_monitoring", "cleanup_interval_minutes"),
            f"{prefix}WORKER_MONITORING_ENABLED": ("worker_monitoring", "enabled"),
            f"{prefix}WORKER_HEALTH_CHECK_INTERVAL": ("worker_monitoring", "health_check_interval_seconds"),
            f"{prefix}METRICS_ENABLED": ("metrics", "enabled"),
            f"{prefix}METRICS_INTERVAL": ("metrics", "collection_interval_seconds"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                if key in ["enabled", "json_format", "include_metadata", "use_colors", "track_performance"]:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif key in ["max_size_mb", "backup_count", "max_trace_history", "cleanup_interval_minutes",
                           "trace_retention_hours", "health_check_interval_seconds", "metrics_retention_hours",
                           "max_metrics_per_worker", "collection_interval_seconds", "retention_days"]:
                    value = int(value)
                elif key == "level" or key == "console_min_level":
                    value = LogLevel(value.upper())
                
                config_dict[section][key] = value
        
        return cls.from_dict(config_dict)

    def create_logger(self) -> ILogger:
        """Create logger instance based on configuration."""
        if self.logging.default_logger == "console":
            return ConsoleLogger(
                json_format=self.logging.json_format,
                include_metadata=self.logging.include_metadata,
                min_level=self.logging.level,
                use_colors=self.logging.use_colors
            )
        elif self.logging.default_logger == "file":
            return FileLogger(
                log_file_path=self.logging.file_path,
                max_bytes=self.logging.max_size_mb * 1024 * 1024,
                backup_count=self.logging.backup_count,
                json_format=self.logging.json_format,
                include_metadata=self.logging.include_metadata,
                min_level=self.logging.level
            )
        elif self.logging.default_logger == "composite":
            # Create both file and console loggers
            file_logger = FileLogger(
                log_file_path=self.logging.file_path,
                max_bytes=self.logging.max_size_mb * 1024 * 1024,
                backup_count=self.logging.backup_count,
                json_format=self.logging.json_format,
                include_metadata=self.logging.include_metadata,
                min_level=self.logging.level
            )
            
            console_logger = ConsoleLogger(
                json_format=False,  # Human readable for console
                include_metadata=self.logging.include_metadata,
                min_level=self.logging.console_min_level,
                use_colors=self.logging.use_colors
            )
            
            return CompositeLogger([file_logger, console_logger])
        else:
            raise ValueError(f"Unknown logger type: {self.logging.default_logger}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "logging": {
                "default_logger": self.logging.default_logger,
                "level": self.logging.level.value,
                "json_format": self.logging.json_format,
                "include_metadata": self.logging.include_metadata,
                "file_path": self.logging.file_path,
                "max_size_mb": self.logging.max_size_mb,
                "backup_count": self.logging.backup_count,
                "use_colors": self.logging.use_colors,
                "console_min_level": self.logging.console_min_level.value,
            },
            "event_monitoring": {
                "enabled": self.event_monitoring.enabled,
                "max_trace_history": self.event_monitoring.max_trace_history,
                "cleanup_interval_minutes": self.event_monitoring.cleanup_interval_minutes,
                "trace_retention_hours": self.event_monitoring.trace_retention_hours,
                "track_performance": self.event_monitoring.track_performance,
            },
            "worker_monitoring": {
                "enabled": self.worker_monitoring.enabled,
                "health_check_interval_seconds": self.worker_monitoring.health_check_interval_seconds,
                "metrics_retention_hours": self.worker_monitoring.metrics_retention_hours,
                "max_metrics_per_worker": self.worker_monitoring.max_metrics_per_worker,
            },
            "metrics": {
                "enabled": self.metrics.enabled,
                "collection_interval_seconds": self.metrics.collection_interval_seconds,
                "retention_days": self.metrics.retention_days,
                "export_format": self.metrics.export_format,
            }
        }

    def save_to_file(self, config_path: Union[str, Path]) -> None:
        """Save configuration to file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = self.to_dict()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif config_path.suffix.lower() == '.json':
                json.dump(config_dict, f, indent=2)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def create_default_config_file(config_path: Union[str, Path]) -> None:
    """Create a default monitoring configuration file."""
    config = MonitoringConfig()
    config.save_to_file(config_path)


def load_monitoring_config(config_path: Optional[Union[str, Path]] = None) -> MonitoringConfig:
    """
    Load monitoring configuration from various sources.
    
    Priority order:
    1. Explicit config file path
    2. Environment variables
    3. ./monitoring.yaml
    4. ./monitoring.json
    5. Default configuration
    """
    # Try explicit config file
    if config_path:
        return MonitoringConfig.from_file(config_path)
    
    # Try environment variables
    try:
        return MonitoringConfig.from_env()
    except Exception:
        pass
    
    # Try default config files
    for default_path in ["./monitoring.yaml", "./monitoring.yml", "./monitoring.json"]:
        if Path(default_path).exists():
            try:
                return MonitoringConfig.from_file(default_path)
            except Exception:
                continue
    
    # Return default configuration
    return MonitoringConfig()