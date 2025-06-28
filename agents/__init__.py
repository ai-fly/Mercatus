"""Compatibility layer providing minimal stubs so existing code that imported
`agents` continues to run after migration away from the original OpenAI-agents
package.

Only the symbols used in this repository are implemented:
• Agent – exposes `.as_tool()` returning the wrapped coroutine.
• RunContextWrapper – simple container giving `.context` attribute.
• function_tool – decorator that stores a custom `tool_name` attribute.

Everything else can be added later as required.
"""
from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar, Awaitable, Coroutine
import functools

__all__ = [
    "Agent",
    "RunContextWrapper",
    "function_tool",
]

T = TypeVar("T")


class RunContextWrapper(Generic[T]):
    """Very small wrapper used by prompt helpers to access the context object."""

    def __init__(self, context: T):
        self.context: T = context

    # representation helpful in logs/debugging
    def __repr__(self) -> str:  # pragma: no cover
        return f"RunContextWrapper({self.context!r})"


# ---------------------------------------------------------------------------
# Minimal replacement for the old `@function_tool` decorator.
# It does **nothing** except keep metadata so other libraries can introspect.
# ---------------------------------------------------------------------------

def function_tool(name_override: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that tags a callable as a tool.

    The wrapped function is returned unchanged, but gets two helpful
    attributes: `tool_name` (the public name) and `is_function_tool = True`.
    """

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        setattr(fn, "tool_name", name_override or fn.__name__)
        setattr(fn, "is_function_tool", True)
        return fn

    return _decorator


# ---------------------------------------------------------------------------
# Extremely light-weight Agent stub, only covering what this codebase needs.
# ---------------------------------------------------------------------------

class Agent:
    """Stub replacement so constructs like `Agent(...).as_tool()` work.

    The real execution is delegated elsewhere (e.g. via LangGraph).  For now
    we just expose an `as_tool` method that returns the provided coroutine so
    the rest of the code can import it and keep running.
    """

    def __init__(self, *_, **__):  # pylint: disable=unused-argument
        pass

    async def _dummy(self, *_, **__) -> str:  # pragma: no cover
        return "Agent stub – implement real logic later."

    def as_tool(self, tool_name: str, tool_description: str) -> Callable[..., Coroutine[Any, Any, str]]:
        """Return an async function that simply calls the dummy implementation."""

        @functools.wraps(self._dummy)
        async def _tool(*args: Any, **kwargs: Any) -> str:  # noqa: D401
            return await self._dummy(*args, **kwargs)

        _tool.__name__ = tool_name  # type: ignore[attr-defined]
        _tool.__doc__ = tool_description  # type: ignore[attr-defined]
        return _tool 