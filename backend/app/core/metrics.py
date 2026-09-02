"""Lightweight in-memory metrics helpers."""
from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Any, Dict, Tuple

LabelItems = Tuple[Tuple[str, str], ...]


class MetricsRegistry:
    """Simple counter registry safe for single-process usage."""

    def __init__(self) -> None:
        self._counters: Dict[str, Dict[LabelItems, int]] = defaultdict(dict)
        self._lock = Lock()

    def increment(self, name: str, *, labels: Dict[str, str] | None = None, value: int = 1) -> None:
        label_key = self._normalize_labels(labels)
        with self._lock:
            current = self._counters.setdefault(name, {})
            current[label_key] = current.get(label_key, 0) + value

    def snapshot(self, prefix: str | None = None) -> Dict[str, list[Dict[str, Any]]]:
        with self._lock:
            result: Dict[str, list[Dict[str, Any]]] = {}
            for metric_name, label_map in self._counters.items():
                if prefix and not metric_name.startswith(prefix):
                    continue
                result[metric_name] = [
                    {"labels": dict(labels), "value": value}
                    for labels, value in label_map.items()
                ]
            return result

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()

    @staticmethod
    def _normalize_labels(labels: Dict[str, str] | None) -> LabelItems:
        if not labels:
            return tuple()
        return tuple(sorted(labels.items()))


_registry = MetricsRegistry()


def increment_counter(name: str, *, labels: Dict[str, str] | None = None, value: int = 1) -> None:
    """Increment a named metric counter."""

    _registry.increment(name, labels=labels, value=value)


def get_metrics_snapshot(prefix: str | None = None) -> Dict[str, list[Dict[str, Any]]]:
    """Return a serializable snapshot of accumulated metrics."""

    return _registry.snapshot(prefix=prefix)


def reset_metrics() -> None:
    """Reset all tracked metrics (useful for tests)."""

    _registry.reset()
