# T-153(e) + T-154(2)(3) mutation ledger

- integrated commit: `9b26b3bd3acc10df95ef6ef6684a91d2ff3fa2ec`
- run date: 2026-07-29
- execution: repo root, single-run `flock`, `pytest -q -rf`
- restoration: every mutation used `git checkout -- <target>` and byte comparison
  against `git show HEAD:<target>`
- baseline hashes:
  - `tools/check_ai_provenance.py`:
    `0bc510b4e239394524aad209bd1c01ec4ff3d3d34938dec432c211bf8964970f`
  - `tools/check_docs.py`:
    `707f8f369086fe80cec9d296be8e9b3fad26a82ea08b7cc69149ec662e533195`

| ID | single mutation | expected / observed failed node | result |
|---|---|---|---|
| M1 | canonical parser から `--no-divider` を除去 | `orchestrator/tests/test_check_ai_provenance.py::test_m1_no_divider_changes_only_cab_finding` | KILLED, rc=1。CAB finding が非空から空へ変化 |
| M2 | private parser env から `GIT_CEILING_DIRECTORIES` を除去 | `orchestrator/tests/test_check_ai_provenance.py::test_canonical_parser_uses_fresh_ceiling_below_hostile_local_repo` | KILLED, rc=1。hostile local alias が分断 CAB を相殺 |
| M3 | parsed CAB 件数を boolean 化 | `orchestrator/tests/test_check_ai_provenance.py::test_co_authored_by_accepted_boundary[exact-duplicate]` | KILLED, rc=1。raw=2 / parsed=1 の偽拒否 |
| M4 | `AI-Agent: none` 正常 return から CAB finding を脱落 | `orchestrator/tests/test_check_ai_provenance.py::test_co_authored_by_rejected_boundary[cab-then-blank-then-ai]` | KILLED, rc=1。分断 CAB の拒否が消失 |
| M5 | history の `check_cab` を常時 true 化 | `orchestrator/tests/test_check_ai_provenance.py::test_cab_pre_policy_range_does_not_call_canonical_parser` | KILLED, rc=1。pre-policy parser no-call 境界を破壊 |
| M6 | `--message-file` の finding 合流から CAB を除去 | `orchestrator/tests/test_check_ai_provenance.py::test_message_file_always_rejects_split_cab_without_policy_history` | KILLED, rc=1。CLI が rc=1 から rc=0 へ fail-open |
| M7 | `all_limits` から `PROVENANCE_LIMITS` を除去 | `orchestrator/tests/test_check_docs.py::test_provenance_limit_rejects_9001_bytes` | KILLED, rc=1。9,001 bytes が rc=1 から rc=0 へ変化 |
| M8 | CAB が1件以上なら一致していても拒否 | `orchestrator/tests/test_check_ai_provenance.py::test_co_authored_by_accepted_boundary[cab-before-ai]` | KILLED, rc=1。承認外の過剰拒否を正例が検出 |

8/8 KILLED。診断文字列だけの差、SURVIVED、mask、combined mutation、
timeout、erratum はなかった。各走の `FAILED` node は事前登録と完全一致し、
各復元後は対象ファイルが integrated commit と byte-identical、tracked diff は空だった。
