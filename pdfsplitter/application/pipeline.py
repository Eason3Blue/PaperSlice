"""Pipeline module - 处理管线框架."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """管线上下文，在阶段间传递数据.

    Attributes:
        data: 阶段间共享的键值对数据.
    """

    data: dict[str, Any] = field(default_factory=dict)


class PipelineStage(ABC):
    """管线阶段抽象基类.

    每个阶段实现 process 方法，接收 PipelineContext 并返回修改后的 Context.
    """

    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """执行阶段处理逻辑.

        Args:
            context: 当前管线上下文.

        Returns:
            修改后的管线上下文.

        Raises:
            Exception: 阶段处理失败.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """阶段名称."""
        ...


class Pipeline:
    """可组合的处理管线.

    按顺序执行多个 PipelineStage.
    未来新增阶段 (Crop, Rotate, Scale) 无需修改已有代码.
    """

    def __init__(self) -> None:
        self._stages: list[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> Pipeline:
        """添加处理阶段 (链式调用).

        Args:
            stage: 管线阶段.

        Returns:
            self, 支持链式调用.
        """
        self._stages.append(stage)
        return self

    def execute(self, context: PipelineContext | None = None) -> PipelineContext:
        """执行管线.

        Args:
            context: 初始上下文, 若为 None 则创建空上下文.

        Returns:
            处理完毕的管线上下文.

        Raises:
            RuntimeError: 某阶段执行失败.
        """
        if context is None:
            context = PipelineContext()
        logger.info("Pipeline: executing %d stages", len(self._stages))
        for stage in self._stages:
            logger.debug("Pipeline: running stage '%s'", stage.name)
            try:
                context = stage.process(context)
            except Exception:
                logger.exception("Pipeline: stage '%s' failed", stage.name)
                raise
        logger.info("Pipeline: execution complete")
        return context
