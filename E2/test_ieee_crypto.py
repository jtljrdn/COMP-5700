"""T4. Five test cases each for T1, T2, and T3.

Run from this directory:

    python -m unittest -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from ieee_crypto import (
    extract_violation_content,
    load_user_story,
    lookup_violations,
    parse_yaml_content,
)

STORY_PATH = Path(__file__).with_name("user_story.yaml")


def _assignment_story() -> dict[str, str]:
    stories = load_user_story(STORY_PATH)
    if len(stories) != 1:
        raise AssertionError(f"expected 1 story, found {len(stories)}")
    return stories[0]


class TestT1ParseYaml(unittest.TestCase):
    def test_t1_parses_assignment_story_keys(self):
        story = _assignment_story()
        self.assertEqual(
            list(story),
            ["ALL", "R1", "R2", "R3", "R4", "R5"],
        )

    def test_t1_preserves_requirement_text(self):
        story = _assignment_story()
        self.assertEqual(
            story["ALL"],
            "This user story focuses on clearly specifying "
            "crytography-related requirements",
        )
        self.assertEqual(
            story["R1"],
            "We will use MD5 for encrypting all passwords and GitHUb API keys.",
        )
        self.assertEqual(
            story["R5"],
            "If a new cryptography algorithm comes with better strength, "
            "then we will use it instead of SHA512.",
        )

    def test_t1_parses_bare_mapping(self):
        yaml_text = 'R2: "Use a fixed range between 1 and 2."\n'
        stories = parse_yaml_content(yaml_text)
        self.assertEqual(len(stories), 1)
        self.assertEqual(stories[0]["R2"], "Use a fixed range between 1 and 2.")

    def test_t1_empty_document_returns_no_stories(self):
        self.assertEqual(parse_yaml_content(""), [])
        self.assertEqual(parse_yaml_content("null\n"), [])

    def test_t1_rejects_invalid_yaml(self):
        with self.assertRaises(yaml.YAMLError):
            parse_yaml_content(":\n  - [")


class TestT2ExtractViolationContent(unittest.TestCase):
    def setUp(self):
        self.story = _assignment_story()

    def test_t2_r1_extracts_md5_password_encryption(self):
        extracted = extract_violation_content(self.story["R1"])
        self.assertIn("MD5", extracted["algorithms"])
        misuse = " ".join(extracted["misuse_phrases"]).lower()
        self.assertIn("md5", misuse)
        self.assertIn("encrypting all passwords", misuse)

    def test_t2_r2_extracts_fixed_random_range(self):
        extracted = extract_violation_content(self.story["R2"])
        weak = " ".join(extracted["weak_random_phrases"]).lower()
        self.assertIn("fixed range between 39 and 51", weak)
        self.assertEqual(extracted["misuse_phrases"], [])

    def test_t2_r3_extracts_custom_sha512(self):
        extracted = extract_violation_content(self.story["R3"])
        custom = " ".join(extracted["custom_implementation_phrases"]).lower()
        self.assertIn("own implementation", custom)
        self.assertIn("SHA512", extracted["algorithms"])
        misuse = " ".join(extracted["misuse_phrases"]).lower()
        self.assertIn("sha512", misuse)
        self.assertIn("protect", misuse)

    def test_t2_r4_extracts_key_rotation_without_violation_phrases(self):
        extracted = extract_violation_content(self.story["R4"])
        rotation = " ".join(extracted["key_rotation_phrases"]).lower()
        self.assertIn("rotated", rotation)
        self.assertEqual(extracted["custom_implementation_phrases"], [])
        self.assertEqual(extracted["misuse_phrases"], [])
        self.assertEqual(extracted["poor_key_phrases"], [])
        self.assertEqual(extracted["weak_random_phrases"], [])
        self.assertEqual(extracted["agility_failure_phrases"], [])

    def test_t2_r5_extracts_algorithm_adaptation_without_violation_phrases(self):
        extracted = extract_violation_content(self.story["R5"])
        adaptation = " ".join(extracted["adaptation_phrases"]).lower()
        self.assertIn("better strength", adaptation)
        self.assertIn("SHA512", extracted["algorithms"])
        self.assertEqual(extracted["custom_implementation_phrases"], [])
        self.assertEqual(extracted["misuse_phrases"], [])
        self.assertEqual(extracted["poor_key_phrases"], [])
        self.assertEqual(extracted["weak_random_phrases"], [])
        self.assertEqual(extracted["agility_failure_phrases"], [])


class TestT3LookupViolations(unittest.TestCase):
    def setUp(self):
        self.story = _assignment_story()

    def test_t3_r1_misuse_of_md5(self):
        violations = lookup_violations(self.story, "R1")
        self.assertEqual(
            [item["principle_key"] for item in violations],
            ["algorithm_misuse"],
        )
        self.assertEqual(
            violations[0]["principle"],
            "Misuse of libraries and algorithms",
        )

    def test_t3_r2_randomness_that_is_not_random(self):
        violations = lookup_violations(self.story, "R2")
        self.assertEqual(
            [item["principle_key"] for item in violations],
            ["weak_randomness"],
        )
        self.assertEqual(
            violations[0]["principle"],
            "Randomness that is not random",
        )

    def test_t3_r3_custom_crypto_and_hash_misuse(self):
        violations = lookup_violations(self.story, "R3")
        self.assertEqual(
            [item["principle_key"] for item in violations],
            ["custom_crypto", "algorithm_misuse"],
        )
        self.assertEqual(
            violations[0]["principle"],
            "Do not use your own cryptographic algorithms or implementations",
        )
        self.assertEqual(
            violations[1]["principle"],
            "Misuse of libraries and algorithms",
        )

    def test_t3_r4_key_rotation_is_not_a_violation(self):
        self.assertEqual(lookup_violations(self.story, "R4"), [])

    def test_t3_r5_algorithm_adaptation_is_not_a_violation(self):
        self.assertEqual(lookup_violations(self.story, "R5"), [])


if __name__ == "__main__":
    unittest.main()
