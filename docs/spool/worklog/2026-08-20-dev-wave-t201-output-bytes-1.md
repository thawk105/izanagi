---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t201-output-bytes
seq: 1
title: "[T-201] 択 (b) を実装し output/insights/ の tracked bytes を約158MB削減した — 削除ではなく履歴保全した gzip 圧縮に置き換えた (コード + docs、branch worktree-dev-wave-t201-output-bytes、変異 matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0、受入 13682 passed / 96 skipped / 246.55秒・non-attributable 1件 (test_spool_fold.py の real corpus drift、main 側で本 wave と無関係))"
---

## 本文

- **実測が裁定時 (entry 74、2026-07-31、3437 files/151MB) から大きく陳腐化していた**。
  着手時点 (2026-08-19) の `output/` は 12153 files / 431MB (約3.5倍・2.7倍)。DW-S01 に従い
  brief 前に再実測した。
- **段2 codex plan の独立再検証が、親 (brief 起草者) 自身の pin 閉包検索の見落としを捕捉した**。
  親は広域 grep で `orchestrator/campaign/s6_proposal_rounds.py` 等を候補リストに出していたが
  深堀りせず見落とした。段2 plan が独立に再列挙し、`output/insights/2026-07-10_s8a-n1-provenance.json`
  (s6_proposal_rounds.py・t141_region_profile.sh・profiler_directive.py の実 consumer) と
  `output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json`
  (test_t338_submission_gate_unit2.py の read_bytes 対象) を実 consumer として検出した。
- **段3 レンズA が t419-probe-causality の「pin ではないが安全でない」構造を発見した**。
  `output/env/pegasus/t419-probe-causality/` (55.5MB) は FROZEN_MANIFEST 等の pin 対象では
  ないが、各 job の `manifest.json`/`parent-receipt.json` が同一 job 内の `result.json`・
  `cpuinfo-raw-*.txt` を path 参照するため、一部だけ圧縮すると job 内の相互参照が壊れる。
  部分圧縮不可と判断し、本 wave は scope 外へ後退させた ({{D:t201-output-bytes-history-preserving}})。
- **段6 レンズB が実データへの実際の dry-run で `docs/phase3.md` の隠れた依存を発見した**。
  `docs/phase3.md:308` と `:1364` (merge 後の行番号) が `output/insights/2026-07-08_s4b-loopstate-audit.json`
  と `output/insights/2026-07-20_wave2-mutation-ledger.json` を `check_docs.py` の `PATH_REF`
  実在確認対象として引用しており (`.gz` fallback なし)、圧縮すると `check_docs.py` が壊れる
  ところだった。docs 非改変を優先し、この2件も exclude-path へ追加して解決した。
  実データに対する dry-run を静的レビューと併用したことで発見できた — 静的レビューだけでは
  見落としていた可能性が高い。
- **変異 harness は commit 済み HEAD blob を基準に一時変異を注入する**。未 commit (untracked)
  の新設ファイルに対しては `--plan-only` ですら rc=2 で拒否される。実装を先に commit してから
  変異走行する、という順序が必要だった (次回以降の新設ツール wave への申し送り)。
- **受入 attempt 1 が attributable-red だった**。新設 `test_migrate_output_gzip.py` に自走
  harness (`__main__` が実際にテストを走らせる) も pytest 専用 allowlist 記載も無く、
  偽緑ガード (`test_plain_runner_coverage.py`) に検出された。fix (`pytest.main([__file__])`
  委譲を追加) で解消し attempt 2 で解決した。もう1件の赤
  (`test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`)
  は本 wave が一切触れていない real corpus (docs/worklog.md 等) 依存で、
  `check_acceptance_reds.py` が non-attributable と機械判定した。
- **最終確定 scope**: `output/insights/**` の非凍結ファイル (拡張子 json/jsonl/log/stdout/
  stderr/txt、4096 bytes 超)、除外4件 (上記2件 + N1 provenance + receipt-schema-v1.json)。
  実データ実測: 981 files / 186,126,812 bytes → 20,111,971 bytes
  (削減 166,014,841 bytes ≈ 158.3MB、圧縮率89.2%)。過去 commit の blob は書き換えていない
  ため元 bytes は `git show <旧commit>:<path>` で永久に取得可能 — 削減対象は HEAD の
  tracked bytes であり `.git` サイズやクローン転送量そのものではない。
- **scope 外へ送った残課題** ({{T:output-env-further-bytes-reduction}} として新規登録):
  (1) `output/env/pegasus/t419-probe-causality/` (55.5MB) — manifest/parent-receipt の
  path 参照を `.gz` 対応させる設計が別途要る、(2) `output/env/` の残り約16.5MB — pin 監査未実施、
  (3) `output/insights/**/*.md` (約40MB) — 逐語ログ的な .md と規範文書的な .md の分類が
  必要 (段3 レンズB 指摘)、(4) 今後の書き込みを恒久的に圧縮/抑制する仕組み — 3週間で
  151MB→431MB (2.7倍) に増えた再増殖ペースへの対策、本 wave は既存 backlog の一括削減のみ
  (規律5、段階導入)。

## 次の一手差分

### 完了

- [T-201] 択 (a)+(b) をどちらも実装した。(a) は entry 357 で land 済み、(b) は本 entry で完了。
  remaining: none
  base: cfb825c84873e4fef2607b7fecee857e3a0b4ed864acdce9afb76bbbcb192448

### 新規

- {{T:output-env-further-bytes-reduction}} **P2・新規**: `output/` のさらなる tracked bytes
  削減。t419-probe-causality の path 参照対応、output/env 残り約16.5MBの pin 監査、
  output/insights の .md 分類、恒久的な再増殖抑制の要否検討をまとめて次 wave の scope とする。
