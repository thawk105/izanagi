---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1456-hold-bypass-reclassify
seq: 1
title: '[T-1456] hold_inventory.py の bypass_surface 4 entry を実効guard状態へ再分類した (コード+テスト、branch worktree-dev-wave-t1456-hold-bypass-reclassify、変異matrix = baseline PASSED・MUT-1〜2 2/2 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- `tools/hold_inventory.py:107-141` の test層 `bypass_surface` は、plain runner・
  `--noconftest`・`--confcutdir`(suite下)・direct callの4経路を `known-unresolved-bypass`
  と報告していたが、2026-08-13 [T-930] (D360) が実装した二層guard
  (`enforce_held_functions`/`_wrap_held_function`) で既に閉じている誤報だった。
  過去2wave (2026-08-16 T-1222 archive worklog-phase3-0816-606、2026-08-21 T-1222
  archive worklog-phase3-0821-778) が「scope外のreal所見」として指摘のみで未着手のまま
  持ち越していた。両archiveとも「本waveが作った穴ではない」として起票のみで終わっていた。
- 着手前に `tools/hold_inventory.py`/`orchestrator/tests/test_hold_inventory.py` の他wave
  編集有無を確認した (git log・全worktree grep、該当なし)。
- 過去の指摘を鵜呑みにせず、現HEADで4経路を親が自ら実行して裏取りした
  (対象: `orchestrator/tests/test_s8b_repo_scan_invariant.py`, plain_runner="manual")。
  (a) `python3 <file>` rc=1・import時 `GrowthTestHoldBypassRefused`。
  (b) `pytest --noconftest <file>` rc=2・collection ERROR同exception。
  (c) `pytest --confcutdir=<suite下> <file>` rc=2・同上。
  (d) 直接import+関数呼出し rc=1・importの時点で例外 (呼出しへ到達せず)。
  control (通常pytest、release token未設定) はrc=0・1 skipped (正常な保留)。全て現行guardで
  拒否されることを確認し、誤報を確定した。
- 段2 codex plan (`known-resolved-bypass` 案) を段3敵対相談2レンズが攻撃した。sol
  レンズが、提案文言がguardの保証範囲 (D360の「適用範囲」節が明記する、同一process内
  `__wrapped__`直呼び・guard再束縛は対象外という限定) を越えて一般化していたと看破し、
  `plain_runner="pytest-delegating"` file では拒否の機序が (import時raiseでなく)
  委譲後のpytest session側のgraceful skipになる点も指摘した (real、採用)。luna
  レンズは、T-1456自体が2026-08-16に [T-1267] として起票された同一事案の後継である
  ことを検出した (real、記録面で採用) — 本fragmentの次の一手差分で両IDを完了させる。
  両レンズともD347 (bypass_surfaceの構造契約) との抵触はrefutedと判定し、decisions.md
  への追記は不要と確定した。
- 段4裁定で `classification: "known-guarded-bypass"`・`effect: "blocked-by-hold-guard"`
  へ是正し、reasonはoutcome指向 (「exact release tokenが無い限りblocked」) とし機序を
  過度に断定しない方針とした。段6敵対レビュー2本のうちreviewBが、裁定で求めた
  「T-930により解決済み」の明示が実装のreasonに反映されていないとreal所見を出し、
  fix1で4 entry全部のreason先頭に「T-930 closed this bypass: 」を追加して是正した
  (reviewBのnit「held test execution is blocked」への言い換えも同時に採用)。reviewAは
  所見ゼロ (golden-copy 3箇所の byte-for-byte 一致を独立確認)。
- Pegasus計算ノード (gen_S) が本wave段6後半で severe に混雑した。他セッション
  (lease coordination compute saturation / cross-session) との連携で、
  `dev_wave_wait.py acceptance` の `preclaim-history-provenance` 段が
  300秒timeoutで子processをSIGKILLする際にPBS jobをqdelせず孤児化する設計バグが
  原因の一つと判明した (孤児14件を別セッションがqdel済み)。本waveは同経路
  (`dev_wave_wait.py acceptance`) を未使用のため直接の影響は無いが、fix連絡が
  来るまで新規の受入投入を控える方針で協調した。`tools/check_ai_provenance.py` の
  直接呼出しは同じ孤児化経路ではないと実測で確認し (timeoutした過去request ID
  4件がqstatから既に消滅、`dispatch_compute.py`の`_best_effort_qdel`による後始末と
  判断)、これをpeerへの裏取り材料として報告した。

## 次の一手差分

### 完了

- [T-1456] hold_inventory.py の bypass_surface 4 entry (`plain-python-runner`・
  `pytest-noconftest`・`pytest-confcutdir-below-suite`・`direct-test-function-call`) を
  `known-unresolved-bypass` から `known-guarded-bypass`/`blocked-by-hold-guard` へ
  再分類し、`test_hold_inventory.py` の golden-copy を追随させた。guard本体
  (`enforce_held_functions`/`_wrap_held_function`)・受理集合は無変更。
  remaining: none
  base: 0d22ffbd1ebb1121b6c996ff6120b0b4ceeaa7e750df9255b2191a7a5b03dfe1
- [T-1267] [T-1456] と同一事案 (2026-08-16 起票の先行ID)。[T-1456] の対応で同時に解消。
  remaining: none
  base: 4c644ae9501b5c6162aaadccdd19722862f1a7704c29f1cbae51992fa1d56ed2
