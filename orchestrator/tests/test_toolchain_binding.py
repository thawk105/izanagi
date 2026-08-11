#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pure toolchain binding helper の回帰テスト。"""
from __future__ import annotations

from itertools import product
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orchestrator.campaign import toolchain_binding as binding  # noqa: E402


def _legacy_tool_version_body(version: str) -> str:
    normalized = version.strip()
    for index, character in enumerate(normalized):
        if character.isspace():
            body = normalized[index:]
            if body.strip():
                return body
            break
    raise ValueError("tool version must contain an argv0 token and body")


def test_tool_version_body_drops_only_argv0_and_keeps_full_body():
    registered = "gcc (Vendor) 1.0\nCopyright registered"
    same = "x86_64-linux-gnu-gcc (Vendor) 1.0\nCopyright registered"
    changed_body = "x86_64-linux-gnu-gcc (Vendor) 1.0\nCopyright changed"

    assert binding.tool_version_body(same) == binding.tool_version_body(
        registered
    )
    assert binding.tool_version_body(changed_body) != (
        binding.tool_version_body(registered)
    )
    assert "\nCopyright registered" in binding.tool_version_body(same)


def test_silo_predicate_matches_legacy_five_condition_truth_table():
    observed_cc = "/tool/cc"
    observed_cxx = "/tool/cxx"
    observed_version = "host-cc (Vendor) 1.0\nCopyright stable"

    for conditions in product((False, True), repeat=5):
        deps_ok, cc_build_ok, cxx_build_ok, cc_receipt_ok, version_ok = (
            conditions
        )
        registered_pins = {"gflags": "a", "glog": "b"}
        live_pins = (
            dict(registered_pins)
            if deps_ok
            else {"gflags": "different", "glog": "b"}
        )
        registered_cc = observed_cc if cc_build_ok else "/other/build-cc"
        registered_cxx = (
            observed_cxx if cxx_build_ok else "/other/build-cxx"
        )
        receipt_cc = observed_cc if cc_receipt_ok else "/other/receipt-cc"
        receipt_version = (
            "receipt-cc (Vendor) 1.0\nCopyright stable"
            if version_ok
            else "receipt-cc (Vendor) 1.0\nCopyright changed"
        )

        legacy = not (
            registered_pins != live_pins
            or observed_cc != registered_cc
            or observed_cxx != registered_cxx
            or observed_cc != receipt_cc
            or _legacy_tool_version_body(observed_version)
            != _legacy_tool_version_body(receipt_version)
        )
        actual = binding.silo_toolchain_matches(
            registered_dependency_pins=registered_pins,
            dependency_pins=live_pins,
            registered_cc_realpath=registered_cc,
            registered_cxx_realpath=registered_cxx,
            receipt_cc_realpath=receipt_cc,
            receipt_cc_version=receipt_version,
            observed_cc_realpath=observed_cc,
            observed_cxx_realpath=observed_cxx,
            observed_cc_version=observed_version,
        )
        assert actual is legacy, conditions


def test_silo_predicate_rejects_registered_dependency_pin_mismatch():
    assert not binding.silo_toolchain_matches(
        registered_dependency_pins={"gflags": "registered", "glog": "pin"},
        dependency_pins={"gflags": "changed", "glog": "pin"},
        registered_cc_realpath="/tool/cc",
        registered_cxx_realpath="/tool/cxx",
        receipt_cc_realpath="/tool/cc",
        receipt_cc_version="receipt-cc (Vendor) 1.0\nsecond line",
        observed_cc_realpath="/tool/cc",
        observed_cxx_realpath="/tool/cxx",
        observed_cc_version="live-cc (Vendor) 1.0\nsecond line",
    )


def test_floor_and_silo_extraction_keep_distinct_acceptance_sets():
    matching = [
        "cmake",
        "-DCMAKE_C_COMPILER=/tool/cc",
        "-DCMAKE_CXX_COMPILER=/tool/cxx",
    ]
    assert binding.extract_floor_compiler_paths(matching) == (
        "/tool/cc",
        "/tool/cxx",
    )

    missing_sets = (
        ["-DCMAKE_CXX_COMPILER=/tool/cxx"],
        ["-DCMAKE_C_COMPILER=/tool/cc"],
    )
    duplicate_sets = (
        matching + ["-DCMAKE_C_COMPILER=/other/cc"],
        matching + ["-DCMAKE_CXX_COMPILER=/other/cxx"],
    )
    for build_argv in missing_sets + duplicate_sets:
        try:
            binding.extract_floor_compiler_paths(build_argv)
        except binding.ToolchainBindingError:
            pass
        else:
            raise AssertionError(f"floor accepted ambiguous argv: {build_argv!r}")

    duplicated = [
        "-DCMAKE_C_COMPILER=/first/cc",
        "-DCMAKE_C_COMPILER=/second/cc",
        "-DCMAKE_CXX_COMPILER=/first/cxx",
        "-DCMAKE_CXX_COMPILER=/second/cxx",
    ]
    assert binding.extract_silo_compiler_paths(duplicated) == (
        "/first/cc",
        "/first/cxx",
    )


def _matching_floor_arguments() -> dict[str, object]:
    return {
        "receipt_toolchain": {
            "compiler_path": "/tool/cc",
            "compiler_version": "receipt-cc (Vendor) 1.0\nCopyright stable",
            "cmake_version": "cmake version 3.25.0\nCopyright stable",
        },
        "receipt_build_argv": [
            "cmake",
            "-DCMAKE_C_COMPILER=/tool/cc",
            "-DCMAKE_CXX_COMPILER=/tool/cxx",
        ],
        "live_cc_realpath": "/tool/cc",
        "live_cxx_realpath": "/tool/cxx",
        "live_cc_version": "live-cc (Vendor) 1.0\nCopyright stable",
        "live_cxx_version": "live-cxx (Vendor) 1.0\nCopyright stable",
        "live_cmake_version": "cmake version 3.25.0\nCopyright stable",
    }


def test_floor_predicate_accepts_exact_registered_match():
    assert binding.floor_toolchain_matches(**_matching_floor_arguments())


def test_floor_predicate_rejects_each_independent_mismatch():
    scalar_mutations: tuple[tuple[str, object], ...] = (
        ("live_cc_realpath", "/other/cc"),
        ("live_cxx_realpath", "/other/cxx"),
        (
            "live_cc_version",
            "live-cc (Vendor) 1.0\nCopyright changed",
        ),
        (
            "live_cmake_version",
            "cmake version 3.25.0\nCopyright changed",
        ),
        (
            "live_cxx_version",
            "live-cxx (Vendor) 1.0\nCopyright changed",
        ),
        ("receipt_toolchain", None),
    )
    for key, value in scalar_mutations:
        arguments = _matching_floor_arguments()
        arguments[key] = value
        assert not binding.floor_toolchain_matches(**arguments), key

    receipt_mismatch = _matching_floor_arguments()
    receipt_mismatch["receipt_toolchain"] = {
        "compiler_path": "/other/receipt-cc",
        "compiler_version": "receipt-cc (Vendor) 1.0\nCopyright stable",
        "cmake_version": "cmake version 3.25.0\nCopyright stable",
    }
    assert not binding.floor_toolchain_matches(**receipt_mismatch)

    build_mismatch = _matching_floor_arguments()
    build_mismatch["receipt_build_argv"] = [
        "cmake",
        "-DCMAKE_C_COMPILER=/other/build-cc",
        "-DCMAKE_CXX_COMPILER=/tool/cxx",
    ]
    assert not binding.floor_toolchain_matches(**build_mismatch)


def _run() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"PASS {test.__name__}")
    print(f"{len(tests) - failures} passed, {failures} failed")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(_run())
