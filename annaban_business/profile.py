"""Canonical business profile used to tie modules back to the owner/operator."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BusinessProfile:
    """Public product ownership context for AnnabanOS integrations.

    This profile is intentionally operational: it identifies the business stack,
    products, and module fit without encoding private contact details or claiming
    external account verification.
    """

    owner: str = "Jacob Wayne Kinnaird"
    organization: str = "AnnabanAI"
    orchestration_platform: str = "SparkAI+"
    operating_system: str = "AnnabanOS"
    profile_version: str = "0.2.0"
    provenance: str = "local-project-declaration"
    verification_status: str = "UNVERIFIED"
    tagline: str = "Deterministic governance and simulation middleware for agentic AI systems."
    business_domains: tuple[str, ...] = (
        "AI governance middleware",
        "agent orchestration",
        "simulation systems",
        "logistics intelligence",
        "audit and safety tooling",
    )
    modules: dict[str, str] = field(
        default_factory=lambda: {
            "annaban_benchmark": "core governance, routing, constraints, signals, and audit ledger",
            "annaban_maritime": "logistics demonstrator for ETA, route scoring, and alignment checks",
            "iaftp": "local inter-agent artifact transfer emulation for planner/executor workflows",
            "spark_integration": "fictional local SparkAI+ node safety simulation with haptic interlock",
        }
    )

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the business profile."""

        return {
            "owner": self.owner,
            "organization": self.organization,
            "orchestration_platform": self.orchestration_platform,
            "operating_system": self.operating_system,
            "profile_version": self.profile_version,
            "provenance": self.provenance,
            "verification_status": self.verification_status,
            "tagline": self.tagline,
            "business_domains": list(self.business_domains),
            "modules": dict(self.modules),
        }


def get_business_profile() -> BusinessProfile:
    """Return the default Jacob Wayne Kinnaird business profile."""

    return BusinessProfile()
