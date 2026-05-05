"""Real-time progress tracking for migration jobs."""

from datetime import datetime


class ProgressTracker:
    """Tracks migration progress with per-entity stats and ETA estimation."""

    def __init__(self, total_items: int, entity_types: list = None):
        self.total = total_items
        self.processed = 0
        self.succeeded = 0
        self.failed = 0
        self.start_time = datetime.now()
        self.entity_progress = {e: {"total": 0, "done": 0} for e in (entity_types or [])}
        self.log = []

    def update(self, count: int = 1, success: bool = True, entity_type: str = None):
        self.processed += count
        if success:
            self.succeeded += count
        else:
            self.failed += count
        if entity_type and entity_type in self.entity_progress:
            self.entity_progress[entity_type]["done"] += count

    def set_entity_total(self, entity_type: str, total: int):
        self.entity_progress[entity_type] = {"total": total, "done": 0}

    def get_status(self) -> dict:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.processed / elapsed if elapsed > 0 else 0
        remaining = (self.total - self.processed) / rate if rate > 0 else 0

        return {
            "progress": f"{self.processed}/{self.total} ({self._pct()}%)",
            "succeeded": self.succeeded,
            "failed": self.failed,
            "elapsed_sec": round(elapsed, 1),
            "rate_per_sec": round(rate, 2),
            "eta_sec": round(remaining, 1),
            "entities": {
                k: f"{v['done']}/{v['total']}" for k, v in self.entity_progress.items()
            }
        }

    def _pct(self) -> str:
        return f"{(self.processed / self.total * 100):.1f}" if self.total else "0.0"

    def render_bar(self, width: int = 40) -> str:
        filled = int(width * self.processed / self.total) if self.total else 0
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {self._pct()}%  ({self.processed}/{self.total})"
