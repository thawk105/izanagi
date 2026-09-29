# DW-O09 pin 閉包 (Explore 子 sonnet の報告の要約、親が P5 の根拠 file:line を別途確認済み)

対象: orchestrator/campaign/s8b_holdout_freeze.py (変更前 sha256 5a8798d482631918b2113c778f7eaf8c4c5ddf5b7203b582eaac1469694e978a)

## 分類
- worktree bytes 照合: s8b_holdout_freeze.py:945-967 `_verify_source`、呼出し :1026。:1015 で `_freeze_hold.HELD` なら skip (freeze_verification_hold.py:13 HELD=True、check id
  `s8b-holdout.generator-implementation-bytes`)。v1 記録値 1910fff… は既に現物と不一致 (親が実測)。
- frozen_at_head blob 照合: s8b_ratified_freeze.py:1095-1103 (V1b)。v2 g1 (output/s8b-freeze/holdout_freeze.v2.g1.json、generator sha = 5a8798d4…、frozen_at_head cc82edc8) の権威。
- 歴史記録: t080_freeze_migration.py:113-123 METADATA_SPECS (v1 記録値 1910fff… の pin)、test_frozen_artifacts.py:41-88 FROZEN_MANIFEST (JSON 出力の pin)、
  decisions.md の行番号言及 (prose)。
- 動的 (その場で読む): test_s8b_oracle_driver.py:5221-5242、:5245-5284、s8b_v2_freeze_fixture.py:759-770、test_s8b_holdout_freeze.py:286-294、test_s8b_budget_approval_preflight.py:264。
- 無関係: test_official_perf_closure.py (対象 `_validate_floor_inputs`)、test_ccbench_spawn_sites.py:280-282 (subprocess 起動数。enumerate 経路を触れば要注意)。

## live scan を実行する経路
- s8b_ratified_freeze.py:3680 `launch_validate` 内 `_hf.search_repository(root, exempt_exact=...)`。s8b_holdout_freeze.py 自身は免除外 → 自己汚染に注意。
- t080_freeze_migration.py:2256 `_verify_holdout_live_scan`、:1891 `_assert_receipt_does_not_pollute_scan`、:1718 draft の searcher。

## source guard (自己汚染)
- test_s8b_repo_scan_invariant.py:18-35 (実 repo 走査、KNOWN_CONJUNCTION_HITS 空を要求)、test_s8c_preregistration_invariant.py:623-643。
  両方 growth hold (growth_test_holds.py:200-202、:240-245、解除はユーザー指示のみ)。
- 禁止: 軸 key と具体値を連続 literal で書くこと。現行は RRATIO_KEY = "ycsb_" + "rratio" (:64) 等の連結で回避。

## 既存 test (全て test_s8b_holdout_freeze.py)
- :407-424 `_derive_required_literal` が 1 走査 12 回。
- :427-451 re.compile spy で search 5 回。
- :645-677 memo hit で re.compile 0 回・`_reference_scan_one` (:917-953) と bytes 一致。
- :985-1097 `_prefilter_equivalence_fixture` + `test_prefilter_report_exactly_matches_slow_path` — D513 三段分離: optimized / 中間層 (`_derive_required_literal` 無効化) /
  完全 slow (`_scan_one` → `_reference_scan_one`) で search 回数 0 / 5 / 9、reference 呼出し ["H1","H2","rr50-positive-control"]、5 parametrize (files / exempt-none / empty-mapping / hash-match / hash-mismatch)。
- 他: :388-404、:454-622、:680-691、:956-982 (8192 byte 以降の hit)、:1100-1196 (monkeypatch された式からの導出、snapshot 1 回)。
