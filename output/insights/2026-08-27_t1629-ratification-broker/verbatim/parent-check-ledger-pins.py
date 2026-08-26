"""Check whether a regenerated duration ledger preserves the T-1574 pins."""
import hashlib
import json
import pathlib

JOB = pathlib.Path(
    "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1629-ratification-broker")
WT = pathlib.Path(
    "/work/1/SFC/tanab/izanagi/.claude/worktrees"
    "/dev-wave-t1629-ratification-broker")

new = json.loads((JOB / "ledger-regen.json").read_text(encoding="ascii"))
old = json.loads(
    (WT / "orchestrator/tests/acceptance_duration_ledger.json").read_text(
        encoding="ascii"))

new_durations = new["duration_seconds_by_nodeid"]
old_durations = old["duration_seconds_by_nodeid"]

REMOVED = {
    "orchestrator/tests/test_critic.py::test_current_loader_rejects_non_exact_oracle_contract_ids[sort-swo-v3-corpus1-protocol2-checker2-grammar1-x2b6d45baab3f921208db25299b8622592c484dfb28bebeb8d2cf976fe38474f9-c436a66d9d5d5-tud88f98bc1991-f7ad0ac262561-a215b718a5bfe-suffix]",
    "orchestrator/tests/test_critic.py::test_current_loader_rejects_non_exact_oracle_contract_ids[sort-swo-v4-corpus1-protocol2-checker2-grammar1-x2b6d45baab3f921208db25299b8622592c484dfb28bebeb8d2cf976fe38474f9-c436a66d9d5d5-tud88f98bc1991-f7ad0ac262561-a215b718a5bfe]",
    r"orchestrator/tests/test_critic.py::test_sort_swo_non_axiom_kinds_have_dedicated_fixed_rendering[mutation-全 field snapshot が変化]",
    r"orchestrator/tests/test_critic.py::test_sort_swo_non_axiom_kinds_have_dedicated_fixed_rendering[protocol-固定長 protocol の異常]",
    "orchestrator/tests/test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
}
ADDED = {
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
SUITE_SETS = {
    "orchestrator/tests/test_critic.py::": (121, "1e8b4cd41b1e80708c79f247ef9c8ddb21d82bdc7e999cdc53e8713821cb0692"),
    "orchestrator/tests/test_p3_exploration_namespace.py::": (26, "db38065c3ebe9834490717df17f634af1c54dddab130d1eea0851723f3db7efa"),
    "orchestrator/tests/test_p3_s4_loop_sort.py::": (29, "f29aabf31c8ce1ee6b5e15435834ba6a535b2628f14ad186f342b2f47f6c2bed"),
    "orchestrator/tests/test_real_repo_serialization.py::": (42, "6fb7e97e2d410d716f45e641092794dafc9fc98717b663429bb9d18528db8874"),
    "orchestrator/tests/test_s1_direct_comparison.py::": (97, "ed1a63057f76b8807144943fff4ca7689fa7e0c2936a6c6512ef3ad5ffdce9d5"),
    "orchestrator/tests/test_s8b_materialization.py::": (30, "31ee53d57df57fdc3e8c350c97d9425afa4e9897aa2c716efe0608e822884f5b"),
    "orchestrator/tests/test_s8b_sort_swo_receipt.py::": (12, "a95979bd14e970ac6e08f1061a1c7b434549a3f4a3e3913d3ef6303b6a3a4ec2"),
    "orchestrator/tests/test_sort_swo_oracle.py::": (69, "7e97c114b313d8fccb97f486379745e060e3486a132de271a244e9c1e3f6d912"),
}


def identity(nodes):
    canonical = "".join("%s\n" % node for node in sorted(nodes)).encode("utf-8")
    return len(nodes), hashlib.sha256(canonical).hexdigest()


print("== 台帳の規模 ==")
print("  旧: %d node" % len(old_durations))
print("  新: %d node" % len(new_durations))

print()
print("== pin 1: removed node が不在か ==")
present = sorted(n for n in REMOVED if n in new_durations)
print("  違反:", len(present), present[:2])

print()
print("== pin 2: added 12 node の所要値 exact 一致 ==")
mismatch = []
for node, want in ADDED.items():
    got = new_durations.get(node)
    if got != want:
        mismatch.append((node.split("::")[-1][:60], want, got))
print("  不一致:", len(mismatch), "/", len(ADDED))
for name, want, got in mismatch:
    print("    %-62s want=%s got=%s" % (name, want, got))

print()
print("== pin 3: 8 suite の node 集合 identity ==")
bad = []
for prefix, want in SUITE_SETS.items():
    nodes = {n for n in new_durations if n.startswith(prefix)}
    got = identity(nodes)
    if got != want:
        bad.append((prefix.split("/")[-1][:46], want, got))
print("  不一致:", len(bad), "/", len(SUITE_SETS))
for name, want, got in bad:
    print("    %-48s want=%s got=%s" % (name, want, got))

print()
print("== 自己整合 ==")
print("  nodeid_count field:", new.get("nodeid_count"),
      "len(durations):", len(new_durations),
      "一致:", new.get("nodeid_count") == len(new_durations))
