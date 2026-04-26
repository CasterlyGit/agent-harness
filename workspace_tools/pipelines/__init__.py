"""Pre-baked pipeline shapes. Each is just a `list[Stage]`.

Adding a new shape:
  - Compose Stage instances from `workspace_tools.stages`
  - Or build a custom one inline
  - Pipeline doesn't care; it runs whatever ordered list you give it.
"""
from __future__ import annotations

from .. import stages as S
from ..core.stage import Stage


def sdd_brownfield() -> list[Stage]:
    """Full 7-stage SDD pipeline. For substantial features. ~10-20 min."""
    return [S.EXPLORE, S.RESEARCH, S.REQUIREMENTS, S.DESIGN,
            S.TEST_PLAN, S.IMPLEMENT, S.INTEGRATION_TEST]


def sdd_greenfield() -> list[Stage]:
    """Greenfield: skips explore (fresh repo). For /automate."""
    return [S.RESEARCH, S.REQUIREMENTS, S.DESIGN,
            S.TEST_PLAN, S.IMPLEMENT, S.INTEGRATION_TEST]


def quickfix() -> list[Stage]:
    """3-stage minimal pipeline for small bugs / polish. ~3-6 min.

    Skips RESEARCH, REQUIREMENTS, DESIGN, TEST_PLAN — the issue body itself
    serves as the spec. Goes straight from explore (so the agent knows the
    code) to implement to integration-test."""
    return [S.EXPLORE, S.IMPLEMENT, S.INTEGRATION_TEST]


def bugfix() -> list[Stage]:
    """5-stage compact pipeline. For real bugs that need a tiny spec. ~6-10 min.

    Skips REQUIREMENTS (issue body = spec) and TEST_PLAN (regression test
    inside implement). Keeps DESIGN because real bugs benefit from a
    documented theory of the fix."""
    return [S.EXPLORE, S.RESEARCH, S.DESIGN, S.IMPLEMENT, S.INTEGRATION_TEST]


SHAPES = {
    "full":       sdd_brownfield,
    "feature":    sdd_brownfield,
    "greenfield": sdd_greenfield,
    "bugfix":     bugfix,
    "bug":        bugfix,
    "quickfix":   quickfix,
    "polish":     quickfix,
    "chore":      quickfix,
}


def pick_shape(name: str | None, *, default: str = "full") -> list[Stage]:
    """Resolve a shape by name. Falls back to `default` if name is None / unknown."""
    if name and name.lower() in SHAPES:
        return SHAPES[name.lower()]()
    return SHAPES[default]()


def shape_for_issue(labels: list[str], body: str) -> str:
    """Heuristic — pick a sensible default shape from the issue's labels + body.

    Order of precedence:
      1. Explicit magic line in body: `pipeline: bugfix` (or feature/quickfix/etc.)
      2. Labels: bug+small → bugfix, polish/chore → quickfix, feature → full
      3. Body length: < 400 chars → quickfix, < 1500 → bugfix, else → full

    The orchestrator never picks for you silently — it logs the chosen shape
    so you see why it ran what it did."""
    import re
    m = re.search(r"^pipeline:\s*(\w+)\s*$", body or "", re.MULTILINE | re.IGNORECASE)
    if m and m.group(1).lower() in SHAPES:
        return m.group(1).lower()

    label_set = {l.lower() for l in labels}
    if "polish" in label_set or "chore" in label_set or "docs" in label_set:
        return "quickfix"
    if "bug" in label_set:
        return "bugfix"
    if "feature" in label_set:
        # Length-based escalation for features
        if len(body or "") < 600:
            return "bugfix"
        return "full"

    if len(body or "") < 400:
        return "quickfix"
    if len(body or "") < 1500:
        return "bugfix"
    return "full"


__all__ = [
    "sdd_brownfield", "sdd_greenfield", "quickfix", "bugfix",
    "SHAPES", "pick_shape", "shape_for_issue",
]
