"""
Metrics collection utilities for load testing.
Collects performance metrics during load tests and generates reports.
"""
import asyncio
import time
import psutil
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Deque
import json
import csv
from pathlib import Path
import statistics


@dataclass
class RequestMetrics:
    """Metrics for a single request/workflow execution."""
    timestamp: float
    duration: float
    success: bool
    error: Optional[str] = None
    transaction_id: Optional[str] = None
    workflow_type: Optional[str] = None
    step_count: int = 0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0


@dataclass
class SystemMetrics:
    """System resource metrics at a point in time."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    redis_connections: int = 0
    active_workflows: int = 0


@dataclass
class LoadTestSummary:
    """Summary of load test results."""
    test_name: str
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    peak_memory_mb: float
    avg_cpu_percent: float
    peak_cpu_percent: float
    errors: Dict[str, int] = field(default_factory=dict)


class PerformanceCollector:
    """Collects performance metrics during load testing."""
    
    def __init__(self, collection_interval: float = 1.0):
        self.collection_interval = collection_interval
        self.request_metrics: List[RequestMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        
        # Real-time tracking
        self.active_requests = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        # Threading
        self._collecting = False
        self._collection_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # System monitoring
        self._process = psutil.Process()
        self._start_time = time.time()
    
    def start_collection(self):
        """Start collecting system metrics."""
        if self._collecting:
            return
            
        self._collecting = True
        self._start_time = time.time()
        self._collection_thread = threading.Thread(target=self._collect_system_metrics)
        self._collection_thread.daemon = True
        self._collection_thread.start()
    
    def stop_collection(self):
        """Stop collecting metrics."""
        self._collecting = False
        if self._collection_thread:
            self._collection_thread.join(timeout=2.0)
    
    def record_request_start(self, transaction_id: str = None, workflow_type: str = None) -> float:
        """Record the start of a request."""
        with self._lock:
            self.active_requests += 1
            self.total_requests += 1
        return time.time()
    
    def record_request_end(self, start_time: float, success: bool, 
                          error: str = None, transaction_id: str = None,
                          workflow_type: str = None, step_count: int = 0):
        """Record the end of a request."""
        end_time = time.time()
        duration = end_time - start_time
        
        # Get current system usage
        try:
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            cpu_percent = self._process.cpu_percent()
        except:
            memory_mb = 0.0
            cpu_percent = 0.0
        
        metrics = RequestMetrics(
            timestamp=end_time,
            duration=duration,
            success=success,
            error=error,
            transaction_id=transaction_id,
            workflow_type=workflow_type,
            step_count=step_count,
            memory_usage_mb=memory_mb,
            cpu_percent=cpu_percent
        )
        
        with self._lock:
            self.active_requests -= 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            self.request_metrics.append(metrics)
    
    def _collect_system_metrics(self):
        """Background thread for collecting system metrics."""
        while self._collecting:
            try:
                # CPU and Memory
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                
                # Network I/O
                network_io = psutil.net_io_counters()
                
                metrics = SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / 1024 / 1024,
                    disk_io_read_mb=disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
                    disk_io_write_mb=disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
                    network_sent_mb=network_io.bytes_sent / 1024 / 1024 if network_io else 0,
                    network_recv_mb=network_io.bytes_recv / 1024 / 1024 if network_io else 0,
                    active_workflows=self.active_requests
                )
                
                with self._lock:
                    self.system_metrics.append(metrics)
                
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
            
            time.sleep(self.collection_interval)
    
    def get_summary(self, test_name: str) -> LoadTestSummary:
        """Generate a summary of the load test results."""
        with self._lock:
            if not self.request_metrics:
                return LoadTestSummary(
                    test_name=test_name,
                    duration_seconds=0,
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    requests_per_second=0,
                    avg_response_time=0,
                    min_response_time=0,
                    max_response_time=0,
                    p50_response_time=0,
                    p95_response_time=0,
                    p99_response_time=0,
                    error_rate=0,
                    peak_memory_mb=0,
                    avg_cpu_percent=0,
                    peak_cpu_percent=0
                )
            
            # Calculate duration
            start_time = min(m.timestamp for m in self.request_metrics)
            end_time = max(m.timestamp for m in self.request_metrics)
            duration = end_time - start_time
            
            # Response time statistics
            response_times = [m.duration for m in self.request_metrics]
            response_times.sort()
            
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # Percentiles
            p50_idx = int(len(response_times) * 0.5)
            p95_idx = int(len(response_times) * 0.95)
            p99_idx = int(len(response_times) * 0.99)
            
            p50_response_time = response_times[p50_idx] if response_times else 0
            p95_response_time = response_times[p95_idx] if response_times else 0
            p99_response_time = response_times[p99_idx] if response_times else 0
            
            # Error analysis
            errors = defaultdict(int)
            for metric in self.request_metrics:
                if metric.error:
                    errors[metric.error] += 1
            
            # System metrics
            if self.system_metrics:
                peak_memory_mb = max(m.memory_used_mb for m in self.system_metrics)
                avg_cpu_percent = statistics.mean(m.cpu_percent for m in self.system_metrics)
                peak_cpu_percent = max(m.cpu_percent for m in self.system_metrics)
            else:
                peak_memory_mb = 0
                avg_cpu_percent = 0
                peak_cpu_percent = 0
            
            return LoadTestSummary(
                test_name=test_name,
                duration_seconds=duration,
                total_requests=self.total_requests,
                successful_requests=self.successful_requests,
                failed_requests=self.failed_requests,
                requests_per_second=self.total_requests / duration if duration > 0 else 0,
                avg_response_time=avg_response_time,
                min_response_time=min_response_time,
                max_response_time=max_response_time,
                p50_response_time=p50_response_time,
                p95_response_time=p95_response_time,
                p99_response_time=p99_response_time,
                error_rate=self.failed_requests / self.total_requests if self.total_requests > 0 else 0,
                peak_memory_mb=peak_memory_mb,
                avg_cpu_percent=avg_cpu_percent,
                peak_cpu_percent=peak_cpu_percent,
                errors=dict(errors)
            )
    
    def export_detailed_metrics(self, output_dir: Path):
        """Export detailed metrics for analysis."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export request metrics
        request_file = output_dir / "request_metrics.csv"
        with open(request_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'duration', 'success', 'error', 'transaction_id',
                'workflow_type', 'step_count', 'memory_usage_mb', 'cpu_percent'
            ])
            
            for metric in self.request_metrics:
                writer.writerow([
                    metric.timestamp,
                    metric.duration,
                    metric.success,
                    metric.error or '',
                    metric.transaction_id or '',
                    metric.workflow_type or '',
                    metric.step_count,
                    metric.memory_usage_mb,
                    metric.cpu_percent
                ])
        
        # Export system metrics
        system_file = output_dir / "system_metrics.csv"
        with open(system_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'cpu_percent', 'memory_percent', 'memory_used_mb',
                'disk_io_read_mb', 'disk_io_write_mb', 'network_sent_mb',
                'network_recv_mb', 'active_workflows'
            ])
            
            for metric in self.system_metrics:
                writer.writerow([
                    metric.timestamp,
                    metric.cpu_percent,
                    metric.memory_percent,
                    metric.memory_used_mb,
                    metric.disk_io_read_mb,
                    metric.disk_io_write_mb,
                    metric.network_sent_mb,
                    metric.network_recv_mb,
                    metric.active_workflows
                ])
    
    def clear_metrics(self):
        """Clear all collected metrics."""
        with self._lock:
            self.request_metrics.clear()
            self.system_metrics.clear()
            self.active_requests = 0
            self.total_requests = 0
            self.successful_requests = 0
            self.failed_requests = 0


class LoadTestReporter:
    """Generates reports from load test results."""
    
    @staticmethod
    def print_summary(summary: LoadTestSummary):
        """Print a formatted summary to console."""
        print("\n" + "="*80)
        print(f"LOAD TEST SUMMARY: {summary.test_name}")
        print("="*80)
        
        print(f"Duration: {summary.duration_seconds:.2f} seconds")
        print(f"Total Requests: {summary.total_requests}")
        print(f"Successful: {summary.successful_requests}")
        print(f"Failed: {summary.failed_requests}")
        print(f"Error Rate: {summary.error_rate:.2%}")
        print(f"Requests/sec: {summary.requests_per_second:.2f}")
        
        print("\nResponse Times (seconds):")
        print(f"  Average: {summary.avg_response_time:.3f}")
        print(f"  Min: {summary.min_response_time:.3f}")
        print(f"  Max: {summary.max_response_time:.3f}")
        print(f"  50th percentile: {summary.p50_response_time:.3f}")
        print(f"  95th percentile: {summary.p95_response_time:.3f}")
        print(f"  99th percentile: {summary.p99_response_time:.3f}")
        
        print("\nSystem Resources:")
        print(f"  Peak Memory: {summary.peak_memory_mb:.1f} MB")
        print(f"  Average CPU: {summary.avg_cpu_percent:.1f}%")
        print(f"  Peak CPU: {summary.peak_cpu_percent:.1f}%")
        
        if summary.errors:
            print("\nErrors:")
            for error, count in summary.errors.items():
                print(f"  {error}: {count}")
        
        print("="*80)
    
    @staticmethod
    def export_json_report(summary: LoadTestSummary, output_file: Path):
        """Export summary as JSON."""
        data = {
            'test_name': summary.test_name,
            'timestamp': datetime.utcnow().isoformat(),
            'duration_seconds': summary.duration_seconds,
            'total_requests': summary.total_requests,
            'successful_requests': summary.successful_requests,
            'failed_requests': summary.failed_requests,
            'error_rate': summary.error_rate,
            'requests_per_second': summary.requests_per_second,
            'response_times': {
                'avg': summary.avg_response_time,
                'min': summary.min_response_time,
                'max': summary.max_response_time,
                'p50': summary.p50_response_time,
                'p95': summary.p95_response_time,
                'p99': summary.p99_response_time
            },
            'system_resources': {
                'peak_memory_mb': summary.peak_memory_mb,
                'avg_cpu_percent': summary.avg_cpu_percent,
                'peak_cpu_percent': summary.peak_cpu_percent
            },
            'errors': summary.errors
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def generate_html_report(summary: LoadTestSummary, detailed_metrics_dir: Path, 
                           output_file: Path):
        """Generate an HTML report with charts."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Load Test Report: {test_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .metric h3 {{ margin-top: 0; color: #333; }}
        .metric .value {{ font-size: 24px; font-weight: bold; color: #007acc; }}
        .chart-container {{ width: 100%; height: 400px; margin: 20px 0; }}
        .error-rate {{ color: #d32f2f; }}
        .success-rate {{ color: #388e3c; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Load Test Report: {test_name}</h1>
        <p>Generated: {timestamp}</p>
        <p>Duration: {duration:.2f} seconds</p>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <h3>Total Requests</h3>
            <div class="value">{total_requests}</div>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <div class="value success-rate">{success_rate:.1%}</div>
        </div>
        <div class="metric">
            <h3>Error Rate</h3>
            <div class="value error-rate">{error_rate:.1%}</div>
        </div>
        <div class="metric">
            <h3>Requests/sec</h3>
            <div class="value">{rps:.2f}</div>
        </div>
        <div class="metric">
            <h3>Avg Response Time</h3>
            <div class="value">{avg_response:.3f}s</div>
        </div>
        <div class="metric">
            <h3>95th Percentile</h3>
            <div class="value">{p95:.3f}s</div>
        </div>
    </div>
    
    <h2>Response Time Distribution</h2>
    <table>
        <tr><th>Percentile</th><th>Response Time (seconds)</th></tr>
        <tr><td>50th</td><td>{p50:.3f}</td></tr>
        <tr><td>95th</td><td>{p95:.3f}</td></tr>
        <tr><td>99th</td><td>{p99:.3f}</td></tr>
        <tr><td>Min</td><td>{min_response:.3f}</td></tr>
        <tr><td>Max</td><td>{max_response:.3f}</td></tr>
    </table>
    
    <h2>System Resources</h2>
    <div class="metrics">
        <div class="metric">
            <h3>Peak Memory</h3>
            <div class="value">{peak_memory:.1f} MB</div>
        </div>
        <div class="metric">
            <h3>Average CPU</h3>
            <div class="value">{avg_cpu:.1f}%</div>
        </div>
        <div class="metric">
            <h3>Peak CPU</h3>
            <div class="value">{peak_cpu:.1f}%</div>
        </div>
    </div>
    
    {error_section}
</body>
</html>
        """
        
        # Format error section
        error_section = ""
        if summary.errors:
            error_section = "<h2>Errors</h2><table><tr><th>Error</th><th>Count</th></tr>"
            for error, count in summary.errors.items():
                error_section += f"<tr><td>{error}</td><td>{count}</td></tr>"
            error_section += "</table>"
        
        html_content = html_template.format(
            test_name=summary.test_name,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            duration=summary.duration_seconds,
            total_requests=summary.total_requests,
            success_rate=1 - summary.error_rate,
            error_rate=summary.error_rate,
            rps=summary.requests_per_second,
            avg_response=summary.avg_response_time,
            p50=summary.p50_response_time,
            p95=summary.p95_response_time,
            p99=summary.p99_response_time,
            min_response=summary.min_response_time,
            max_response=summary.max_response_time,
            peak_memory=summary.peak_memory_mb,
            avg_cpu=summary.avg_cpu_percent,
            peak_cpu=summary.peak_cpu_percent,
            error_section=error_section
        )
        
        with open(output_file, 'w') as f:
            f.write(html_content)