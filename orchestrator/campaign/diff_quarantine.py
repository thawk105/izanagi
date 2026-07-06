#!/usr/bin/env python3
"""
Diff Quarantine Layer for Stage 4 Autonomous Coder

Parses unified diff output and validates that modifications stay within
designated EVOLVE-BLOCK holes, preventing frame-alteration and hole-escape attacks.

Part of rigid_enforce pipeline (D30/D33 revised for stage 4).
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass
from enum import Enum


class DiffRejectSubtype(Enum):
    """S4 rejection subtypes for structured diagnosis."""
    FRAME_ALTERED = "frame-altered"
    HOLE_ESCAPE = "hole-escape"
    OUTSIDE_REGION = "outside-region"


@dataclass
class TemplateMarker:
    """Represents an EVOLVE-BLOCK marker region in template."""
    marker_id: str  # e.g., "silo-backoff-magnitude"
    begin_line: int  # Line number of "EVOLVE-BLOCK-BEGIN"
    begin_marker: str  # Full marker line text
    if_line: int  # Line number of "#if BACKOFF_FIXED >= 0"
    if_marker: str
    else_line: int  # Line number of "#else"
    else_marker: str
    endif_line: int  # Line number of "#endif"
    endif_marker: str
    end_line: int  # Line number of "EVOLVE-BLOCK-END"
    end_marker: str

    @property
    def hole_start(self) -> int:
        """Start line of hole (line after #if, inside synthesis branch)."""
        return self.if_line + 1

    @property
    def hole_end(self) -> int:
        """End line of hole (line before #else)."""
        return self.else_line - 1


@dataclass
class DiffHunk:
    """Represents a unified diff hunk."""
    source_start: int
    source_count: int
    dest_start: int
    dest_count: int
    lines: List[Tuple[Literal['+', '-', ' '], str]]  # (prefix, content)

    def added_lines(self) -> List[int]:
        """Return line numbers of added lines in destination file."""
        result = []
        current_dest = self.dest_start
        for prefix, content in self.lines:
            if prefix in ('+', ' '):
                result.append(current_dest)
                current_dest += 1
        return result

    def modified_lines(self) -> List[int]:
        """Return line numbers of modified (context+added) lines in destination file."""
        result = []
        current_dest = self.dest_start
        for prefix, content in self.lines:
            if prefix in ('+', ' '):
                result.append(current_dest)
                current_dest += 1
        return result


@dataclass
class DiffQuarantineResult:
    """Result of diff quarantine check."""
    passed: bool
    rejection_type: Optional[DiffRejectSubtype] = None
    reason: Optional[str] = None
    digest: Optional[Dict] = None  # Structured digest for critic


class DiffQuarantine:
    """
    Validates unified diff against template structure.

    Enforces:
    1. Frame byte-identity: BEGIN/END/markers must match template exactly
    2. Hole boundaries: modifications must stay within #if...#else hole
    3. Stock branch immutability: #else branch (stock code) must not change
    """

    def __init__(self, template_marker: TemplateMarker, working_diff: str):
        """
        Args:
            template_marker: Pre-parsed marker definition from template file
            working_diff: Output of `git diff HEAD` containing modifications
        """
        self.marker = template_marker
        self.diff_text = working_diff
        self.hunks: List[DiffHunk] = []
        self._parse_diff()

    def _parse_diff(self) -> None:
        """Parse unified diff format into hunk objects."""
        hunk_pattern = r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
        lines = self.diff_text.split('\n')

        i = 0
        while i < len(lines):
            match = re.match(hunk_pattern, lines[i])
            if match:
                source_start = int(match.group(1))
                source_count = int(match.group(2) or 1)
                dest_start = int(match.group(3))
                dest_count = int(match.group(4) or 1)

                hunk_lines = []
                i += 1
                while i < len(lines) and not re.match(hunk_pattern, lines[i]):
                    if lines[i].startswith(('+', '-', ' ')):
                        hunk_lines.append((lines[i][0], lines[i][1:]))
                    i += 1

                self.hunks.append(DiffHunk(source_start, source_count, dest_start, dest_count, hunk_lines))
            else:
                i += 1

    def validate(self) -> DiffQuarantineResult:
        """
        Run all quarantine checks.

        Returns:
            DiffQuarantineResult with passed=True or specific rejection_type
        """
        # TODO: Implement checks
        # 1. Frame byte-identity (BEGIN/END/markers must be unchanged)
        # 2. Modified lines within hole
        # 3. #else branch protection
        # 4. No changes outside template region

        # Stub: pass all for now (implementation follows in next session)
        return DiffQuarantineResult(passed=True)


def parse_template_file(template_path: str, marker_id: str) -> Optional[TemplateMarker]:
    """
    Extract EVOLVE-BLOCK marker definition from template file.

    Args:
        template_path: Path to source file (e.g., external/ccbench/include/backoff.hh)
        marker_id: Marker name (e.g., "silo-backoff-magnitude")

    Returns:
        TemplateMarker or None if marker not found
    """
    # TODO: Implement marker parsing
    # Pattern: EVOLVE-BLOCK-BEGIN <marker_id>
    #           ...
    #           #if CONDITION
    #           ...  (hole)
    #           #else
    #           ...  (stock)
    #           #endif
    #           ...
    #           EVOLVE-BLOCK-END <marker_id>
    return None


if __name__ == "__main__":
    # Test stub
    print("diff_quarantine module loaded (implementation pending stage 4)")
