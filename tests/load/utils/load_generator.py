"""
Load generation utilities for performance testing.
Generates various load patterns and controls test execution.
"""
import asyncio
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Any, Callable, Optional, AsyncGenerator, Coroutine
from enum import Enum
import math


class LoadPattern(Enum):
    """Different load testing patterns."""
    CONSTANT = "constant"
    RAMP_UP = "ramp_up"
    SPIKE = "spike"
    STEP = "step"
    WAVE = "wave"


@dataclass
class LoadConfig:
    """Configuration for load testing."""
    pattern: LoadPattern
    duration_seconds: int
    max_concurrent_requests: int
    requests_per_second: Optional[float] = None
    ramp_up_seconds: Optional[int] = None
    spike_multiplier: Optional[float] = None
    step_size: Optional[int] = None
    step_duration_seconds: Optional[int] = None
    wave_period_seconds: Optional[int] = None


class LoadGenerator:
    """Generates load based on different patterns."""
    
    def __init__(self, config: LoadConfig):
        self.config = config
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def generate_load(self, 
                           task_factory: Callable[[], Coroutine],
                           progress_callback: Optional[Callable[[int, int, float], None]] = None):
        """
        Generate load according to the configured pattern.
        
        Args:
            task_factory: Function that returns a coroutine to execute
            progress_callback: Optional callback for progress updates (completed, total, rate)
        """
        self._running = True
        start_time = time.time()
        
        try:
            if self.config.pattern == LoadPattern.CONSTANT:
                await self._constant_load(task_factory, progress_callback, start_time)
            elif self.config.pattern == LoadPattern.RAMP_UP:
                await self._ramp_up_load(task_factory, progress_callback, start_time)
            elif self.config.pattern == LoadPattern.SPIKE:
                await self._spike_load(task_factory, progress_callback, start_time)
            elif self.config.pattern == LoadPattern.STEP:
                await self._step_load(task_factory, progress_callback, start_time)
            elif self.config.pattern == LoadPattern.WAVE:
                await self._wave_load(task_factory, progress_callback, start_time)
        finally:
            self._running = False
            await self._wait_for_completion()
    
    async def _constant_load(self, task_factory, progress_callback, start_time):
        """Generate constant load."""
        if not self.config.requests_per_second:
            # Burst mode - create all tasks at once
            await self._burst_requests(
                self.config.max_concurrent_requests,
                task_factory,
                progress_callback
            )
        else:
            # Rate-limited mode
            await self._rate_limited_requests(
                self.config.requests_per_second,
                self.config.duration_seconds,
                task_factory,
                progress_callback,
                start_time
            )
    
    async def _ramp_up_load(self, task_factory, progress_callback, start_time):
        """Generate ramping load from 0 to max over ramp_up_seconds."""
        ramp_duration = self.config.ramp_up_seconds or 60
        max_rps = self.config.requests_per_second or (self.config.max_concurrent_requests / 10)
        
        ramp_end_time = start_time + ramp_duration
        test_end_time = start_time + self.config.duration_seconds
        
        completed = 0
        
        while time.time() < test_end_time and self._running:
            current_time = time.time()
            
            if current_time < ramp_end_time:
                # Ramping phase
                progress = (current_time - start_time) / ramp_duration
                current_rps = max_rps * progress
            else:
                # Steady state
                current_rps = max_rps
            
            if current_rps > 0:
                # Calculate delay between requests
                interval = 1.0 / current_rps
                
                # Create task if we have capacity
                if len(self._tasks) < self.config.max_concurrent_requests:
                    task = asyncio.create_task(self._execute_with_tracking(task_factory()))
                    self._tasks.append(task)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, -1, current_rps)
                
                await asyncio.sleep(interval)
            else:
                await asyncio.sleep(0.1)
    
    async def _spike_load(self, task_factory, progress_callback, start_time):
        """Generate spike load pattern."""
        normal_rps = self.config.requests_per_second or 10
        spike_rps = normal_rps * (self.config.spike_multiplier or 5)
        spike_duration = 30  # 30 second spikes
        
        end_time = start_time + self.config.duration_seconds
        next_spike_time = start_time + random.randint(60, 120)
        
        completed = 0
        
        while time.time() < end_time and self._running:
            current_time = time.time()
            
            # Determine if we're in a spike
            if (next_spike_time <= current_time <= next_spike_time + spike_duration):
                current_rps = spike_rps
                if current_time > next_spike_time + spike_duration:
                    # Schedule next spike
                    next_spike_time = current_time + random.randint(60, 180)
            else:
                current_rps = normal_rps
            
            # Execute request
            if len(self._tasks) < self.config.max_concurrent_requests:
                task = asyncio.create_task(self._execute_with_tracking(task_factory()))
                self._tasks.append(task)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, -1, current_rps)
            
            await asyncio.sleep(1.0 / current_rps)
    
    async def _step_load(self, task_factory, progress_callback, start_time):
        """Generate stepped load pattern."""
        step_size = self.config.step_size or 10
        step_duration = self.config.step_duration_seconds or 60
        base_rps = self.config.requests_per_second or 10
        
        end_time = start_time + self.config.duration_seconds
        step_start_time = start_time
        current_step = 0
        completed = 0
        
        while time.time() < end_time and self._running:
            current_time = time.time()
            
            # Check if we should move to next step
            if current_time >= step_start_time + step_duration:
                current_step += 1
                step_start_time = current_time
            
            current_rps = base_rps + (current_step * step_size)
            current_rps = min(current_rps, self.config.max_concurrent_requests)
            
            # Execute request
            if len(self._tasks) < self.config.max_concurrent_requests:
                task = asyncio.create_task(self._execute_with_tracking(task_factory()))
                self._tasks.append(task)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, -1, current_rps)
            
            await asyncio.sleep(1.0 / current_rps if current_rps > 0 else 0.1)
    
    async def _wave_load(self, task_factory, progress_callback, start_time):
        """Generate wave load pattern."""
        period = self.config.wave_period_seconds or 120
        base_rps = self.config.requests_per_second or 10
        amplitude = base_rps * 0.8  # Wave varies from 20% to 180% of base
        
        end_time = start_time + self.config.duration_seconds
        completed = 0
        
        while time.time() < end_time and self._running:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Calculate wave position (sine wave)
            wave_position = math.sin(2 * math.pi * elapsed / period)
            current_rps = base_rps + (amplitude * wave_position)
            current_rps = max(1, current_rps)  # Ensure positive
            
            # Execute request
            if len(self._tasks) < self.config.max_concurrent_requests:
                task = asyncio.create_task(self._execute_with_tracking(task_factory()))
                self._tasks.append(task)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, -1, current_rps)
            
            await asyncio.sleep(1.0 / current_rps)
    
    async def _rate_limited_requests(self, rps, duration, task_factory, progress_callback, start_time):
        """Generate requests at a specific rate."""
        interval = 1.0 / rps
        end_time = start_time + duration
        completed = 0
        
        while time.time() < end_time and self._running:
            if len(self._tasks) < self.config.max_concurrent_requests:
                task = asyncio.create_task(self._execute_with_tracking(task_factory()))
                self._tasks.append(task)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, int(rps * duration), rps)
            
            await asyncio.sleep(interval)
    
    async def _burst_requests(self, count, task_factory, progress_callback):
        """Generate a burst of requests."""
        for i in range(count):
            if not self._running:
                break
                
            task = asyncio.create_task(self._execute_with_tracking(task_factory()))
            self._tasks.append(task)
            
            if progress_callback:
                progress_callback(i + 1, count, -1)
            
            # Small delay to prevent overwhelming
            if i % 100 == 0:
                await asyncio.sleep(0.01)
    
    async def _execute_with_tracking(self, coro):
        """Execute a coroutine and track its completion."""
        try:
            return await coro
        finally:
            # Remove completed task from tracking
            current_task = asyncio.current_task()
            if current_task in self._tasks:
                self._tasks.remove(current_task)
    
    async def _wait_for_completion(self):
        """Wait for all tasks to complete."""
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
    
    def stop(self):
        """Stop load generation."""
        self._running = False


class ScenarioRunner:
    """Runs load testing scenarios with different configurations."""
    
    def __init__(self, name: str):
        self.name = name
        self.scenarios: List[Dict[str, Any]] = []
    
    def add_scenario(self, name: str, config: LoadConfig, 
                    task_factory: Callable[[], Coroutine],
                    description: str = ""):
        """Add a scenario to run."""
        self.scenarios.append({
            'name': name,
            'config': config,
            'task_factory': task_factory,
            'description': description
        })
    
    async def run_all_scenarios(self, 
                               metrics_collector,
                               progress_callback: Optional[Callable] = None):
        """Run all scenarios sequentially."""
        results = []
        
        for i, scenario in enumerate(self.scenarios):
            print(f"\nRunning scenario {i+1}/{len(self.scenarios)}: {scenario['name']}")
            if scenario['description']:
                print(f"Description: {scenario['description']}")
            
            # Clear previous metrics
            metrics_collector.clear_metrics()
            
            # Start metrics collection
            metrics_collector.start_collection()
            
            try:
                # Run the load generator
                generator = LoadGenerator(scenario['config'])
                
                def scenario_progress(completed, total, rate):
                    if progress_callback:
                        progress_callback(scenario['name'], completed, total, rate)
                    else:
                        if total > 0:
                            percent = (completed / total) * 100
                            print(f"\rProgress: {completed}/{total} ({percent:.1f}%) @ {rate:.1f} req/s", end='')
                        else:
                            print(f"\rCompleted: {completed} @ {rate:.1f} req/s", end='')
                
                await generator.generate_load(
                    scenario['task_factory'],
                    scenario_progress
                )
                
                print()  # New line after progress
                
            finally:
                metrics_collector.stop_collection()
            
            # Generate summary
            summary = metrics_collector.get_summary(scenario['name'])
            results.append(summary)
            
            # Brief wait between scenarios
            await asyncio.sleep(2)
        
        return results


def create_load_configs() -> Dict[str, LoadConfig]:
    """Create predefined load testing configurations."""
    return {
        'smoke': LoadConfig(
            pattern=LoadPattern.CONSTANT,
            duration_seconds=30,
            max_concurrent_requests=5,
            requests_per_second=2
        ),
        
        'light': LoadConfig(
            pattern=LoadPattern.CONSTANT,
            duration_seconds=60,
            max_concurrent_requests=20,
            requests_per_second=10
        ),
        
        'moderate': LoadConfig(
            pattern=LoadPattern.CONSTANT,
            duration_seconds=120,
            max_concurrent_requests=50,
            requests_per_second=25
        ),
        
        'heavy': LoadConfig(
            pattern=LoadPattern.CONSTANT,
            duration_seconds=180,
            max_concurrent_requests=100,
            requests_per_second=50
        ),
        
        'ramp_up': LoadConfig(
            pattern=LoadPattern.RAMP_UP,
            duration_seconds=300,
            max_concurrent_requests=100,
            requests_per_second=50,
            ramp_up_seconds=120
        ),
        
        'spike': LoadConfig(
            pattern=LoadPattern.SPIKE,
            duration_seconds=300,
            max_concurrent_requests=200,
            requests_per_second=20,
            spike_multiplier=5
        ),
        
        'step': LoadConfig(
            pattern=LoadPattern.STEP,
            duration_seconds=600,
            max_concurrent_requests=200,
            requests_per_second=10,
            step_size=10,
            step_duration_seconds=60
        ),
        
        'wave': LoadConfig(
            pattern=LoadPattern.WAVE,
            duration_seconds=600,
            max_concurrent_requests=150,
            requests_per_second=30,
            wave_period_seconds=120
        ),
        
        'burst': LoadConfig(
            pattern=LoadPattern.CONSTANT,
            duration_seconds=60,
            max_concurrent_requests=1000,
            # No RPS limit - burst mode
        ),
        
        'endurance': LoadConfig(
            pattern=LoadPattern.CONSTANT,
            duration_seconds=1800,  # 30 minutes
            max_concurrent_requests=50,
            requests_per_second=20
        )
    }