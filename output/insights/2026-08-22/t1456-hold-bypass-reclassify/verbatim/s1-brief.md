# T-1456 brief — hold_inventory.py bypass_surface 誤報是正

## scope
`tools/hold_inventory.py` の test層 `bypass_surface` 中、id=`plain-python-runner` /
`pytest-noconftest` / `pytest-confcutdir-below-suite` / `direct-test-function-call` の
4 entry の `classification`/`effect`/`reason` フィールドを、現行二層guardの実挙動に
合わせて是正する。`orchestrator/tests/test_hold_inventory.py` の対応する golden-copy
(`_expected_inventory()` と `test_inventory_projects_exact_registered_source_sets` 内
`bypass_by_id` assertion) を追随させる。

## 確定済み前提 (親が実測済み、裁定不要)
- 現HEAD (worktree branch `worktree-dev-wave-t1456-hold-bypass-reclassify`) で
  対象4経路すべてが `GrowthTestHoldBypassRefused` で拒否されることを親が直接実行し確認済み
  (対象file: `orchestrator/tests/test_s8b_repo_scan_invariant.py`, plain_runner="manual",
  guard呼出し行 :55)。(a) `python3 <file>` rc=1 import時raise。(b) `pytest --noconftest <file>`
  rc=2 collection ERROR。(c) `pytest --confcutdir=<suite下>` rc=2 同上。(d) 直接import+呼出し
  rc=1 import時raise (呼出しへ到達すらしない)。control (通常pytest, token未設定) はrc=0で
  1 skipped (正常な保留)。
- `plain_runner="pytest-delegating"` file (`test_env_attestation.py`) は `__main__` 終端が
  `raise SystemExit(pytest.main([__file__, "-q"]))` で D360のAST照合契約どおりと静的確認済み。
- D360 (`docs/decisions.md:15662`) が二層guard (import時 `enforce_held_functions` +
  call時 `_wrap_held_function`, `orchestrator/tests/growth_test_holds.py`) の設計正本。
  実装waveは `docs/archive/worklog-phase3-0813-515.md` ([T-930], 2026-08-13, 8/8 KILLED)。
- 過去2wave (`docs/archive/worklog-phase3-0816-606.md` T-1222 2026-08-16、
  `docs/archive/worklog-phase3-0821-778.md` T-1222 2026-08-21) が同じ誤報を
  「scope外」として指摘のみで未着手のまま [T-1456] を持ち越していた。
- grep全域 (worktree除く): `"known-unresolved-bypass"` 文字列は
  `tools/hold_inventory.py` と `orchestrator/tests/test_hold_inventory.py` の2箇所のみ。
  他consumerなし。DW-O09 pin閉包: `tools/hold_inventory.py` のbytesをpinする
  FROZEN_MANIFEST等は存在しない (grep確認済み)。

## 不変条件 (絶対に破らない)
- `enforce_held_functions` / `_wrap_held_function`
  (`orchestrator/tests/growth_test_holds.py`) は1バイトも変更しない (規律2、D360)。
- どのtestが保留/実行されるか (受理集合) を変えない。純粋な報告メタデータの是正のみ。

## (P1) 新 classification 文言 — 親の provisional 裁定であり攻撃対象
`"known-resolved-bypass"` を軸に、`effect`/`reason` も「現在は拒否される」内容へ更新する
(例: `effect: "rejected-by-hold-guard"`、`reason` は import時/呼出し時どちらで
拒否されるかを反映)。`tracking: "T-930"` は維持 (解決したwaveへの正当なポインタ)。
段3で文言・field設計・簡潔性を攻撃対象にする。

## (P2) D347 (`docs/decisions.md:15303`) への抵触有無 — 親の provisional 裁定
D347は `bypass_surface` の**構造契約** (未解決なら未解決と明示する) を規範化するが、
個々entryのliteral値までは pin していない。classification値の更新はD347の趣旨
(正確性の担保) に沿うと見立てる。decisions.md自体の追記は不要と見立てるが、
段3で反証されれば段4でdecisions fragment追加を検討する。

## 変更面アンカー (実アンカー表)
- `tools/hold_inventory.py:110,118,126,136` (各entry classification)
- `tools/hold_inventory.py:112,120,130,138` (各entry effect — 更新候補)
- `tools/hold_inventory.py:113,121,131,139,481` (各entry reason — 更新候補)
- `orchestrator/tests/test_hold_inventory.py:446,456,464,476` (`_expected_inventory` 内 classification)
- `orchestrator/tests/test_hold_inventory.py:448,458,468,480` (同 effect)
- `orchestrator/tests/test_hold_inventory.py:449-451,459,469-471,481-483` (同 reason)
- `orchestrator/tests/test_hold_inventory.py:595,603,611,619` (`bypass_by_id` assertion内 classification)
- `orchestrator/tests/test_hold_inventory.py:597,605,613,621` (同 effect)
- `orchestrator/tests/test_hold_inventory.py:598,606-607,614-615,622-623` (同 reason)

## 成果物影響 (DW-G05)
放置した場合: D347が「保留状態はユーザーの判断入力そのもの」と規範化する
hold_inventory出力が、既に閉じたbypassを "unresolved" と偽り続け、これで3度目となる
将来waveの無駄な再調査コストを強いる。是正すれば出力は実態と一致する。

## 並列分割方針
単一 Codex 実装単位 (対象2 file、所有非重複なし、依存順不要)。段5は1本のみ。

## 環境
pegasus02 (`PEGASUS_LOGIN`)。テスト実行は `tools/run_tests.py` 経由必須
(pytest・buildの直接起動禁止、単一file/nodeidも同じ — `AGENTS.md` 参照)。
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify`
branch: `worktree-dev-wave-t1456-hold-bypass-reclassify`
