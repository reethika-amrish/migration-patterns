"""
Migration Patterns Demo — End-to-end migration simulation.

Demonstrates:
  1. Entitlement mapping across tenants
  2. Batch processing with retry
  3. Checkpoint-based rollback
  4. Progress tracking
  5. Error classification

Run: python -m src.migration_demo
"""

import random
from .entitlement import EntitlementMapper, SOURCE_PERMISSIONS
from .batch_processor import BatchProcessor
from .progress import ProgressTracker


def generate_mock_items(count: int = 500) -> list:
    """Generate mock migration items (Teams channels, SharePoint sites, users)."""
    entity_types = ["teams_channel", "sharepoint_site", "user_mailbox", "onedrive"]
    departments = ["Engineering", "Marketing", "Finance", "HR", "Legal"]

    items = []
    for i in range(count):
        items.append({
            "id": f"item-{i:05d}",
            "type": random.choice(entity_types),
            "name": f"Resource-{i}",
            "department": random.choice(departments),
            "size_mb": random.randint(1, 5000),
        })
    return items


def run_demo():
    print("=" * 60)
    print("  Cross-Tenant Migration Demo")
    print("  Patterns from 10,000+ user enterprise migration")
    print("=" * 60)

    # --- Step 1: Entitlement Mapping ---
    print("\n📋 Step 1: Entitlement Mapping")
    print("-" * 40)
    mapper = EntitlementMapper()
    result = mapper.map_all(SOURCE_PERMISSIONS)
    print(f"  Mapped {result['total_mapped']} users")
    print(f"  Conflicts: {result['total_conflicts']}")
    for ctype, count in result["conflict_types"].items():
        print(f"    - {ctype}: {count}")
    for m in result["mappings"]:
        print(f"  {m['user_id']}: {m['source_role']} → {m['target_role']} | groups: {m['target_groups']}")

    # --- Step 2: Batch Processing with Checkpoints ---
    print("\n📦 Step 2: Batch Processing (500 items, batch_size=100)")
    print("-" * 40)
    items = generate_mock_items(500)
    processor = BatchProcessor(batch_size=100, max_retries=3)

    # Track progress
    tracker = ProgressTracker(len(items), ["teams_channel", "sharepoint_site", "user_mailbox", "onedrive"])
    for etype in ["teams_channel", "sharepoint_site", "user_mailbox", "onedrive"]:
        tracker.set_entity_total(etype, sum(1 for it in items if it["type"] == etype))

    batch_results = processor.process_all(items)

    tracker.processed = batch_results["stats"]["migrated"] + batch_results["stats"]["failed"]
    tracker.succeeded = batch_results["stats"]["migrated"]
    tracker.failed = batch_results["stats"]["failed"]

    print(f"\n  {tracker.render_bar()}")
    status = tracker.get_status()
    print(f"  Succeeded: {status['succeeded']} | Failed: {status['failed']}")
    print(f"  Retries: {batch_results['stats']['retried']}")
    print(f"  Checkpoints: {batch_results['checkpoints']['total_checkpoints']}")

    # --- Step 3: Demonstrate Rollback ---
    print("\n🔄 Step 3: Checkpoint Rollback Demo")
    print("-" * 40)
    cp_mgr = processor.checkpoint_mgr
    if len(cp_mgr.checkpoints) >= 2:
        print(f"  Current checkpoint: {cp_mgr.current['id']}")
        rollback_result = cp_mgr.rollback()
        if rollback_result["success"]:
            print(f"  Rolled back to: {rollback_result['rolled_back_to']}")
            print(f"  Batches reverted: {rollback_result['batches_reverted']}")
            print(f"  Items to reprocess: {rollback_result['items_to_reprocess']}")
        resume = cp_mgr.get_resume_point()
        if resume:
            print(f"  Resume from: batch={resume['last_batch']}, item={resume['last_item_id']}")
    else:
        print("  (Not enough checkpoints to demo rollback)")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("  Migration Complete")
    print(f"  Total migrated: {batch_results['stats']['migrated']}")
    print(f"  Total failed: {batch_results['stats']['failed']}")
    print(f"  Checkpoints saved: {batch_results['checkpoints']['total_checkpoints']}")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
