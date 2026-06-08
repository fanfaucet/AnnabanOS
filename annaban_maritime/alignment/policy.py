"""Named policies used by the alignment evaluator."""

from enum import Enum


class Policy(str, Enum):
    """Policy identifiers for maritime route constraints."""

    DO_NO_HARM = "do_no_harm"
    ECO_PROTECTION = "eco_protection"
    HUMANITARIAN_PRIORITY = "humanitarian_priority"
