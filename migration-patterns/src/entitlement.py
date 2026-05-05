"""Entitlement mapping — maps permissions across tenants with conflict resolution."""


# Mock permission structures
SOURCE_PERMISSIONS = {
    "user-001": {"role": "Owner", "groups": ["Engineering", "All-Company"]},
    "user-002": {"role": "Member", "groups": ["Marketing", "All-Company"]},
    "user-003": {"role": "Owner", "groups": ["Engineering", "Leadership"]},
    "user-004": {"role": "Guest", "groups": ["External-Partners"]},
    "user-005": {"role": "Member", "groups": ["Engineering", "All-Company"]},
}

TARGET_GROUPS = {
    "Engineering": "eng-team-target",
    "Marketing": "mktg-team-target",
    "All-Company": "all-staff-target",
    "Leadership": "leadership-target",
}


class EntitlementMapper:
    """Maps source tenant permissions to target tenant with conflict resolution."""

    def __init__(self):
        self.mappings = []
        self.conflicts = []

    def map_user(self, user_id: str, source_perms: dict) -> dict:
        """Map a single user's permissions to the target tenant."""
        mapped_groups = []
        user_conflicts = []

        for group in source_perms.get("groups", []):
            if group in TARGET_GROUPS:
                mapped_groups.append(TARGET_GROUPS[group])
            else:
                user_conflicts.append({
                    "user": user_id,
                    "type": "unmapped_group",
                    "source_group": group,
                    "resolution": "skip"
                })

        # Role mapping with conflict detection
        role = source_perms.get("role", "Member")
        if role == "Guest":
            user_conflicts.append({
                "user": user_id,
                "type": "guest_access",
                "resolution": "external_sharing_policy"
            })

        mapping = {
            "user_id": user_id,
            "source_role": role,
            "target_role": role if role != "Guest" else "ExternalUser",
            "target_groups": mapped_groups,
            "conflicts": user_conflicts,
        }

        self.mappings.append(mapping)
        self.conflicts.extend(user_conflicts)
        return mapping

    def map_all(self, permissions: dict) -> dict:
        """Map all users and return summary."""
        for user_id, perms in permissions.items():
            self.map_user(user_id, perms)

        return {
            "total_mapped": len(self.mappings),
            "total_conflicts": len(self.conflicts),
            "conflict_types": self._summarize_conflicts(),
            "mappings": self.mappings,
        }

    def _summarize_conflicts(self):
        types = {}
        for c in self.conflicts:
            t = c["type"]
            types[t] = types.get(t, 0) + 1
        return types
