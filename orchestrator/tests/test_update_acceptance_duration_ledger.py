from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import stat
import xml.etree.ElementTree as ET

import pytest

from tools import update_acceptance_duration_ledger as ledger


_REJECTION_PREFIX = "acceptance duration ledger input rejected:"


@pytest.fixture
def join_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    module = repo / "pkg" / "tests" / "test_mod.py"
    module.parent.mkdir(parents=True)
    module.write_text("# join fixture\n", encoding="utf-8")
    return repo


def _case(
    classname: str,
    name: str,
    time: str | None,
    *,
    skipped: bool = False,
    failure: bool = False,
    error: bool = False,
) -> dict[str, object]:
    return {
        "classname": classname,
        "name": name,
        "time": time,
        "skipped": skipped,
        "failure": failure,
        "error": error,
    }


def _write_junit(
    path: Path,
    cases: list[dict[str, object]],
    *,
    failures: int = 0,
    errors: int = 0,
) -> None:
    root = ET.Element("testsuites", {"name": "pytest tests"})
    suite = ET.SubElement(
        root,
        "testsuite",
        {
            "name": "pytest",
            "tests": str(len(cases)),
            "failures": str(failures),
            "errors": str(errors),
            "skipped": str(sum(bool(case["skipped"]) for case in cases)),
        },
    )
    for case in cases:
        attributes = {
            "classname": str(case["classname"]),
            "name": str(case["name"]),
        }
        if case["time"] is not None:
            attributes["time"] = str(case["time"])
        testcase = ET.SubElement(suite, "testcase", attributes)
        if case["skipped"]:
            ET.SubElement(testcase, "skipped")
        if case["failure"]:
            ET.SubElement(testcase, "failure")
        if case["error"]:
            ET.SubElement(testcase, "error")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def _run(
    repo: Path,
    output: Path,
    *junit: Path,
    extra: list[str] | None = None,
) -> int:
    argv = [*(str(path) for path in junit), "--repo", str(repo), "--output", str(output)]
    if extra:
        argv.extend(extra)
    return ledger.main(argv)


def test_g7a_join_generates_canonical_nodeids_and_check_passes(
    join_repo: Path,
    tmp_path: Path,
) -> None:
    junit = tmp_path / "join.xml"
    output = tmp_path / "ledger.json"
    _write_junit(
        junit,
        [
            _case("pkg.tests.test_mod", "test_top", "0.125"),
            _case("pkg.tests.test_mod.TestCase", "test_method", "1.234"),
            _case("pkg.tests.test_mod", "test_param[value]", "0.00456"),
            _case("pkg.tests.test_mod", "test_skipped", "0", skipped=True),
        ],
    )

    assert _run(join_repo, output, junit) == 0
    payload = json.loads(output.read_text(encoding="ascii"))
    assert payload == {
        "duration_seconds_by_nodeid": {
            "pkg/tests/test_mod.py::TestCase::test_method": 1.2,
            "pkg/tests/test_mod.py::test_param[value]": 0.0046,
            "pkg/tests/test_mod.py::test_skipped": 0.0,
            "pkg/tests/test_mod.py::test_top": 0.13,
        },
        "nodeid_count": 4,
        "schema_version": 1,
        "unit": "seconds",
    }
    assert output.read_bytes().endswith(b"\n")
    assert _run(join_repo, output, junit, extra=["--check"]) == 0


@pytest.mark.parametrize(
    ("case_kind", "cases", "failures"),
    [
        (
            "shifted-module-class-boundary",
            [_case("pkg.TestCase.tests.test_mod", "test_x", "0.1")],
            0,
        ),
        (
            "duplicate-nodeid",
            [
                _case("pkg.tests.test_mod", "test_x", "0.1"),
                _case("pkg.tests.test_mod", "test_x", "0.2"),
            ],
            0,
        ),
        ("missing-duration", [_case("pkg.tests.test_mod", "test_x", None)], 0),
        ("negative-duration", [_case("pkg.tests.test_mod", "test_x", "-0.1")], 0),
        ("nan-duration", [_case("pkg.tests.test_mod", "test_x", "nan")], 0),
        ("infinite-duration", [_case("pkg.tests.test_mod", "test_x", "inf")], 0),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_g7a_each_invalid_input_is_rejected_with_fixed_signature(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case_kind: str,
    cases: list[dict[str, object]],
    failures: int,
) -> None:
    del case_kind
    junit = tmp_path / "invalid.xml"
    output = tmp_path / "ledger.json"
    _write_junit(junit, cases, failures=failures)

    assert _run(join_repo, output, junit) == 2
    assert capsys.readouterr().err.startswith(_REJECTION_PREFIX)
    assert not output.exists()


def test_g7a_duplicate_nodeid_across_shards_is_rejected(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = tmp_path / "first.xml"
    second = tmp_path / "second.xml"
    output = tmp_path / "ledger.json"
    duplicate = _case("pkg.tests.test_mod", "test_same", "0.1")
    _write_junit(first, [duplicate])
    _write_junit(
        second,
        [_case("pkg.tests.test_mod", "test_same", "0.2", failure=True)],
        failures=1,
    )

    assert _run(join_repo, output, first, second) == 2
    assert capsys.readouterr().err.startswith(_REJECTION_PREFIX)
    assert not output.exists()


def test_f5_ambiguous_module_prefix_lengths_are_rejected(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = tmp_path / "repo"
    short_module = repo / "pkg" / "test_mod.py"
    long_module = repo / "pkg" / "test_mod" / "TestCase.py"
    short_module.parent.mkdir(parents=True)
    long_module.parent.mkdir(parents=True)
    short_module.write_text("# short candidate\n", encoding="utf-8")
    long_module.write_text("# long candidate\n", encoding="utf-8")
    junit = tmp_path / "ambiguous.xml"
    output = tmp_path / "ledger.json"
    _write_junit(junit, [_case("pkg.test_mod.TestCase", "test_x", "0.1")])

    assert _run(repo, output, junit) == 2
    error = capsys.readouterr().err
    assert error.startswith(_REJECTION_PREFIX)
    assert "ambiguous module" in error
    assert not output.exists()


def test_f9_disjoint_junit_shards_are_merged(
    join_repo: Path,
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.xml"
    second = tmp_path / "second.xml"
    output = tmp_path / "ledger.json"
    _write_junit(first, [_case("pkg.tests.test_mod", "test_first", "0.1")])
    _write_junit(second, [_case("pkg.tests.test_mod", "test_second", "0.2")])

    assert _run(join_repo, output, first, second) == 0
    payload = json.loads(output.read_text(encoding="ascii"))
    assert payload["duration_seconds_by_nodeid"] == {
        "pkg/tests/test_mod.py::test_first": 0.1,
        "pkg/tests/test_mod.py::test_second": 0.2,
    }
    assert payload["nodeid_count"] == 2


def test_g7a_check_difference_returns_one_without_writing(
    join_repo: Path,
    tmp_path: Path,
) -> None:
    junit = tmp_path / "valid.xml"
    output = tmp_path / "ledger.json"
    _write_junit(junit, [_case("pkg.tests.test_mod", "test_x", "0.1")])
    before = b"stale ledger bytes\n"
    output.write_bytes(before)

    assert _run(join_repo, output, junit, extra=["--check"]) == 1
    assert output.read_bytes() == before


def test_g7b_second_input_failure_leaves_existing_output_byte_exact(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = tmp_path / "first.xml"
    second = tmp_path / "second.xml"
    output = tmp_path / "ledger.json"
    before = b"pre-existing ledger bytes\x00\xff\n"
    output.write_bytes(before)
    _write_junit(first, [_case("pkg.tests.test_mod", "test_first", "0.1")])
    _write_junit(second, [_case("pkg.tests.test_mod", "test_bad", None)])

    assert _run(join_repo, output, first, second) == 2
    assert capsys.readouterr().err.startswith(_REJECTION_PREFIX)
    assert output.read_bytes() == before


def test_g7c_group_suffix_guard_preserves_at_inside_parametrize_value(
    join_repo: Path,
    tmp_path: Path,
) -> None:
    junit = tmp_path / "groups.xml"
    output = tmp_path / "ledger.json"
    _write_junit(
        junit,
        [
            _case("pkg.tests.test_mod", "test_x[user@example.com]", "0.1"),
            _case("pkg.tests.test_mod", "test_y@g", "0.2"),
            _case("pkg.tests.test_mod", "test_z[user@example.com]@group", "0.3"),
        ],
    )

    assert _run(join_repo, output, junit) == 0
    nodeids = set(json.loads(output.read_text())["duration_seconds_by_nodeid"])
    assert nodeids == {
        "pkg/tests/test_mod.py::test_x[user@example.com]",
        "pkg/tests/test_mod.py::test_y",
        "pkg/tests/test_mod.py::test_z[user@example.com]",
    }


def test_g7d_quantization_is_byte_deterministic_and_absorbs_small_jitter(
    join_repo: Path,
    tmp_path: Path,
) -> None:
    junit = tmp_path / "duration.xml"
    output = tmp_path / "ledger.json"
    cases = [_case("pkg.tests.test_mod", "test_x", "1.234")]
    _write_junit(junit, cases)

    assert _run(join_repo, output, junit) == 0
    first = output.read_bytes()
    assert _run(join_repo, output, junit) == 0
    assert output.read_bytes() == first

    cases[0]["time"] = "1.239"
    _write_junit(junit, cases)
    assert _run(join_repo, output, junit) == 0
    assert output.read_bytes() == first


def test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations() -> None:
    path = Path(__file__).with_name("acceptance_duration_ledger.json")
    payload = json.loads(path.read_text(encoding="ascii"))
    assert set(payload) == {
        "duration_seconds_by_nodeid",
        "nodeid_count",
        "schema_version",
        "unit",
    }
    assert payload["schema_version"] == 1
    assert payload["unit"] == "seconds"
    durations = payload["duration_seconds_by_nodeid"]
    assert isinstance(durations, dict)
    assert payload["nodeid_count"] == len(durations)
    assert all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
        for value in durations.values()
    )


def test_t1574_changed_suite_ledger_node_delta_is_exact() -> None:
    payload = json.loads(
        Path(__file__).with_name("acceptance_duration_ledger.json").read_text(
            encoding="ascii"
        )
    )
    durations = payload["duration_seconds_by_nodeid"]
    removed = {
        "orchestrator/tests/test_critic.py::test_current_loader_rejects_non_exact_oracle_contract_ids[sort-swo-v3-corpus1-protocol2-checker2-grammar1-x2b6d45baab3f921208db25299b8622592c484dfb28bebeb8d2cf976fe38474f9-c436a66d9d5d5-tud88f98bc1991-f7ad0ac262561-a215b718a5bfe-suffix]",
        "orchestrator/tests/test_critic.py::test_current_loader_rejects_non_exact_oracle_contract_ids[sort-swo-v4-corpus1-protocol2-checker2-grammar1-x2b6d45baab3f921208db25299b8622592c484dfb28bebeb8d2cf976fe38474f9-c436a66d9d5d5-tud88f98bc1991-f7ad0ac262561-a215b718a5bfe]",
        r"orchestrator/tests/test_critic.py::test_sort_swo_non_axiom_kinds_have_dedicated_fixed_rendering[mutation-\u5168 field snapshot \u304c\u5909\u5316]",
        r"orchestrator/tests/test_critic.py::test_sort_swo_non_axiom_kinds_have_dedicated_fixed_rendering[protocol-\u56fa\u5b9a\u9577 protocol \u306e\u7570\u5e38]",
        "orchestrator/tests/test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
    }
    added = {
        "orchestrator/tests/test_sort_swo_oracle.py::test_cpp_e2e_high_storage_only_negative_kills_corpus_narrowing": 5.89,
        "orchestrator/tests/test_sort_swo_oracle.py::test_cpp_e2e_reports_each_axiom_and_exact_indices[equivalence-transitive]": 5.88,
        "orchestrator/tests/test_sort_swo_oracle.py::test_real_ctor_pointer_topology_and_triplicate_have_expected_matrix_meaning": 5.81,
        "orchestrator/tests/test_sort_swo_oracle.py::test_cpp_e2e_rejects_same_process_call_count_dependence_with_witness": 5.8,
        "orchestrator/tests/test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding@real-repo": 0.19,
        "orchestrator/tests/test_sort_swo_oracle.py::test_masstree_manifest_rejects_one_byte_change": 0.12,
        "orchestrator/tests/test_sort_swo_oracle.py::test_masstree_manifest_rejects_unregistered_fixture_file": 0.11,
        "orchestrator/tests/test_sort_swo_oracle.py::test_masstree_manifest_rejects_parent_reference": 0.11,
        "orchestrator/tests/test_sort_swo_oracle.py::test_masstree_manifest_rejects_symlink_outside_fixture": 0.11,
        "orchestrator/tests/test_sort_swo_oracle.py::test_masstree_manifest_rejects_header_removed_from_manifest": 0.11,
        "orchestrator/tests/test_sort_swo_oracle.py::test_masstree_manifest_rejects_missing_fixture_file": 0.11,
        "orchestrator/tests/test_sort_swo_oracle.py::test_resolver_config_h_missing_is_exact_failure_not_skip": 0.11,
    }
    assert removed.isdisjoint(durations)
    assert {node: durations.get(node) for node in added} == added

    # CS-1/2/3 が変更した suite ごとに、current collection から台帳へ登録済みの
    # node 集合を sorted UTF-8 + LF の SHA-256 で exact 固定する。件数だけでなく
    # node bytes 全体への commitment なので、current 1 件を stale 1 件へ入れ替える
    # count-preserving mutation も必ず不一致になる。未実測 node の値は合成しない。
    expected_suite_node_sets = {
        "orchestrator/tests/test_critic.py::": (
            121, "1e8b4cd41b1e80708c79f247ef9c8ddb21d82bdc7e999cdc53e8713821cb0692",
        ),
        "orchestrator/tests/test_p3_exploration_namespace.py::": (
            26, "db38065c3ebe9834490717df17f634af1c54dddab130d1eea0851723f3db7efa",
        ),
        "orchestrator/tests/test_p3_s4_loop_sort.py::": (
            29, "f29aabf31c8ce1ee6b5e15435834ba6a535b2628f14ad186f342b2f47f6c2bed",
        ),
        "orchestrator/tests/test_real_repo_serialization.py::": (
            42, "6fb7e97e2d410d716f45e641092794dafc9fc98717b663429bb9d18528db8874",
        ),
        "orchestrator/tests/test_s1_direct_comparison.py::": (
            97, "ed1a63057f76b8807144943fff4ca7689fa7e0c2936a6c6512ef3ad5ffdce9d5",
        ),
        "orchestrator/tests/test_s8b_materialization.py::": (
            30, "31ee53d57df57fdc3e8c350c97d9425afa4e9897aa2c716efe0608e822884f5b",
        ),
        "orchestrator/tests/test_s8b_sort_swo_receipt.py::": (
            12, "a95979bd14e970ac6e08f1061a1c7b434549a3f4a3e3913d3ef6303b6a3a4ec2",
        ),
        "orchestrator/tests/test_sort_swo_oracle.py::": (
            69, "7e97c114b313d8fccb97f486379745e060e3486a132de271a244e9c1e3f6d912",
        ),
    }

    def exact_node_set_identity(nodes: set[str]) -> tuple[int, str]:
        canonical = "".join(f"{node}\n" for node in sorted(nodes)).encode(
            "utf-8"
        )
        return len(nodes), hashlib.sha256(canonical).hexdigest()

    observed_by_suite = {
        prefix: {node for node in durations if node.startswith(prefix)}
        for prefix in expected_suite_node_sets
    }
    assert {
        prefix: exact_node_set_identity(nodes)
        for prefix, nodes in observed_by_suite.items()
    } == expected_suite_node_sets

    # 同数入替えを明示的に反転させ、hash gate が count-only でないことを固定する。
    critic_prefix = "orchestrator/tests/test_critic.py::"
    count_preserving_swap = set(observed_by_suite[critic_prefix])
    count_preserving_swap.remove(min(count_preserving_swap))
    count_preserving_swap.add(
        "orchestrator/tests/test_critic.py::test_stale_count_preserving_swap"
    )
    assert exact_node_set_identity(count_preserving_swap) != (
        expected_suite_node_sets[critic_prefix]
    )


def test_g7f_coverage_reports_complete_and_missing_nodeids(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    junit = tmp_path / "coverage.xml"
    output = tmp_path / "ledger.json"
    collection = tmp_path / "collection.txt"
    known = "pkg/tests/test_mod.py::test_known"
    _write_junit(junit, [_case("pkg.tests.test_mod", "test_known", "0.1")])

    collection.write_text(f"{known}\n1 test collected in 0.01s\n", encoding="utf-8")
    assert _run(
        join_repo,
        output,
        junit,
        extra=["--coverage-against", str(collection)],
    ) == 0
    assert capsys.readouterr().out == (
        "excluded_failure_or_error=0\n"
        "covered=1 total=1 ratio=1.000\n"
    )

    collection.write_text(
        f"{known}\npkg/tests/test_mod.py::test_not_in_ledger\n"
        "2 tests collected in 0.01s\n",
        encoding="utf-8",
    )
    assert _run(
        join_repo,
        output,
        junit,
        extra=["--check", "--coverage-against", str(collection)],
    ) == 0
    assert capsys.readouterr().out == (
        "excluded_failure_or_error=0\n"
        "covered=1 total=2 ratio=0.500\n"
    )


def test_f8_coverage_normalizes_relative_path_and_group_suffix(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    junit = tmp_path / "coverage-group.xml"
    output = tmp_path / "ledger.json"
    collection = tmp_path / "collection.txt"
    _write_junit(junit, [_case("pkg.tests.test_mod", "test_known", "0.1")])
    collection.write_text(
        "./pkg/tests/test_mod.py::test_known@load-group\n",
        encoding="utf-8",
    )

    assert _run(
        join_repo,
        output,
        junit,
        extra=["--coverage-against", str(collection)],
    ) == 0
    assert capsys.readouterr().out == (
        "excluded_failure_or_error=0\n"
        "covered=1 total=1 ratio=1.000\n"
    )


def test_g7g_failed_and_error_cases_are_excluded_but_skipped_is_included(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    junit = tmp_path / "mixed-outcomes.xml"
    output = tmp_path / "ledger.json"
    _write_junit(
        junit,
        [
            _case("pkg.tests.test_mod", "test_failure", "1.0", failure=True),
            _case("pkg.tests.test_mod", "test_error", "2.0", error=True),
            _case("pkg.tests.test_mod", "test_pass_one", "0.1"),
            _case("pkg.tests.test_mod", "test_pass_two", "0.2"),
            _case("pkg.tests.test_mod", "test_skipped", "0.0", skipped=True),
        ],
        failures=1,
        errors=1,
    )

    assert _run(join_repo, output, junit) == 0
    assert capsys.readouterr().out == "excluded_failure_or_error=2\n"
    payload = json.loads(output.read_text(encoding="ascii"))
    assert payload["nodeid_count"] == 3
    assert set(payload["duration_seconds_by_nodeid"]) == {
        "pkg/tests/test_mod.py::test_pass_one",
        "pkg/tests/test_mod.py::test_pass_two",
        "pkg/tests/test_mod.py::test_skipped",
    }


def test_add_only_preserves_existing_entry_bytes_and_excludes_frozen_nodes(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for prefix in ledger._ADD_ONLY_FROZEN_SUITE_PREFIXES:
        module = join_repo / prefix.removesuffix("::")
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("# add-only exclusion fixture\n", encoding="utf-8")

    existing_durations = {
        "pkg/tests/test_mod.py::test_other": 0.7,
        "pkg/tests/test_mod.py::test_existing": 0.5,
    }
    before = (
        json.dumps(
            {
                "duration_seconds_by_nodeid": existing_durations,
                "nodeid_count": len(existing_durations),
                "schema_version": 1,
                "unit": "seconds",
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    ).encode("ascii")
    output = tmp_path / "ledger.json"
    output.write_bytes(before)

    def case_for_nodeid(
        nodeid: str,
        time: str,
        *,
        failure: bool = False,
    ) -> dict[str, object]:
        module_path, name = nodeid.split("::", 1)
        classname = module_path.removesuffix(".py").replace("/", ".")
        return _case(classname, name, time, failure=failure)

    frozen_suite_nodeids = {
        f"{prefix}test_add_only_must_exclude"
        for prefix in ledger._ADD_ONLY_FROZEN_SUITE_PREFIXES
    }
    failed_nodeid = "pkg/tests/test_mod.py::test_failed_new"
    junit = tmp_path / "add-only.xml"
    _write_junit(
        junit,
        [
            case_for_nodeid("pkg/tests/test_mod.py::test_existing", "9.9"),
            case_for_nodeid("pkg/tests/test_mod.py::test_new", "0.25"),
            *(case_for_nodeid(nodeid, "0.1") for nodeid in frozen_suite_nodeids),
            *(
                case_for_nodeid(nodeid, "0.2")
                for nodeid in ledger._ADD_ONLY_FROZEN_REMOVED_NODEIDS
            ),
            case_for_nodeid(failed_nodeid, "0.3", failure=True),
        ],
        failures=1,
    )

    assert _run(join_repo, output, junit, extra=["--add-only"]) == 0
    assert capsys.readouterr().out == (
        "excluded_failure_or_error=1\n"
        "mode=add-only\n"
        "added=1\n"
        "skipped_existing=1\n"
        "excluded_frozen_removed=4\n"
        "excluded_writer_base_key=1\n"
        "excluded_frozen_suite=8\n"
        "excluded_total=14\n"
    )

    after = output.read_bytes()
    added_entry = b'    "pkg/tests/test_mod.py::test_new": 0.25,\n'
    assert after.count(added_entry) == 1
    restored = after.replace(added_entry, b"", 1).replace(
        b'  "nodeid_count": 3,',
        b'  "nodeid_count": 2,',
        1,
    )
    assert restored == before

    durations = json.loads(after.decode("ascii"))["duration_seconds_by_nodeid"]
    assert list(durations.items())[-2:] == list(existing_durations.items())
    assert durations["pkg/tests/test_mod.py::test_existing"] == 0.5
    assert frozen_suite_nodeids.isdisjoint(durations)
    assert ledger._ADD_ONLY_FROZEN_REMOVED_NODEIDS.isdisjoint(durations)
    assert ledger._ADD_ONLY_FROZEN_WRITER_BASE_KEY not in durations
    assert failed_nodeid not in durations


def test_f6_failed_case_is_excluded_before_duration_validation(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    junit = tmp_path / "failure-without-time.xml"
    output = tmp_path / "ledger.json"
    _write_junit(
        junit,
        [
            _case("pkg.tests.test_mod", "test_pass", "0.1"),
            _case("pkg.tests.test_mod", "test_failure", None, failure=True),
        ],
        failures=1,
    )

    assert _run(join_repo, output, junit) == 0
    assert capsys.readouterr().out == "excluded_failure_or_error=1\n"
    payload = json.loads(output.read_text(encoding="ascii"))
    assert payload["duration_seconds_by_nodeid"] == {
        "pkg/tests/test_mod.py::test_pass": 0.1,
    }
    assert "pkg/tests/test_mod.py::test_failure" not in payload[
        "duration_seconds_by_nodeid"
    ]


def test_f6_error_case_with_invalid_classname_is_discarded(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    junit = tmp_path / "error-with-invalid-classname.xml"
    output = tmp_path / "ledger.json"
    _write_junit(
        junit,
        [
            _case("pkg.tests.test_mod", "test_pass", "0.1"),
            _case("not/a/classname", "test_error", "0.2", error=True),
        ],
        errors=1,
    )

    assert _run(join_repo, output, junit) == 0
    assert capsys.readouterr().out == "excluded_failure_or_error=1\n"
    payload = json.loads(output.read_text(encoding="ascii"))
    assert payload["duration_seconds_by_nodeid"] == {
        "pkg/tests/test_mod.py::test_pass": 0.1,
    }


def test_f11_atomic_write_fsyncs_file_then_parent_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "nested" / "ledger.json"
    fsync_targets: list[bool] = []
    real_fsync = ledger.os.fsync

    def recording_fsync(fd: int) -> None:
        fsync_targets.append(stat.S_ISDIR(ledger.os.fstat(fd).st_mode))
        real_fsync(fd)

    monkeypatch.setattr(ledger.os, "fsync", recording_fsync)
    ledger._atomic_write(output, b"ledger bytes\n")

    assert output.read_bytes() == b"ledger bytes\n"
    assert fsync_targets == [False, True]


def test_g7h_all_failed_and_empty_junit_have_distinct_rejections(
    join_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "ledger.json"
    before = b"pre-existing ledger bytes\x00\xff\n"
    output.write_bytes(before)

    all_failed = tmp_path / "all-failed.xml"
    _write_junit(
        all_failed,
        [
            _case("pkg.tests.test_mod", "test_failure_one", "1.0", failure=True),
            _case("pkg.tests.test_mod", "test_failure_two", "2.0", failure=True),
        ],
        failures=2,
    )
    assert _run(join_repo, output, all_failed) == 2
    all_failed_error = capsys.readouterr().err
    assert all_failed_error.startswith(_REJECTION_PREFIX)
    assert "no usable testcases after excluding 2 failed/error testcases" in all_failed_error
    assert output.read_bytes() == before

    empty = tmp_path / "empty.xml"
    _write_junit(empty, [])
    assert _run(join_repo, output, empty) == 2
    empty_error = capsys.readouterr().err
    assert empty_error.startswith(_REJECTION_PREFIX)
    assert "contains no testcases" in empty_error
    assert empty_error != all_failed_error
    assert output.read_bytes() == before



def _refresh_fixture_bytes(durations: dict[str, float]) -> bytes:
    return (json.dumps({
        "duration_seconds_by_nodeid": durations,
        "nodeid_count": len(durations),
        "schema_version": 1,
        "unit": "seconds",
    }, ensure_ascii=True, indent=2, allow_nan=False) + "\n").encode("ascii")


def _refresh_frozen_modules(repo: Path) -> None:
    for prefix in ledger._ADD_ONLY_FROZEN_SUITE_PREFIXES:
        module = repo / prefix.removesuffix("::")
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("# refresh fixture\n", encoding="utf-8")


def _refresh_case(nodeid: str, time: str, **outcome: bool) -> dict[str, object]:
    module, name = nodeid.split("::", 1)
    return _case(module.removesuffix(".py").replace("/", "."), name, time, **outcome)


@pytest.mark.parametrize("duration", ["9.9", "0.5"])
def test_refresh_replaces_nonfrozen_entries_and_removes_old_names(
    join_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], duration: str,
) -> None:
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    output.write_bytes(_refresh_fixture_bytes({
        "pkg/tests/test_mod.py::test_existing": 0.5,
        "pkg/tests/test_mod.py::test_old": 0.7,
    }))
    _write_junit(junit, [
        _case("pkg.tests.test_mod", "test_existing", duration),
        _case("pkg.tests.test_mod", "test_new", "0.25"),
    ])
    assert _run(join_repo, output, junit, extra=["--refresh"]) == 0
    payload = json.loads(output.read_bytes())
    assert payload["duration_seconds_by_nodeid"] == {
        "pkg/tests/test_mod.py::test_existing": float(duration),
        "pkg/tests/test_mod.py::test_new": 0.25,
    }
    assert "pkg/tests/test_mod.py::test_old" not in payload["duration_seconds_by_nodeid"]
    assert payload["nodeid_count"] == 2
    assert capsys.readouterr().out == (
        "excluded_failure_or_error=0\nmode=refresh\npreserved_frozen=0\n"
        "replaced=1\nadded=1\nremoved=1\nexcluded_frozen_suite=0\n"
    )


@pytest.mark.parametrize("sibling_prefix", ledger._ADD_ONLY_FROZEN_SUITE_PREFIXES)
def test_refresh_preserves_frozen_entry_bytes_and_values(
    join_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    sibling_prefix: str,
) -> None:
    _refresh_frozen_modules(join_repo)
    frozen = {prefix + "test_kept": 5.89 for prefix in ledger._ADD_ONLY_FROZEN_SUITE_PREFIXES}
    frozen[ledger._ADD_ONLY_FROZEN_WRITER_BASE_KEY + "@real-repo"] = 0.19
    sibling = sibling_prefix.replace(".py::", "_extra.py::") + "test_existing"
    module = join_repo / sibling.split("::")[0]
    module.write_text("# sibling outside exact module boundary\n", encoding="utf-8")
    before = _refresh_fixture_bytes({
        "pkg/tests/test_mod.py::test_before": 0.5,
        **frozen,
        sibling: 0.7,
        "pkg/tests/test_mod.py::test_after": 0.2,
    })
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    output.write_bytes(before)
    _write_junit(junit, [
        *(_refresh_case(nodeid, "9.9") for nodeid in list(frozen)[::2]),
        _refresh_case(sibling, "0.25"),
        _case("pkg.tests.test_mod", "test_after", "0.3"),
    ])
    assert _run(join_repo, output, junit, extra=["--refresh"]) == 0
    after = output.read_bytes()
    durations = json.loads(after)["duration_seconds_by_nodeid"]
    assert {k: v for k, v in durations.items()
            if k.startswith(ledger._ADD_ONLY_FROZEN_SUITE_PREFIXES)} == frozen
    for nodeid, value in frozen.items():
        line = ("    " + json.dumps(nodeid) + ": " + json.dumps(value) + ",\n").encode("ascii")
        assert line in before and line in after
    assert durations[sibling] == 0.25
    assert "preserved_frozen=9\n" in capsys.readouterr().out


def test_refresh_excludes_all_frozen_junit_nodes(
    join_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    _refresh_frozen_modules(join_repo)
    excluded = {prefix + "test_new" for prefix in ledger._ADD_ONLY_FROZEN_SUITE_PREFIXES}
    excluded.update(ledger._ADD_ONLY_FROZEN_REMOVED_NODEIDS)
    cases = [_refresh_case(
        nodeid + ("@real-repo" if nodeid == ledger._ADD_ONLY_FROZEN_WRITER_BASE_KEY else ""),
        "0.1",
    ) for nodeid in sorted(excluded)]
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    output.write_bytes(_refresh_fixture_bytes({}))
    _write_junit(junit, [*cases, _case("pkg.tests.test_mod", "test_control", "0.2")])
    assert _run(join_repo, output, junit, extra=["--refresh"]) == 0
    durations = json.loads(output.read_bytes())["duration_seconds_by_nodeid"]
    assert durations == {"pkg/tests/test_mod.py::test_control": 0.2}
    assert excluded.isdisjoint(durations)
    assert ledger._ADD_ONLY_FROZEN_WRITER_BASE_KEY not in durations
    assert "excluded_frozen_suite=13\n" in capsys.readouterr().out


def test_refresh_frozen_prefixes_cover_removed_nodes_and_writer_base_key() -> None:
    assert all(nodeid.startswith(ledger._ADD_ONLY_FROZEN_SUITE_PREFIXES)
               for nodeid in ledger._ADD_ONLY_FROZEN_REMOVED_NODEIDS)
    assert ledger._ADD_ONLY_FROZEN_WRITER_BASE_KEY.startswith(ledger._ADD_ONLY_FROZEN_SUITE_PREFIXES)
    assert ledger._ADD_ONLY_FROZEN_WRITER_BASE_KEY in ledger._ADD_ONLY_FROZEN_REMOVED_NODEIDS


def test_refresh_renders_canonical_bytes(join_repo: Path, tmp_path: Path) -> None:
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    output.write_bytes(_refresh_fixture_bytes({
        "orchestrator/tests/test_sort_swo_oracle.py::test_z": 5.89,
        "orchestrator/tests/test_critic.py::test_a": 2,
    }))
    _write_junit(junit, [
        _case("pkg.tests.test_mod", "test_z[日本語]", "0.25"),
        _case("pkg.tests.test_mod", "test_a", "0.1"),
    ])
    expected_payload = {
        "schema_version": 1, "unit": "seconds", "nodeid_count": 4,
        "duration_seconds_by_nodeid": {
            "orchestrator/tests/test_critic.py::test_a": 2,
            "orchestrator/tests/test_sort_swo_oracle.py::test_z": 5.89,
            "pkg/tests/test_mod.py::test_a": 0.1,
            "pkg/tests/test_mod.py::test_z[日本語]": 0.25,
        },
    }
    expected = (json.dumps(expected_payload, ensure_ascii=True, indent=2,
                           sort_keys=True, allow_nan=False) + "\n").encode("ascii")
    assert _run(join_repo, output, junit, extra=["--refresh"]) == 0
    assert output.read_bytes() == expected
    assert output.read_bytes().endswith(b"\n")
    assert _run(join_repo, output, junit, extra=["--refresh"]) == 0
    assert output.read_bytes() == expected


def test_refresh_canonicalizes_noncanonical_frozen_number_spelling(
    join_repo: Path, tmp_path: Path,
) -> None:
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    nodeid = "orchestrator/tests/test_critic.py::test_kept"
    output.write_bytes(_refresh_fixture_bytes({nodeid: 5.89}).replace(b"5.89", b"5.890"))
    _write_junit(junit, [_case("pkg.tests.test_mod", "test_new", "0.1")])
    assert _run(join_repo, output, junit, extra=["--refresh"]) == 0
    after = output.read_bytes()
    assert json.loads(after)["duration_seconds_by_nodeid"][nodeid] == 5.89
    assert b": 5.89,\n" in after
    assert b"5.890" not in after


def test_refresh_and_add_only_are_mutually_exclusive(
    join_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    before = _refresh_fixture_bytes({"pkg/tests/test_mod.py::test_existing": 0.5})
    output.write_bytes(before)
    _write_junit(junit, [_case("pkg.tests.test_mod", "test_new", "0.1")])
    with pytest.raises(SystemExit) as error:
        _run(join_repo, output, junit, extra=["--refresh", "--add-only"])
    assert error.value.code == 2
    stderr = capsys.readouterr().err
    assert "--refresh" in stderr and "--add-only" in stderr
    assert output.read_bytes() == before


def test_refresh_requires_existing_ledger(
    join_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    _write_junit(junit, [_case("pkg.tests.test_mod", "test_new", "0.1")])
    assert _run(join_repo, output, junit, extra=["--refresh"]) == 2
    stderr = capsys.readouterr().err
    assert stderr.startswith(_REJECTION_PREFIX)
    assert "cannot read existing ledger" in stderr
    assert not output.exists()


@pytest.mark.parametrize("kind", [
    "broken-json", "schema", "unit", "count", "bool", "negative", "nan", "infinite",
])
def test_refresh_rejects_invalid_existing_ledger_without_writing(
    join_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], kind: str,
) -> None:
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    payload = json.loads(_refresh_fixture_bytes({"pkg/tests/test_mod.py::test_existing": 0.5}))
    if kind in {"schema", "unit", "count"}:
        field, value = {"schema": ("schema_version", 99), "unit": ("unit", "minutes"),
                        "count": ("nodeid_count", 2)}[kind]
        payload[field] = value
    elif kind != "broken-json":
        payload["duration_seconds_by_nodeid"]["pkg/tests/test_mod.py::test_existing"] = {
            "bool": True, "negative": -0.1, "nan": float("nan"), "infinite": float("inf"),
        }[kind]
    before = b"{" if kind == "broken-json" else json.dumps(payload).encode("ascii")
    output.write_bytes(before)
    _write_junit(junit, [_case("pkg.tests.test_mod", "test_new", "0.1")])
    assert _run(join_repo, output, junit, extra=["--refresh"]) == 2
    assert capsys.readouterr().err.startswith(_REJECTION_PREFIX)
    assert output.read_bytes() == before


def test_refresh_check_and_coverage_use_refreshed_nodeids(
    join_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    _refresh_frozen_modules(join_repo)
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    collection = tmp_path / "collection.txt"
    frozen_new = "orchestrator/tests/test_critic.py::test_new"
    before = _refresh_fixture_bytes({"pkg/tests/test_mod.py::test_old": 0.5})
    output.write_bytes(before)
    _write_junit(junit, [
        _case("pkg.tests.test_mod", "test_new", "0.1"),
        _refresh_case(frozen_new, "0.2"),
    ])
    collection.write_text("pkg/tests/test_mod.py::test_new\npkg/tests/test_mod.py::test_missing\n"
                          + frozen_new + "\n", encoding="utf-8")
    args = ["--refresh", "--coverage-against", str(collection)]
    assert _run(join_repo, output, junit, extra=[*args, "--check"]) == 1
    assert output.read_bytes() == before
    assert capsys.readouterr().out.endswith("covered=1 total=3 ratio=0.333\n")
    assert _run(join_repo, output, junit, extra=args) == 0
    after = output.read_bytes()
    assert _run(join_repo, output, junit, extra=[*args, "--check"]) == 0
    assert output.read_bytes() == after
    assert capsys.readouterr().out.count("covered=1 total=3 ratio=0.333\n") == 2


def test_refresh_drops_failed_and_error_nonfrozen_entries(
    join_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    _refresh_frozen_modules(join_repo)
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    frozen = "orchestrator/tests/test_critic.py::test_failure"
    output.write_bytes(_refresh_fixture_bytes({
        "pkg/tests/test_mod.py::test_failure": 0.5,
        "pkg/tests/test_mod.py::test_error": 0.7,
        frozen: 5.89,
    }))
    _write_junit(junit, [
        _case("pkg.tests.test_mod", "test_failure", "9.9", failure=True),
        _case("pkg.tests.test_mod", "test_error", "9.9", error=True),
        _case("pkg.tests.test_mod", "test_pass", "0.25"),
        _case("pkg.tests.test_mod", "test_skip", "0.00456", skipped=True),
        _refresh_case(frozen, "9.9", failure=True),
        _refresh_case("orchestrator/tests/test_critic.py::test_pass", "0.2"),
    ], failures=2, errors=1)
    assert _run(join_repo, output, junit, extra=["--refresh"]) == 0
    assert json.loads(output.read_bytes())["duration_seconds_by_nodeid"] == {
        frozen: 5.89,
        "pkg/tests/test_mod.py::test_pass": 0.25,
        "pkg/tests/test_mod.py::test_skip": 0.0046,
    }
    assert capsys.readouterr().out == (
        "excluded_failure_or_error=3\nmode=refresh\npreserved_frozen=1\n"
        "replaced=0\nadded=2\nremoved=2\nexcluded_frozen_suite=1\n"
    )


@pytest.mark.parametrize("kind", ["empty", "all-failed", "duplicate-shards"])
def test_refresh_rejects_unusable_junit_without_writing(
    join_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], kind: str,
) -> None:
    output, junit = tmp_path / "ledger.json", tmp_path / "refresh.xml"
    before = _refresh_fixture_bytes({
        "orchestrator/tests/test_critic.py::test_kept": 5.89,
        "pkg/tests/test_mod.py::test_existing": 0.5,
    })
    output.write_bytes(before)
    cases = [] if kind == "empty" else [
        _case("pkg.tests.test_mod", "test_existing", "0.1", failure=kind == "all-failed"),
    ]
    _write_junit(junit, cases, failures=int(kind == "all-failed"))
    inputs = [junit]
    if kind == "duplicate-shards":
        second = tmp_path / "second.xml"
        _write_junit(second, cases)
        inputs.append(second)
    assert _run(join_repo, output, *inputs, extra=["--refresh"]) == 2
    stderr = capsys.readouterr().err
    assert stderr.startswith(_REJECTION_PREFIX)
    assert {"empty": "contains no testcases", "all-failed": "no usable testcases",
            "duplicate-shards": "duplicate nodeid"}[kind] in stderr
    assert output.read_bytes() == before


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
