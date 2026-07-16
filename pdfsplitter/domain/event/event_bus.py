from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, ClassVar

logger = logging.getLogger(__name__)

EventHandler = Callable[["Event"], None]


@dataclass(frozen=True)
class Event(ABC):
    """事件基类.

    所有领域事件必须继承自此类.
    子类使用 frozen=True dataclass 确保不可变性.

    Attributes:
        source: 事件来源标识.
    """

    source: str = ""


class EventBus:
    """独立于 Qt 的轻量事件总线.

    支持同步事件发布/订阅模式.
    线程安全 (简单实现，依赖 GIL).
    """

    _instance: ClassVar[EventBus | None] = None

    def __init__(self) -> None:
        self._handlers: dict[type[Event], list[EventHandler]] = {}

    @classmethod
    def instance(cls) -> EventBus:
        """获取全局单例."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置单例 (主要用于测试)."""
        cls._instance = None

    def subscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        """订阅事件.

        Args:
            event_type: 要订阅的事件类型.
            handler: 事件处理回调.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("EventBus: subscribed to %s", event_type.__name__)

    def unsubscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        """取消订阅.

        Args:
            event_type: 事件类型.
            handler: 要移除的处理回调.
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug("EventBus: unsubscribed from %s", event_type.__name__)
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        """同步发布事件.

        Args:
            event: 事件实例.
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        logger.debug("EventBus: publishing %s to %d handlers", event_type.__name__, len(handlers))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception("EventBus: handler for %s raised exception", event_type.__name__)

    def clear(self) -> None:
        """清除所有订阅."""
        self._handlers.clear()
        logger.debug("EventBus: cleared all handlers")
