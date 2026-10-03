"""Profiling timing utility for VisionIQ.

Active only when environment variable PROFILE_TIMING=1 is set.
Logging only; zero overhead when PROFILE_TIMING is unset or not '1'.
"""

from contextlib import contextmanager
import logging
import os
import time
from typing import Dict, List, Optional

logger = logging.getLogger("visioniq.timing")

# Global collector for latency benchmarking and analysis
_COLLECTOR: Optional[Dict[str, List[float]]] = None


def set_timing_collector(collector_dict: Optional[Dict[str, List[float]]]):
    """Sets a dictionary to collect elapsed seconds per stage."""
    global _COLLECTOR
    _COLLECTOR = collector_dict


@contextmanager
def profile_timer(stage_name: str, collector: Optional[Dict[str, List[float]]] = None):
    """Context manager to measure and log execution time of a stage behind PROFILE_TIMING=1."""
    if os.getenv("PROFILE_TIMING") == "1":
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            logger.info(f"[PROFILE_TIMING] {stage_name}: {elapsed:.4f}s")
            target = collector if collector is not None else _COLLECTOR
            if target is not None:
                target.setdefault(stage_name, []).append(elapsed)
    else:
        yield
