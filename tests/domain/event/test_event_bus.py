from __future__ import annotations

from dataclasses import dataclass

import pytest

from pdfsplitter.domain.event.event_bus import Event, EventBus


@dataclass(frozen=True)
class TestEvent(Event):
    message: str = ""


@dataclass(frozen=True)
class OtherEvent(Event):
    value: int = 0


class TestEventBus:
    """EventBus 测试套件."""

    def setup_method(self) -> None:
        EventBus.reset()

    def test_singleton(self) -> None:
        bus1 = EventBus.instance()
        bus2 = EventBus.instance()
        assert bus1 is bus2

    def test_subscribe_and_publish(self) -> None:
        received: list[str] = []

        def handler(event: Event) -> None:
            assert isinstance(event, TestEvent)
            received.append(event.message)

        bus = EventBus.instance()
        bus.subscribe(TestEvent, handler)
        bus.publish(TestEvent(message="hello"))
        assert received == ["hello"]

    def test_multiple_handlers(self) -> None:
        results: list[str] = []

        def handler_a(event: Event) -> None:
            results.append("a")

        def handler_b(event: Event) -> None:
            results.append("b")

        bus = EventBus.instance()
        bus.subscribe(TestEvent, handler_a)
        bus.subscribe(TestEvent, handler_b)
        bus.publish(TestEvent())
        assert "a" in results
        assert "b" in results

    def test_unsubscribe(self) -> None:
        received: list[str] = []

        def handler(event: Event) -> None:
            received.append("x")

        bus = EventBus.instance()
        bus.subscribe(TestEvent, handler)
        bus.publish(TestEvent())
        assert len(received) == 1

        bus.unsubscribe(TestEvent, handler)
        bus.publish(TestEvent())
        assert len(received) == 1

    def test_different_event_types(self) -> None:
        test_received: list[str] = []
        other_received: list[int] = []

        def test_handler(event: Event) -> None:
            assert isinstance(event, TestEvent)
            test_received.append("t")

        def other_handler(event: Event) -> None:
            assert isinstance(event, OtherEvent)
            other_received.append(1)

        bus = EventBus.instance()
        bus.subscribe(TestEvent, test_handler)
        bus.subscribe(OtherEvent, other_handler)

        bus.publish(TestEvent())
        assert len(test_received) == 1
        assert len(other_received) == 0

        bus.publish(OtherEvent())
        assert len(test_received) == 1
        assert len(other_received) == 1

    def test_handler_exception_is_caught(self) -> None:
        results: list[str] = []

        def bad_handler(event: Event) -> None:
            raise RuntimeError("test error")

        def good_handler(event: Event) -> None:
            results.append("ok")

        bus = EventBus.instance()
        bus.subscribe(TestEvent, bad_handler)
        bus.subscribe(TestEvent, good_handler)
        bus.publish(TestEvent())
        assert results == ["ok"]

    def test_clear(self) -> None:
        received: list[str] = []

        def handler(event: Event) -> None:
            received.append("x")

        bus = EventBus.instance()
        bus.subscribe(TestEvent, handler)
        bus.clear()
        bus.publish(TestEvent())
        assert len(received) == 0

    def test_event_source(self) -> None:
        captured_source: list[str] = []

        def handler(event: Event) -> None:
            captured_source.append(event.source)

        bus = EventBus.instance()
        bus.subscribe(TestEvent, handler)
        bus.publish(TestEvent(source="test-source", message="hi"))
        assert captured_source == ["test-source"]
