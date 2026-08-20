---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t183-codex-failure-recovery
seq: 1
title: '[T-183] F43/F45型の早期分類・retry上限・fail-closed回復を実装した (コード+テスト、branch worktree-dev-wave-t183-codex-failure-recovery、変異matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0、受入は T-1053 の既知バグでブロック中・land 未達)'
---

## 本文

- 2026-08-03 裁定 (着手可、scope1点除外) から17日 carry stub のままだった T-183 に着手。
  着手前に `docs/failures.md` の F43/F45 最新記述を再読し、command 指定どおり scope から
  model×reasoning 非対応組の事前検証を除外した ([T-371] 裁定により [T-189] 系許可リストが所有)。
- 段1 brief 材料調査で fork 1 本が調査結果でなく無関係な待機文言を返す誤動作をした
  ({{F:fork-misacts-as-manager}} 参照)。新規 fork として再投したが、新規 fork は旧 fork の
  ツール呼び出し履歴を継承しないため、明示的に「記憶を捏造せず一から再調査せよ」と指示して
  回避した。実害なし。
- 段3 敵対相談 (正しさ境界 / 整合実効性の2レンズ) が、親 brief の P1 前提
  「既知の F43/F45 事例は全て read-only sandbox 段で発生し workspace-write 例は0件」を
  `docs/failures.md` の実測 (2026-08-18 実装子・2026-08-20 fix子2回、計3件のF43実例) で
  反証した。ただし `failure_class` 分類は `_seal_attempt()` 内で全 sandbox 共通に動く設計だった
  ため、アーキテクチャへの影響はなくテスト網羅性の拡張 (workspace-write × 各分類のテスト追加) で
  閉じた。前提の誤りが実装方針を変えない形で早期に検出された例。
- 段3・段6 で計3回、段2プランの「`docs/dev-wave/operations.md` の docs 3層 byte 予算が
  既に超過している」という主張を親が独立に `python3 tools/check_docs.py` (rc=0) で反証した。
  静的な byte 数再計算より実際に checker を実行する方が信頼できることを再確認した。
- 段6 敵対レビュー2本 (実装差分の正確性 / 回帰・境界条件) はいずれも所見ゼロ寄り
  (前者は完全に所見ゼロ、後者は6所見 refuted・1所見 real)。real 所見は
  `_reserve_receipt_slot()` (既存の crash-recovery 機構、R12) が、新 exact-field-set により
  「invalid」と判定される旧 schema receipt を再実行時に上書きしうるという指摘だった。
  これは段4裁定 (旧receiptの非互換は意図的、移行シムは作らない) の直接的帰結であり、
  job_id 衝突が実際に起こるのは「同一prompt再投」recovery パターン (元の receipt は
  そもそも失敗記録) に限られるため、fix は投じず既知の限定的帰結として本エントリに記録するに
  留めた。
- 変異matrix登録時、M1 (F45 fail-closed分岐無効化) と M3 (F43のheading欠落prefix除去) の
  初回 expected_nodes 見積りが不完全で MISMATCH になった。原因を直接コード調査で特定
  (fake dispatch の `retry_reject` モードは「raw byte数不足」と「heading欠落」の**両方**を
  同時に満たす出力を書くため、`_classify_failure` の `all()` 判定がどちらの prefix を削っても
  影響を受ける) してから expected_nodes を完全集合へ訂正し、再走で 4/4 KILLED を得た。
  DW-M08 の「初回を probe と明記し erratum を残して再登録」を実地で踏んだ例。
- 変異harness起動時の罠2件 (次waveへの申し送り): runner argv へ `-rf` を明示追加しないと
  `DW-M08 の -rf を含まなければならない` で rc=2 (DW-M08 に既に明記されていたが初回投入時に
  見落とした)、runner は harness と同じ Python executable (`sys.executable` の絶対パス、
  今回は `/usr/bin/python3`) で起動しないと `同じPython executableに束縛する必要がある` で
  rc=2 (こちらは docs 未記載)。
- **受入全走を2回投入し、いずれも同一の3件の赤 ([T-183] の差分に帰属しない) で
  `check_acceptance_reds.py` が `probe worktree is not clean, including ignored files`
  (rc=2、[T-1053] として既に裁定済み・未実装の既知バグ) を返し、受領証を発行できなかった。**
  赤3件は (1)(2) `test_codex_worker_launch.py` の `test_launcher_failure_diagnostic_reports_all_visible_failures_and_guard`・
  `test_thread_missing_after_grace_kills_process_group` (両方とも `codex_exit_code=-9`、
  wall-clock 予算 3 秒という攻撃的なタイミング前提テスト、直前 wave の worklog entry 725 (T-755)
  が対照実験で確認済みの環境要因) と (3) `test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`
  (単独再走で直接確認: `docs/archive/worklog-phase3-0813-537.md` 内の `[T-139]` 固定テキストに
  対する期待 SHA256 が、`[T-139]` が別 wave (worklog entry 720) で完了済みになった現在の
  real corpus 解決結果と食い違う、main 側の pre-existing drift。同型が同日の worklog entry 723
  ([T-201]) でも「non-attributable、本waveと無関係」と記録されている)。
  DW-O18 「rc=2 は判定不能で非帰属の根拠にしない」に従い rc=2 を非帰属の確認として扱わず、
  かつ各赤を個別に単独再走・直接コード読解で非帰属と確認したうえで、
  3回目の機械的な再試行 (同じ決定的な赤を再現するだけの見込みが高い) はせず停止した。
  T-183 自体の実装・レビュー・変異検証は完了しており、受入は [T-1053] の解消または
  該当赤の解消 (main 側) を待って再投入すればよい状態にある。

## 次の一手差分

### 更新

- [T-183] **P1・実装完了・受入は [T-1053] でブロック中**: `tools/codex_worker_launch.py`/
  `tools/dev_wave_codex.py` へ `failure_class`
  (`f43_fragment`/`f45_missing_output`/`other`/None、seal 後に不変な観測値だけから導出する
  純粋関数) を追加し、F45型は同一job内での追加試行をfail-closedし、F43型は既存retryを妨げない
  設計を実装した。workspace-writeの`--max-attempts>1`拒否と`_seal_attempt`のaccepted 7条件AND
  は無改修。統合commit `ac52eae3` (branch `worktree-dev-wave-t183-codex-failure-recovery`)。
  テスト新設10関数(15ケース、workspace-write×分類の網羅・late limit trigger後の
  failure_class保持回帰・既定値1でのobservability・positive control3種を含む)、
  変異matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0。受入全走2回とも
  [T-1053] (既知・裁定済み・未実装) でブロックされ受領証未発行。次の一手は受入の再投入
  ([T-1053] 解消後、または該当赤が別 wave の対応で解消した後)。
  base: 72a3732e19231ef094307a36dd084b089be4041072faa9143cfe145ba5513765
