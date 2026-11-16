"""Error types shared across the package."""


class ToolError(Exception):
    """A tool could not do its job (bad input, timeout, unsupported case)."""


class BrainError(Exception):
    """The brain (LLM adapter) failed (unreachable, malformed reply)."""
