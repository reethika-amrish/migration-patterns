"""Checkpoint system for migration rollback support."""

import json
from datetime import datetime


class CheckpointManager:
    """Saves and restores migration progress for rollback capability."""

    def __init__(self):
        self.checkpoints = []
        self.current = None

    def save(self, batch_id: str, migrated_items: list, stats: dict):
        """Save a checkpoint after a successful batch."""
        checkpoint = {
            "id": f"cp-{len(self.checkpoints):04d}",
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "items_migrated": len(migrated_items),
            "item_ids": [item["id"] for item in migrated_items],
            "stats": stats,
        }
        self.checkpoints.append(checkpoint)
        self.current = checkpoint
        return checkpoint

    def rollback(self, checkpoint_id: str = None):
        """Rollback to a specific checkpoint (or latest)."""
        if checkpoint_id:
            target = next((cp for cp in self.checkpoints if cp["id"] == checkpoint_id), None)
        else:
            target = self.checkpoints[-2] if len(self.checkpoints) > 1 else None

        if not target:
            return {"success": False, "message": "No checkpoint to rollback to"}

        # Remove all checkpoints after the target
        idx = self.checkpoints.index(target)
        removed = self.checkpoints[idx + 1:]
        self.checkpoints = self.checkpoints[:idx + 1]
        self.current = target

        return {
            "success": True,
            "rolled_back_to": target["id"],
            "batches_reverted": len(removed),
            "items_to_reprocess": sum(cp["items_migrated"] for cp in removed),
        }

    def get_resume_point(self):
        """Get the item ID to resume from after the last checkpoint."""
        if not self.current:
            return None
        return {
            "last_batch": self.current["batch_id"],
            "last_item_id": self.current["item_ids"][-1] if self.current["item_ids"] else None,
            "total_migrated": sum(cp["items_migrated"] for cp in self.checkpoints),
        }

    def summary(self):
        return {
            "total_checkpoints": len(self.checkpoints),
            "total_migrated": sum(cp["items_migrated"] for cp in self.checkpoints),
            "current": self.current["id"] if self.current else None,
        }
