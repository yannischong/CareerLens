from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequirementMention:
    requirement_type: str
    raw_text: str
    normalized_text: str
    requirement_level: str
    rule_name: str
    structured_value: dict[str, Any] = field(
        default_factory=dict
    )