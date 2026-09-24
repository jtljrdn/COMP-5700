"""
Identify violations of the IEEE principle "Use cryptography correctly."

T1 parse_yaml_content parses the user-story YAML.
T2 extract_violation_content pulls cryptography signals out of a requirement.
T3 lookup_violations decides which principles a requirement violates.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

STORY_PATH = Path(__file__).with_name("user_story.yaml")

PRINCIPLES = {
    "custom_crypto": (
        "Do not use your own cryptographic algorithms or implementations"
    ),
    "algorithm_misuse": "Misuse of libraries and algorithms",
    "poor_key_management": "Poor key management",
    "weak_randomness": "Randomness that is not random",
    "no_algorithm_agility": (
        "Failure to allow for algorithm adaptation and evolution"
    ),
}

# Evidence field -> principle key. lookup_violations walks this table.
FIELD_TO_PRINCIPLE = {
    "custom_implementation_phrases": "custom_crypto",
    "misuse_phrases": "algorithm_misuse",
    "poor_key_phrases": "poor_key_management",
    "weak_random_phrases": "weak_randomness",
    "agility_failure_phrases": "no_algorithm_agility",
}

VIOLATION_PATTERNS = {
    "custom_implementation_phrases": [
        r"\bour own implementation\b",
        r"\bown implementation\b",
        r"\bhome-?grown\b",
        r"\broll(?:ing)? our own\b",
    ],
    "misuse_phrases": [
        r"\bmd5\b",
        r"\bsha-?1\b",
        r"encrypt\w* all passwords",
        r"\bsha-?(?:256|512)\b[^.]*\bprotect\b",
    ],
    "poor_key_phrases": [
        r"\bhard-?coded keys?\b",
        r"\bkeys? in (?:the )?source\b",
        r"\bnever rotate\b",
        r"\bwill not be rotated\b",
        r"\bno key rotation\b",
        r"\bsame key forever\b",
    ],
    "weak_random_phrases": [
        r"\bfixed range between \d+ and \d+\b",
        r"\bfixed seed\b",
        r"\bmath\.random\b",
        r"\brand\(\)",
    ],
    "agility_failure_phrases": [
        r"\bnever change the algorithm\b",
        r"\bcannot be replaced\b",
        r"\bwill always use\b",
        r"\bwill not adopt\b",
        r"\bno algorithm changes\b",
    ],
}

CONTROL_PATTERNS = {
    "key_rotation_phrases": [
        r"\bkeys?\b[^.]*\brotated\b",
        r"\bkey rotation\b",
        r"\brotate keys\b",
    ],
    "adaptation_phrases": [
        r"\bnew cryptography algorithm\b",
        r"\bbetter strength\b",
        r"\binstead of (?:md5|sha-?\d+|aes|rsa)\b",
    ],
}

ALGORITHM_PATTERN = r"\b(?:MD5|SHA-?1|SHA-?256|SHA-?512|AES|RSA|DES|3DES)\b"
# Assignment YAML writes keys as ALL:"text" with no space after the colon.
KEY_VALUE_PATTERN = re.compile(r'([A-Za-z][A-Za-z0-9]*)\s*:\s*"([^"]*)"')


def _story_from_mapping(item: dict) -> dict[str, str]:
    return {
        str(key): "" if value is None else str(value) for key, value in item.items()
    }


def _stories_from_key_value_text(yaml_text: str) -> list[dict[str, str]]:
    """Parse KEY:"value" pairs when standard YAML does not see a mapping."""
    story = {}
    for key, value in KEY_VALUE_PATTERN.findall(yaml_text):
        story[key] = value
    if not story:
        raise ValueError("YAML root must be a mapping or a list of mappings")
    return [story]


def parse_yaml_content(yaml_text: str) -> list[dict[str, str]]:
    """T1. Parse user-story YAML into a list of requirement maps."""
    if yaml_text.strip() == "":
        return []

    loaded = yaml.safe_load(yaml_text)
    if loaded is None:
        return []

    if isinstance(loaded, dict):
        return [_story_from_mapping(loaded)]

    if isinstance(loaded, list):
        if loaded and all(isinstance(item, dict) for item in loaded):
            return [_story_from_mapping(item) for item in loaded]
        if all(isinstance(item, str) for item in loaded):
            return _stories_from_key_value_text(yaml_text)
        raise ValueError("YAML root must be a mapping or a list of mappings")

    if isinstance(loaded, str):
        return _stories_from_key_value_text(yaml_text)

    raise ValueError("YAML root must be a mapping or a list of mappings")


def load_user_story(path: Path = STORY_PATH) -> list[dict[str, str]]:
    """Read a YAML file from disk and parse it with parse_yaml_content."""
    return parse_yaml_content(path.read_text(encoding="utf-8"))


def _matching_phrases(text: str, patterns: list[str]) -> list[str]:
    """Return matched text, dropping a hit that is only part of a longer hit."""
    found = []
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            found.append(match.group(0))

    unique = []
    for phrase in sorted(found, key=len, reverse=True):
        if any(phrase.lower() in kept.lower() for kept in unique):
            continue
        unique.append(phrase)
    return unique


def _without_negated_rotation(phrases: list[str]) -> list[str]:
    """Drop rotation phrases that say the keys will not be rotated."""
    return [phrase for phrase in phrases if not re.search(r"\bnot\b", phrase, re.I)]


def extract_violation_content(text: str) -> dict:
    """T2. Extract cryptography content related to the five principles."""
    extracted = {
        "text": text,
        "algorithms": re.findall(ALGORITHM_PATTERN, text, flags=re.IGNORECASE),
    }
    for field, patterns in VIOLATION_PATTERNS.items():
        extracted[field] = _matching_phrases(text, patterns)
    for field, patterns in CONTROL_PATTERNS.items():
        extracted[field] = _matching_phrases(text, patterns)
    extracted["key_rotation_phrases"] = _without_negated_rotation(
        extracted["key_rotation_phrases"]
    )
    return extracted


def lookup_principle(principle_key: str) -> str:
    """Return the IEEE principle statement for a principle key."""
    return PRINCIPLES[principle_key]


def lookup_violations(
    requirements: dict[str, str], requirement_key: str
) -> list[dict]:
    """T3. Look up a requirement, then look up which principles it violates."""
    text = requirements[requirement_key]
    extracted = extract_violation_content(text)
    violations = []
    for evidence_field, principle_key in FIELD_TO_PRINCIPLE.items():
        evidence = extracted[evidence_field]
        if not evidence:
            continue
        violations.append(
            {
                "requirement": requirement_key,
                "principle_key": principle_key,
                "principle": lookup_principle(principle_key),
                "evidence": evidence,
            }
        )
    return violations


def _compliant_note(extracted: dict) -> str:
    if extracted["key_rotation_phrases"]:
        return (
            "Key rotation is stated, which is consistent with correct "
            "key management."
        )
    if extracted["adaptation_phrases"]:
        return (
            "The requirement allows the current algorithm to be replaced, "
            "which is consistent with algorithm agility."
        )
    return "No violation of the listed principles was found."


def format_report(stories: list[dict[str, str]]) -> str:
    """Build the program report used for the assignment screenshot."""
    lines = [
        "IEEE Secure Design Principle: Use cryptography correctly",
        "",
        "Principles checked:",
    ]
    for statement in PRINCIPLES.values():
        lines.append(f"  - {statement}")

    for story_number, story in enumerate(stories, start=1):
        lines.extend(["", f"User story {story_number}"])
        summary = story.get("ALL")
        if summary:
            lines.append(f"Summary: {summary}")

        lines.extend(["", "T1  Parsed requirements"])
        for key, text in story.items():
            lines.append(f"  {key}: {text}")

        lines.extend(["", "T2  Extracted content    T3  Principle lookup"])
        requirement_keys = [key for key in story if key != "ALL"]
        for key in requirement_keys:
            text = story[key]
            extracted = extract_violation_content(text)
            violations = lookup_violations(story, key)
            lines.append(f"{key}: {text}")
            algorithms = ", ".join(extracted["algorithms"]) or "none"
            lines.append(f"  Algorithms: {algorithms}")
            if extracted["key_rotation_phrases"]:
                shown = "; ".join(extracted["key_rotation_phrases"])
                lines.append(f"  Key-management content: {shown}")
            if extracted["adaptation_phrases"]:
                shown = "; ".join(extracted["adaptation_phrases"])
                lines.append(f"  Adaptation content: {shown}")
            if violations:
                for violation in violations:
                    lines.append(f"  VIOLATION: {violation['principle']}")
                    lines.append(
                        "  Evidence: " + "; ".join(violation["evidence"])
                    )
            else:
                lines.append(f"  No violation. {_compliant_note(extracted)}")
            lines.append("")

    violated = 0
    checked = 0
    for story in stories:
        for key in story:
            if key == "ALL":
                continue
            checked += 1
            if lookup_violations(story, key):
                violated += 1
    lines.append(
        f"Result: {violated} of {checked} requirements violate "
        "Use cryptography correctly."
    )
    return "\n".join(lines)


def main() -> None:
    stories = load_user_story()
    print(format_report(stories))


if __name__ == "__main__":
    main()
