---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1141-spec-single-block
seq: 1
title: [T-1141] spec層でA3-3単一block契約を承認前に発火させた (コード+テスト、branch worktree-dev-wave-t1141-spec-single-block、変異matrix = baseline PASSED・1/1 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=child-green)
---

## 本文

- `validate_reviewed_spec` が A3-3 単一block契約の実装本体 `_validate_schedule` を未呼出しのまま
  (早期returnによる迂回ではない) だった欠陥を修正。同関数を公開名 `validate_schedule` へrename
  (4箇所) し、`validate_reviewed_spec` の `build_schedule` 成功直後へ呼出しを追加、2 block spec
  が承認前に拒否される負例テストを新設した。一次資料 =
  docs/archive/worklog-phase3-0816-565.md:482-488。
- 段2 codex plan が既存回帰 (`test_v1_two_block_manifest_is_rejected_at_build_and_verify` の
  build側がspec承認を経由するため新設チェックが先に発火し `ManifestError` 期待が壊れる) を発見、
  `manifest.build_manifest(...)` 直接呼出しへ修正して対応。
- 段3敵対相談2レンズ (sol/luna)・段6敵対レビュー2レンズ、いずれもreal 0件で収束。sol が
  `tools/codex_reasoning_ab.py:5069` 系の同名無関係一致を追加発見、rename対象外境界へ追加。
- 変異matrix: baseline PASSED (101 passed)・1/1 KILLED・SURVIVED 0・MISMATCH 0 (対象=新規呼出し
  のno-op化、単一理由性を実測確認)。
- local main取り込みで積集合3ファイル (main側 T-1381相当の docstring pin + [T-1142]系の driver
  変更) が発生し、`dev_wave_wait.py acceptance` の自動merge委任が `merge-message-provenance`
  (rc=70) で1回落ちた。手動 `git merge --no-ff --no-commit` + Codex `role=author` 合成監査
  (stale docstring参照2箇所を `_validate_schedule`→`validate_schedule` へ修正) で解消し、
  受入 verdict=child-green・red 0件・flake 0件。

## 次の一手差分

### 完了

- [T-1141] spec層でA3-3単一block契約を承認前に発火させ、既存回帰も併せて修正した (コード+
  テスト、branch worktree-dev-wave-t1141-spec-single-block、変異matrix = baseline PASSED・
  1/1 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=child-green)。
  remaining: none
  base: 3fc74eb44c69a3f574a26ad499fb24afea9feeb57da9a917bafae7dba4b6a74f
