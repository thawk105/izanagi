# -*- coding: utf-8 -*-
"""Shared parser for one materialized EVOLVE-BLOCK conditional.

The parser is deliberately textual.  It returns the exact captured bytes and
does not claim that the marked branch is reachable in a target translation
unit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MaterializedEvolveBlock:
    """Exact source slices for one uniquely marked conditional block."""

    marker_id: str
    conditional: str
    hole: str


def extract_materialized_evolve_block(
    materialized_source: str,
    marker_id: str,
) -> MaterializedEvolveBlock:
    """Return the conditional and synthesized branch inside one marker pair.

    Acceptance and rejection intentionally match the former sort-oracle
    extractor: exactly one BEGIN and END, exactly one ``#if``/``#else``/
    ``#endif`` within them, and strict directive ordering.
    """
    lines = materialized_source.splitlines(keepends=True)
    begin = re.compile(r"EVOLVE-BLOCK-BEGIN\s+" + re.escape(marker_id) + r"\b")
    end = re.compile(r"EVOLVE-BLOCK-END\s+" + re.escape(marker_id) + r"\b")
    begins = [index for index, line in enumerate(lines) if begin.search(line)]
    ends = [index for index, line in enumerate(lines) if end.search(line)]
    if len(begins) != 1 or len(ends) != 1 or not begins[0] < ends[0]:
        raise ValueError("materialized marker boundary is not unique")

    body_range = range(begins[0] + 1, ends[0])
    if_lines = [
        index for index in body_range
        if re.match(r"^\s*#\s*if(?:def|ndef)?\b", lines[index])
    ]
    else_lines = [
        index for index in body_range
        if re.match(r"^\s*#\s*else\b", lines[index])
    ]
    endif_lines = [
        index for index in body_range
        if re.match(r"^\s*#\s*endif\b", lines[index])
    ]
    if not (len(if_lines) == len(else_lines) == len(endif_lines) == 1):
        raise ValueError("materialized marker does not contain one #if/#else/#endif")
    if not if_lines[0] < else_lines[0] < endif_lines[0]:
        raise ValueError("materialized marker branch ordering is invalid")

    return MaterializedEvolveBlock(
        marker_id=marker_id,
        conditional="".join(lines[if_lines[0]:endif_lines[0] + 1]),
        hole="".join(lines[if_lines[0] + 1:else_lines[0]]),
    )


__all__ = ["MaterializedEvolveBlock", "extract_materialized_evolve_block"]
