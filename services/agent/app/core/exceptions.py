"""Domain and application exceptions."""


class OpportunityRadarError(Exception):
    """Base exception for all OpportunityRadar errors."""

    pass


class ResearchTaskNotFoundError(OpportunityRadarError):
    """Raised when a research task cannot be found."""

    pass


class ResearchTaskStateError(OpportunityRadarError):
    """Raised when an operation conflicts with current task state."""

    pass


class PlatformAdapterError(OpportunityRadarError):
    """Raised when a platform adapter fails."""

    pass


class BrowserWorkerError(OpportunityRadarError):
    """Raised when the browser worker encounters an error."""

    pass


class LLMProviderError(OpportunityRadarError):
    """Raised when the LLM provider fails."""

    pass
