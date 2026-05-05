"""Batch processor with retry logic and error classification."""

import random
from .checkpoint import CheckpointManager
from .error_handler import classify_error


class BatchProcessor:
    """Processes migration items in batches with checkpoint and retry support."""

    def __init__(self, batch_size: int = 100, max_retries: int = 3):
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.checkpoint_mgr = CheckpointManager()
        self.stats = {"migrated": 0, "failed": 0, "retried": 0, "skipped": 0}

    def process_batch(self, batch_id: str, items: list) -> dict:
        """Process a single batch of items with retry on retryable errors."""
        migrated = []
        failed = []

        for item in items:
            success = False
            for attempt in range(1, self.max_retries + 1):
                result = self._migrate_item(item)

                if result["success"]:
                    migrated.append(item)
                    self.stats["migrated"] += 1
                    success = True
                    break

                error_class = classify_error(result["error"])
                if error_class["retryable"] and attempt < self.max_retries:
                    self.stats["retried"] += 1
                    continue
                else:
                    failed.append({"item": item, "error": result["error"], "classification": error_class})
                    self.stats["failed"] += 1
                    break

        # Save checkpoint after successful batch
        if migrated:
            self.checkpoint_mgr.save(batch_id, migrated, dict(self.stats))

        return {
            "batch_id": batch_id,
            "migrated": len(migrated),
            "failed": len(failed),
            "failures": failed,
            "checkpoint": self.checkpoint_mgr.current,
        }

    def process_all(self, items: list) -> dict:
        """Process all items in batches."""
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_id = f"batch-{i // self.batch_size:04d}"
            result = self.process_batch(batch_id, batch)
            results.append(result)

        return {
            "total_batches": len(results),
            "stats": self.stats,
            "checkpoints": self.checkpoint_mgr.summary(),
        }

    def _migrate_item(self, item: dict) -> dict:
        """Simulate migrating a single item (90% success rate)."""
        if random.random() < 0.9:
            return {"success": True, "item_id": item["id"]}

        errors = ["THROTTLED", "TIMEOUT", "PERMISSION_DENIED", "NOT_FOUND", "CONFLICT"]
        return {"success": False, "error": random.choice(errors), "item_id": item["id"]}
