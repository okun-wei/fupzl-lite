class LiteFuPZLError(Exception):
    """Base exception for all LiteFuPZL errors."""
    pass

class RecoverableError(LiteFuPZLError):
    """Errors that can be retried (page timeout, element not found)."""
    pass

class RateLimitedError(LiteFuPZLError):
    """HTTP 429 rate limit errors."""
    pass

class SessionFatalError(LiteFuPZLError):
    """Errors that end the current session (cookie expired, account banned)."""
    pass

class SystemFatalError(LiteFuPZLError):
    """Errors that end all tasks (browser crash, DB connection lost)."""
    pass
