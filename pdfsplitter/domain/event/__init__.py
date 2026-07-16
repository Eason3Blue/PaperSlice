"""Event module - 独立于 Qt 的轻量事件总线."""

from pdfsplitter.domain.event.event_bus import Event, EventBus, EventHandler

__all__ = ["Event", "EventBus", "EventHandler"]
