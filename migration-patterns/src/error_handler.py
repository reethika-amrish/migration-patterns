"""Error classification — categorizes migration errors as retryable vs permanent."""


ERROR_CATALOG = {
    "THROTTLED": {"retryable": True, "category": "rate_limit", "action": "backoff_retry"},
    "TIMEOUT": {"retryable": True, "category": "transient", "action": "retry"},
    "SERVICE_UNAVAILABLE": {"retryable": True, "category": "transient", "action": "retry"},
    "PERMISSION_DENIED": {"retryable": False, "category": "auth", "action": "escalate"},
    "NOT_FOUND": {"retryable": False, "category": "missing", "action": "skip_log"},
    "CONFLICT": {"retryable": False, "category": "data", "action": "manual_review"},
    "QUOTA_EXCEEDED": {"retryable": True, "category": "rate_limit", "action": "backoff_retry"},
    "INVALID_DATA": {"retryable": False, "category": "validation", "action": "skip_log"},
}


def classify_error(error_code: str) -> dict:
    """Classify an error code and return handling instructions."""
    if error_code in ERROR_CATALOG:
        return {"error": error_code, **ERROR_CATALOG[error_code]}
    return {"error": error_code, "retryable": False, "category": "unknown", "action": "manual_review"}


def should_retry(error_code: str) -> bool:
    return classify_error(error_code)["retryable"]


def get_retry_delay(attempt: int, error_code: str) -> float:
    """Exponential backoff with jitter for retryable errors."""
    import random
    base = 1.0
    if classify_error(error_code).get("action") == "backoff_retry":
        base = 2.0
    delay = base * (2 ** (attempt - 1))
    jitter = random.uniform(0, delay * 0.3)
    return delay + jitter
