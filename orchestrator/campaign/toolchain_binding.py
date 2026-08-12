#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Toolchain receipt と呼び出し側の観測値を照合する pure helper。"""
from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence


class ToolchainBindingError(ValueError):
    """Toolchain binding の入力が一意に解釈できない。"""


def tool_version_body(version: str) -> str:
    """起動名である第 1 token を除き、tool version 本体を返す。"""
    normalized = version.strip()
    for index, character in enumerate(normalized):
        if character.isspace():
            body = normalized[index:]
            if body.strip():
                return body
            break
    raise ValueError("tool version must contain an argv0 token and body")


def _compiler_definitions(
    build_argv: Sequence[str], variable: str,
) -> Iterator[str]:
    prefix = f"-D{variable}="
    for token in build_argv:
        if token.startswith(prefix):
            yield token.split("=", 1)[1]


def _unique_compiler_definition(
    build_argv: Sequence[str], variable: str,
) -> str:
    definitions = tuple(_compiler_definitions(build_argv, variable))
    if len(definitions) != 1:
        raise ToolchainBindingError(
            f"build_argv must define {variable} exactly once"
        )
    return definitions[0]


def extract_floor_compiler_paths(
    build_argv: Sequence[str],
) -> tuple[str, str]:
    """Floor 用。C/CXX compiler の定義が各 1 件のときだけ返す。"""
    return (
        _unique_compiler_definition(build_argv, "CMAKE_C_COMPILER"),
        _unique_compiler_definition(build_argv, "CMAKE_CXX_COMPILER"),
    )


def extract_silo_compiler_paths(
    build_argv: Sequence[str],
) -> tuple[str, str]:
    """Silo 用。現行契約どおり C/CXX compiler の最初の定義を返す。"""
    return (
        next(_compiler_definitions(build_argv, "CMAKE_C_COMPILER")),
        next(_compiler_definitions(build_argv, "CMAKE_CXX_COMPILER")),
    )


def floor_toolchain_matches(
    *,
    receipt_toolchain: Mapping[str, object] | None,
    receipt_build_argv: Sequence[str],
    live_cc_realpath: str,
    live_cxx_realpath: str,
    live_cc_version: str,
    live_cxx_version: str,
    live_cmake_version: str,
) -> bool:
    """Floor receipt と live 観測の全 binding が一致するかを返す。"""
    if receipt_toolchain is None:
        return False
    try:
        registered_cc, registered_cxx = extract_floor_compiler_paths(
            receipt_build_argv
        )
        receipt_cc_realpath = receipt_toolchain["compiler_path"]
        receipt_cc_version = receipt_toolchain["compiler_version"]
        receipt_cmake_version = receipt_toolchain["cmake_version"]
        return (
            receipt_cc_realpath == registered_cc == live_cc_realpath
            and registered_cxx == live_cxx_realpath
            and tool_version_body(receipt_cc_version)  # type: ignore[arg-type]
            == tool_version_body(live_cc_version)
            and tool_version_body(receipt_cmake_version)  # type: ignore[arg-type]
            == tool_version_body(live_cmake_version)
            and tool_version_body(live_cxx_version)
            == tool_version_body(live_cc_version)
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def silo_toolchain_matches(
    *,
    registered_dependency_pins: Mapping[str, str],
    dependency_pins: Mapping[str, str],
    registered_cc_realpath: str,
    registered_cxx_realpath: str,
    receipt_cc_realpath: str,
    receipt_cc_version: str,
    observed_cc_realpath: str,
    observed_cxx_realpath: str,
    observed_cc_version: str,
) -> bool:
    """Silo ladder の既存 5 条件がすべて一致するかを返す。"""
    return not (
        registered_dependency_pins != dependency_pins
        or observed_cc_realpath != registered_cc_realpath
        or observed_cxx_realpath != registered_cxx_realpath
        or observed_cc_realpath != receipt_cc_realpath
        or tool_version_body(observed_cc_version)
        != tool_version_body(receipt_cc_version)
    )
