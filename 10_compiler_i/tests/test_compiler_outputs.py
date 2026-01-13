from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


COMPILER_ROOT = Path(__file__).resolve().parents[1]

# Ensure `10_compiler_i/` is importable for plain `unittest` runs.
sys.path.insert(0, str(COMPILER_ROOT))

from compilation_engine import generate_compiled_xml, register_class_names  # noqa: E402
from tests.xml_semantics import assert_xml_semantically_equivalent  # noqa: E402


@dataclass(frozen=True)
class DirectoryCase:
    name: str
    source_dir: Path


def _fixture_dirs() -> list[Path]:
    dirs: list[Path] = []
    for child in COMPILER_ROOT.iterdir():
        if not child.is_dir():
            continue
        jack_files = sorted(child.glob("*.jack"))
        xml_files = sorted(child.glob("*.xml"))
        if jack_files and xml_files:
            dirs.append(child)
    return sorted(dirs)


def _directory_cases() -> list[DirectoryCase]:
    return [DirectoryCase(name=d.name, source_dir=d) for d in _fixture_dirs()]


class TestCompilerOutputs(unittest.TestCase):
    def test_compiler_outputs_match_golden(self) -> None:
        cases = _directory_cases()
        self.assertTrue(cases, f"No fixture directories found under {COMPILER_ROOT}")

        for case in cases:
            with self.subTest(fixture_dir=case.name):
                src_dir = case.source_dir
                jack_files = sorted(src_dir.glob("*.jack"))
                self.assertTrue(jack_files, f"No .jack files found in {src_dir}")

                with tempfile.TemporaryDirectory(prefix=f"nand2tetris_{case.name}_") as td:
                    work_dir = Path(td)

                    temp_jacks: list[Path] = []
                    for jack in jack_files:
                        temp_jack = work_dir / jack.name
                        shutil.copyfile(jack, temp_jack)
                        temp_jacks.append(temp_jack)

                    for temp_jack in temp_jacks:
                        register_class_names(temp_jack)

                    for temp_jack in temp_jacks:
                        generate_compiled_xml(temp_jack)

                    mismatches: list[str] = []
                    for jack in jack_files:
                        expected = jack.with_suffix(".xml")
                        if not expected.exists():
                            continue
                        actual = (work_dir / jack.name).with_suffix(".my.xml")
                        if not actual.exists():
                            mismatches.append(
                                f"Missing output for {jack.name}: expected {actual.name} to be created"
                            )
                            continue
                        try:
                            assert_xml_semantically_equivalent(actual=actual, expected=expected)
                        except AssertionError as e:
                            mismatches.append(f"Output mismatch for {jack.name}: {e}")

                    self.assertFalse(mismatches, ";\n".join(mismatches))

