from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest


COMPILER_ROOT = Path(__file__).resolve().parents[1]

# Ensure `10_compiler_i/` is importable for plain `unittest` runs.
sys.path.insert(0, str(COMPILER_ROOT))

from tokenizer import generate_tokenized_xml  # noqa: E402
from tests.xml_semantics import assert_xml_semantically_equivalent  # noqa: E402


def _fixture_dirs() -> list[Path]:
    dirs: list[Path] = []
    for child in COMPILER_ROOT.iterdir():
        if not child.is_dir():
            continue
        jack_files = sorted(child.glob("*.jack"))
        token_xml_files = sorted(child.glob("*T.xml"))
        if jack_files and token_xml_files:
            dirs.append(child)
    return sorted(dirs)


class TestTokenizerOutputs(unittest.TestCase):
    def test_tokenizer_outputs_match_golden(self) -> None:
        fixture_dirs = _fixture_dirs()
        self.assertTrue(fixture_dirs, f"No fixture directories found under {COMPILER_ROOT}")

        for src_dir in fixture_dirs:
            with self.subTest(fixture_dir=src_dir.name):
                jack_files = sorted(src_dir.glob("*.jack"))
                self.assertTrue(jack_files, f"No .jack files found in {src_dir}")

                with tempfile.TemporaryDirectory(prefix=f"nand2tetris_{src_dir.name}_") as td:
                    work_dir = Path(td)

                    for jack in jack_files:
                        temp_jack = work_dir / jack.name
                        shutil.copyfile(jack, temp_jack)
                        generate_tokenized_xml(temp_jack)

                    mismatches: list[str] = []
                    for jack in jack_files:
                        expected = jack.with_name(jack.stem + "T.xml")
                        if not expected.exists():
                            continue
                        actual = (work_dir / jack.name).with_suffix(".my.xml")
                        if not actual.exists():
                            mismatches.append(
                                f"Missing token output for {jack.name}: expected {actual.name} to be created"
                            )
                            continue
                        try:
                            assert_xml_semantically_equivalent(actual=actual, expected=expected)
                        except AssertionError as e:
                            mismatches.append(f"Token output mismatch for {jack.name}: {e}")

                    self.assertFalse(mismatches, ";\n".join(mismatches))
