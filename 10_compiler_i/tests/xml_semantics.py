from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class XmlDiff:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def _norm_text(text: str | None) -> str:
    # In nand2tetris XML outputs, whitespace around token text and indentation/newlines
    # are not semantically meaningful. We treat elements as equal if their text matches
    # after stripping leading/trailing whitespace (internal whitespace is preserved).
    return (text or "").strip()


def _element_id(elem: ET.Element, idx: int) -> str:
    # Helpful for error messages; uses tag plus its position among siblings.
    return f"{elem.tag}[{idx}]"


def _compare_elements(a: ET.Element, b: ET.Element, path: str) -> XmlDiff | None:
    if a.tag != b.tag:
        return XmlDiff(path, f"tag differs: {a.tag!r} != {b.tag!r}")

    # Attributes are rarely used in these outputs, but compare them for completeness.
    if a.attrib != b.attrib:
        return XmlDiff(path, f"attrib differs: {a.attrib!r} != {b.attrib!r}")

    a_text = _norm_text(a.text)
    b_text = _norm_text(b.text)
    if a_text != b_text:
        return XmlDiff(path, f"text differs: {a_text!r} != {b_text!r}")

    a_children = list(a)
    b_children = list(b)
    if len(a_children) != len(b_children):
        return XmlDiff(path, f"child count differs: {len(a_children)} != {len(b_children)}")

    for i, (ac, bc) in enumerate(zip(a_children, b_children)):
        child_path = f"{path}/{_element_id(ac, i)}"
        diff = _compare_elements(ac, bc, child_path)
        if diff is not None:
            return diff

    return None


def assert_xml_semantically_equivalent(actual: Path, expected: Path) -> None:
    """
    Assert that two XML files are semantically equivalent:
    - same element tree structure (tag order and nesting)
    - same attributes
    - same element text after stripping leading/trailing whitespace

    This makes tests robust to formatting differences (indentation, trailing spaces, EOLs).
    """
    try:
        actual_root = ET.parse(actual).getroot()
    except ET.ParseError as e:  # pragma: no cover
        raise AssertionError(f"Failed to parse actual XML {actual}: {e}") from e

    try:
        expected_root = ET.parse(expected).getroot()
    except ET.ParseError as e:  # pragma: no cover
        raise AssertionError(f"Failed to parse expected XML {expected}: {e}") from e

    diff = _compare_elements(actual_root, expected_root, path=f"/{actual_root.tag}[0]")
    if diff is not None:
        raise AssertionError(
            "\n".join(
                [
                    "XML outputs are not semantically equivalent.",
                    f"- actual:   {actual}",
                    f"- expected: {expected}",
                    f"- first diff: {diff}",
                ]
            )
        )

