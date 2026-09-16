---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2634-nonsilo-floor-lift
seq: 1
title: [T-2634] 非 silo の within-run floor の保留を既取得の較正 4 対に限って解除し文書登録した — 依頼が名指した between-run の実測は D1373 の関門で起動できず未実施 (docs のみ、branch worktree-dev-wave-t2634-nonsilo-floor-lift、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- **ユーザー裁定 D2044 項 12 の実装。** 解除の範囲は実測で示された 4 対 (tictoc / rr50・rr95、mocc / rr50・rr95) の
  accepted 較正に限り、現行 phase doc の 8b 節へ silo の rr95 / rr5 と同じ形で登録した。値は insight の散文でなく
  record 自身 (`saturation.miss_rate_at`、`noise_floor.cv`) から取り、4 件とも n=10・records 1,000,000・
  CCBench `511c9538`・`pinned_clean=true` であることを jq で確かめた。設計判断は {{D:nonsilo-within-run-floor-lift}}。
  詳細は `output/insights/2026-09-16/t2634-nonsilo-floor-lift/README.md`。
- **依頼の前提が実測で覆った。** 依頼は「測定は既存の `between_run_floor.py --protocol {tictoc,mocc}` を計算ノードで
  走らせる」としたが、login node で述語を実測すると現行 pin の checkout で `_protocol_source_has_trace_hook_evidence_only`
  は silo=True / mocc=False / tictoc=False、`BASELINES` は {silo, mocc}、`--protocol tictoc` は引数解析で拒否される。
  mocc は `main()` の D1373 関門 (規律 2 の関門) が build 前に拒否する — driver の rc=2 と `ValueError` は実装から
  導いた静的帰結で、計算ノードでの実走はしていない。**関門を緩めず、pin も変えず、実測は行わなかった。**
  再開の必要条件 (mocc は hook を含む pin、tictoc は hook 移植 + baseline 対応) は決定に書いた。
- **「embargo」は code に無い。** 実体は worklog / insight の散文と、phase doc に非 silo の 4 record が未登録である状態。
  `layer3_report.py` の照合は genome 付き record を protocol 問わず一致させ、非 silo を弾く分岐は無い。ただし段 3 の
  レンズ B が示したとおり、層 3 の走査は `calibration/` 直下と契約 pin だけで `registered/` を再帰しない (D1508) ので、
  **文書登録は report 消費の開通ではない。** silo の rr95 / rr5 も同じ状態で、登録の水準はそれと揃えた。
- **段 3 で親の brief を 3 点訂正した。** (1) 「D1360 が禁じるのは性能比較値だけ」は逐語より狭く撤回し、登録根拠を
  D2044 項 12 の用途限定解除に一本化した。(2) 「pin を進めれば関門を通る」は条件不足で、実 checkout の CMake SOURCES
  列挙 file に 3 証拠が揃う必要があると改めた。(3) 「起動できない baseline は規律違反」の一般論は現行 mocc が反例で撤回。
  段 2 plan の「mocc rr50 の LLC miss / CV は一次資料に無い」は README 単独の限界で、record にある値
  (14.821% / 1.4348%) を採った。
- **scope 外として触らなかったもの:** `docs/pegasus-runbook.md` の「登録済み calibration は 2 件」(環境契約が pin する
  2 件の意味で、registered の現物は 8 件) の限定訂正、層 3 report への接続 (契約世代の登録・活性化)、`BASELINES` への
  tictoc 追加、非 silo rr5・cicada の較正取得。
- **エージェント工数:** codex 子 3 本 (段 2 plan 1、段 3 consult 2、いずれも gpt-6-astra / medium、read-only)。
  実装面差分ゼロのため段 5・6 の子は起動していない。変異 matrix は実装面差分ゼロで免除。
- **検査 (記録前に実走):** 作業木 (docs 差分を含む未 commit 状態、base 8f17db598) で `tools/check_docs.py` rc=0、
  `tools/spool_fold.py --dry-run --show-diff` rc=0。実 repo の docs を読む焦点 test 2 file
  (`orchestrator/tests/test_check_docs.py`、`test_spool_fold.py`) は headroom 判定で計算ノードへ dispatch され
  (Pegasus request 1949.nqsv、bnode012、Elapse 22 秒) **741 passed / 3 skipped**、失敗 0。
- **受入全走**は本記録 commit を含む最終 tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない。
  本エントリの作成時点では未実施である。

## 次の一手差分

### 完了

- [T-2634] D2044 項 12 に従い、非 silo の within-run floor の保留を既取得の accepted 較正 4 対
  (tictoc / rr50・rr95、mocc / rr50・rr95) に限って解除し、現行 phase doc の 8b 節へ登録した。
  完了範囲は用途限定の文書登録であり、性能比較・床値本走・層 3 report への接続を含まない。
  between-run の実測は D1373 の関門で起動できず未実施で、再開の必要条件は決定に記した。
  remaining: none
  base: 9a5d7b0ee83174d0ba1e1225351ff033715af8dc879f08f02b39008f6da56813
