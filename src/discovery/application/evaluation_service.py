
from typing import Any


REQUIRED_SECTIONS = (
    "meeting_summary",
    "functional_requirements",
    "non_functional_requirements",
    "user_stories",
    "open_questions",
    "dependencies",
    "risks",
)


def validate_discovery_output(
    result: dict[str, Any],
) -> dict[str, Any]:
    """Validate the basic structure of a discovery result."""
    errors: list[str] = []
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in result:
            errors.append(f"Missing required section: {section}")

    for section in REQUIRED_SECTIONS:
        if section not in result:
            continue

        value = result[section]

        if section == "meeting_summary":
            if not isinstance(value, (str, dict, list)):
                errors.append(
                    "meeting_summary must be a string, object, or list."
                )
            continue

        if not isinstance(value, list):
            errors.append(f"{section} must be a list.")
            continue

        for index, item in enumerate(value):
            location = f"{section}[{index}]"

            if not isinstance(item, dict):
                errors.append(f"{location} must be an object.")
                continue

            if section in (
                "functional_requirements",
                "non_functional_requirements",
            ):
                if not any(
                    item.get(key)
                    for key in ("description", "requirement", "title")
                ):
                    errors.append(
                        f"{location} has no requirement description."
                    )

                if not item.get("evidence"):
                    warnings.append(
                        f"{location} has no supporting evidence."
                    )

            elif section == "user_stories":
                if not item.get("acceptance_criteria"):
                    warnings.append(
                        f"{location} has no acceptance criteria."
                    )

                if not item.get("evidence"):
                    warnings.append(
                        f"{location} has no supporting evidence."
                    )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
