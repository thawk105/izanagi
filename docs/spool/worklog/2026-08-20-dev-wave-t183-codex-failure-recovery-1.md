---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t183-codex-failure-recovery
seq: 1
title: [T-183] F43/F45型の早期分類・retry上限・fail-closed回復を実装し、3日止まっていた取り残し branch を別 context で再開して受入まで進めた (コード+テスト、branch worktree-dev-wave-t183-codex-failure-recovery、変異matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0)
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
- **受入全走を3回投入し、3回とも同一の3件の赤 ([T-183] の差分に帰属しない) で
  `check_acceptance_reds.py` が `probe worktree is not clean, including ignored files`
  (rc=2、[T-1053] として既に裁定済み・未実装の既知バグ) を返し、受領証を発行できなかった。**
  赤3件は (1)(2) `test_codex_worker_launch.py` の `test_launcher_failure_diagnostic_reports_all_visible_failures_and_guard`・
  `test_thread_missing_after_grace_kills_process_group` (両方とも `codex_exit_code=-9`、
  wall-clock 予算 3 秒という攻撃的なタイミング前提テスト、直前 wave の worklog entry 725 (T-755)
  が対照実験で確認済みの環境要因。3走とも寸分違わず同じ2件が失敗しており、現在の計算ノード
  割当てでは flake というより構造的に厳しいタイミング予算になっている可能性が高い) と
  (3) `test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`
  (単独再走で直接確認: `docs/archive/worklog-phase3-0813-537.md` 内の `[T-139]` 固定テキストに
  対する期待 SHA256 が、`[T-139]` が別 wave (worklog entry 720) で完了済みになった現在の
  real corpus 解決結果と食い違う、main 側の pre-existing drift。同型が同日の worklog entry 723
  ([T-201]) でも「non-attributable、本waveと無関係」と記録され、さらに同日 land 済みの
  [T-222] (entry 729、fold dry-run で発見) は同じ赤 1 件だけの受入で checker が
  non-attributable 判定に成功している — 赤が 1 件なら通る checker が、赤 3 件 (本wave) では
  probe cleanliness 検査そのものに失敗する形で壊れている可能性を示唆する)。
  DW-O18 「rc=2 は判定不能で非帰属の根拠にしない」に従い rc=2 を非帰属の確認として扱わず、
  かつ各赤を個別に単独再走・直接コード読解で非帰属と確認したうえで、3回とも寸分違わず
  同一の3件が再現し収束の見込みが薄いため、4回目の機械的な再試行はせず停止した。
  T-183 自体の実装・レビュー・変異検証は完了しており、受入は [T-1053] の解消または
  該当赤の解消 (main 側) を待って再投入すればよい状態にある。

### 2026-08-23 の再開 (別 context)

- 2026-08-22 23:48 から止まっていた取り残し branch を fresh context で再開した。着手時点で
  branch は local main から 248 commit 遅れており、まず main
  `c301c4fdb0bc7997d729fe0de80f8b99356a6012` を取り込んだ。競合は 3 hunk
  (`tools/codex_worker_launch.py` の定数定義部 1 件、
  `orchestrator/tests/test_codex_worker_launch.py` の finalization 締切テスト 2 件) で、
  いずれも両側 union として解消した。後者は main 側が受理締切を 3 区間へ分けた改修で
  期待値を `accepted is True` / `limit_trigger is None` へ改めており、wave 側が足していた
  `failure_class is None` の 1 行だけを併置する形になった。
- **この競合解消は Codex 実装子へ委任できなかった。** conflict marker が launcher 自身の
  source に載るため `tools/dev_wave_codex.py --stage author` が import 時に SyntaxError で
  停止し、marker 除去後も authority-snapshot が未 commit の `docs/dev-wave/operations.md` を
  拒否した。暫定 message で merge を commit してから合成監査子を投入し、監査結果を
  amend で畳み込む順序で回した。
- **合成監査 (Codex role=author) が実際の退行を 1 件検出した。** wave 側が
  `failure_class` を attempt receipt の必須 field にしたため、main 親が読めていた schema
  V1〜V3 の receipt (この field を持たない) が `_validate_attempt` の閉じた field 表で
  拒否されるようになっていた。受理集合が意図せず狭まる型の退行で、テストは緑・競合も
  出ない箇所だった。V4 は必須のまま維持し、V1〜V3 に限り field 有無の両形式を受理して
  sealed artifact から内部再導出する形へ修正し、回帰テストを 3 本追加した。
  **「競合が無い automerge でも合成は保証されない」の実例がまた 1 つ増えた。**
- 2026-08-20 時点で受入をブロックしていた `check_acceptance_reds.py` の probe cleanliness
  検査は、その後 main 側で受入経路から外された ([D662] 系の運用簡素化)。

### 受入 1 回目が暴いた自分のバグ 2 件 — 2026-08-20 の非帰属判定は誤りだった

- 受入全走 (計算ノード 48 並列、`raw_child_rc=1`) の赤 5 件のうち **4 件が本 wave 起因**
  だった。非帰属は `test_dev_wave_cleanup.py::test_landed_attached_worktree_is_removed[unlocked]`
  の 1 件だけである。
- **バグ A**: F45 fail-closed の `AttemptLoopError` 送出を、attempt ループの終端判定
  (`accepted or limit_trigger is not None` の break、`attempt_index >= max_attempts` の
  continue、retry admission limit) より**前**に置いていた。このため次の attempt が構造的に
  起きない走行 (`--max-attempts` 既定の 1) や launcher 自身の予算執行で終わる走行まで
  rc=1 (not_accepted) が rc=2 (launcher_error) へ横取りされていた。送出を全終端判定の
  後ろへ移した。F45 fail-closed の目的は「同一 prompt での**次の** attempt を止める」ことで
  あり、止めるべき retry が無い走行で発火するのは仕様の取り違えだった。
- **バグ B**: `_validate_attempt` が `_validator_failures()` を無条件に再読していたが、
  `_seal_attempt` は output file 不在時に `None` を封じており、「file 不在」の扱いが
  seal 側と検査側で非対称だった。検査側を seal 側へ揃えた。
- **2026-08-20 の記録の訂正**: 当時 3 回の受入で毎回同じ 2 件
  (`test_launcher_failure_diagnostic_reports_all_visible_failures_and_guard`・
  `test_thread_missing_after_grace_kills_process_group`) が落ちたのを
  「共有 login node の負荷による timing flake、環境要因」と結論し非帰属としたが、
  **これは誤りだった。** 実際は上記バグ A / B であり、`codex_exit_code=-9` という
  署名の一致だけを根拠に既知の環境要因パターンへ当てはめてしまった。
  「3 走とも寸分違わず同じ 2 件」という当時の観測そのものが、flake ではなく決定的な
  バグであることを示していた — 環境要因なら走行ごとに揺れるはずである。
  **非帰属判定は署名の見た目一致でなく、赤の本文 (assertion message) まで読んで行う。**
- 今回それを捕まえられたのは、main 側が受理締切を 3 区間へ分ける改修で新設した
  `test_codex_worker_launch_budget.py` の 2 件が、同じバグ A を別の入口から踏んだためである。
  自 wave のテストだけでは 3 日間見つからなかった。
- 変異 matrix (fix 後、`mutation-spec-v1.json`): baseline PASSED (188 passed)、
  `MF-1` (F45 gate 除去) と `MF-2` (validate 側の file 不在扱い) がともに KILLED。
  2/2 KILLED・SURVIVED 0・MISMATCH 0。
- login node での焦点走は launcher の timing 系が 78 件赤くなった
  (hostname=pegasus02・PBS_JOBID 未設定・`codex_exit_code=-15`・wall 予算 3 秒)。
  計算ノードへ dispatch した焦点走では新設回帰テスト 6 件が緑。
  **launcher 系テストの緑判定を login node の走行で行ってはいけない。**

## 次の一手差分

### 完了

- [T-183] `tools/codex_worker_launch.py` / `tools/dev_wave_codex.py` へ `failure_class`
  (`f43_fragment`/`f45_missing_output`/`other`/None、seal 後に不変な観測値だけから導出する
  純粋関数) を追加し、F45 型は同一 job 内での追加試行を fail-closed し、F43 型は既存 retry を
  妨げない設計を実装した。workspace-write の `--max-attempts>1` 拒否と `_seal_attempt` の
  accepted 7 条件 AND は無改修。テスト新設 10 関数 (15 ケース)、変異 matrix =
  baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0。main 取り込みの合成監査で見つかった
  旧 schema V1〜V3 receipt の受理集合退行、および受入 1 回目が暴いた F45 fail-closed の
  発火範囲の誤り (バグ A) と `failure_class` 再計算の seal/検査 非対称 (バグ B) も
  同じ branch 内で修正し、回帰テストを足した。fix 後の変異 matrix は
  baseline PASSED・2/2 KILLED・SURVIVED 0・MISMATCH 0。
  remaining: none
  base: 72a3732e19231ef094307a36dd084b089be4041072faa9143cfe145ba5513765
