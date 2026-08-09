---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t677-relay-reach
seq: 2
---

## 新規

### {{F:in-tree-temp-test-tree}}. 新規テストが repo 作業ツリーへ一時 test file を作り、tree 安定性 guard と競合した [手順漏れ]

- 事象: 段 6 の fix 1 巡目後、親の組み合わせ実走で
  `test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root`
  が赤になった (1 failed, 25 passed)。新規テストが subprocess pytest 用の一時 test file を
  `orchestrator/tests/.failure-digest-states-<rand>/` へ作っており、guard の観測窓に
  未追跡ファイルとして写り込んだ。
- 根本原因: subprocess pytest に**実 conftest の自動 discovery を通す**という要件を、
  一時 test tree を `orchestrator/tests/` 配下へ置くことで満たしていた。
  作ってすぐ消していたため単独走行では通り、**xdist 並列で guard と時間が重なったときだけ赤**になる。
  fix 前の実装も同じ在処に作っており、偶然通っていた潜在フレークが顕在化した。
- 恒久対応: 一時 test tree を `tmp_path` 配下へ移し、実 `conftest.py` を一時 rootdir へ
  コピーして自動 discovery を満たす。全 subprocess に `PYTHONDONTWRITEBYTECODE=1` を設定し、
  一時 root が repo 配下でないことを assert する
  (`orchestrator/tests/test_pytest_failure_digest.py` の E2E / 終了形 fixture)。
  既存の repo tree 安定性 guard がこの型を fail-closed で検出する。
- 再発検知: 実走の直前・直後で `git status --porcelain` が完全一致することを子の完了条件に入れ、
  親は**単一ファイルではなく guard を含む組み合わせ**で実走する。
  単一ファイル実走の緑は本型を検出しない (今回、子は 14 passed / 26 passed を報告していたが
  組み合わせ実走で初めて赤が出た)。
