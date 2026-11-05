"""
Severity Classification Engine

Classifies findings according to their potential impact on API consumers.
Per §6.2 of specification: Responsible for classifying findings according to their potential impact.
"""

from enum import Enum
from typing import Optional


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


def classify_finding(
    change_type: str,
    json_path: str,
    expected: Optional[str] = None,
    actual: Optional[str] = None,
    is_required_field: bool = False,
) -> Severity:
    """
    Classify a finding based on its change type and context.
    
    Rules per specification:
    - CRITICAL: Required field missing, type change on required field
    - HIGH: Type change (non-required), field removed (non-required)
    - MEDIUM: Field added (unexpected)
    - LOW: Value change within same type
    - INFO: Metadata changes, minor additions
    """
    
    # Critical: Required field issues
    if is_required_field:
        if change_type == "field_missing":
            return Severity.CRITICAL
        if change_type == "type_changed":
            return Severity.CRITICAL
        if change_type == "unexpected_null":
            return Severity.CRITICAL
    
    # High: Structural breaking changes
    if change_type == "type_changed":
        return Severity.HIGH
    if change_type == "field_missing":
        return Severity.HIGH
    if change_type == "field_removed":  # alias for field_missing
        return Severity.HIGH
    
    # Medium: Unexpected additions
    if change_type == "field_added":
        return Severity.MEDIUM
    if change_type == "unexpected_field":
        return Severity.MEDIUM
    
    # Low: Value changes (non-structural)
    if change_type == "value_changed":
        return Severity.LOW
    
    # Info: Everything else
    return Severity.INFO


def get_severity_priority(severity: Severity) -> int:
    """Get numeric priority for sorting (higher = more severe)."""
    priorities = {
        Severity.CRITICAL: 5,
        Severity.HIGH: 4,
        Severity.MEDIUM: 3,
        Severity.LOW: 2,
        Severity.INFO: 1,
    }
    return priorities.get(severity, 0)


def is_breaking_change(severity: Severity) -> bool:
    """Determine if a severity level represents a breaking change."""
    return severity in (Severity.CRITICAL, Severity.HIGH)