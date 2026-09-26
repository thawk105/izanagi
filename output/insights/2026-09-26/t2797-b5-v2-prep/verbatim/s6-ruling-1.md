# 段 6 裁定 1 — 敵対レビュー 2 本の所見 (2026-09-26 23:40 JST、親)

入力: `codex/review-1.md` (正しさ境界)、`codex/review-2.md` (過剰・削除)、統合差分 `patches/integrated.patch`。

| 所見 | 判定 | 処置 |
|---|---|---|
| R1-1・R2-1 v2 header の `purpose="registered-v2"` を report が拒否 | real must-fix | **fix-B:** v2 の header の `purpose` は `"registered"` のままにし、v2 は `cohort` (と `prereg_version`) で区別する。producer の関数引数・CLI の purpose 値は内部で使ってよいが header の field は `registered`。 |
| R2-3 `RoundTool` が `registered-v2` で KeyError | real must-fix | fix-B の header 変更で解消。fix-AD は v2 fixture が producer の実 header (purpose `registered`、cohort v2、`prereg_version`) と同じ形であることを確かめる |
| R1-2・R1-3・R2-2 429 後の stock 測り直しを report が `attempt-unowned`・`stock-unestablished` にする | real must-fix | **fix-AD:** report の v2 分岐で、測り直しの logical slot (`stock-start-1-restart-N`) と `stock_restart` を解釈して `core.slot_key(..., stock_restart=N)` で照合し、v2 では「最後の stock-start が確立していること」を系列開始 stock の成立とする (先行の stock は outage で置き換えられた記録として数え、記述に出す)。v1 は不変 |
| R1-4 report が v2 の `prereg_version` を照合しない | real should | **fix-AD:** v2 cohort の header は `prereg_version == core.PREREG_VERSION_V2` を必須にする |
| R1-5・R2-4 429 → 測り直し → 同じ a の採用・評価を一続きに見る test が無い (M-B1 の単一理由の kill が弱い) | real must-fix (test) | **fix-B:** 起動器・producer・親 module を実体でつなぎ (qsub・claude の起動だけを seam で差し替え)、job 1 の待ち中の 429 を 3 回挟んで、stock の測り直し、同じ a の採用、評価 1 までを通し、A・B・欠測・retry 回数が不変であることを 1 本の test で確かめる |
| R2-5 v2 定数の重複 | real should | **fix-AD:** `tools/b5_llm_round.py` と report は v2 cohort 名・版・workload を `b5_generator_contrast` の定数から参照し、report の slot key の文字列置換をやめる |
| R2-6 job 1 の標識 (`restarting-`・`failure-`・`inheritance-`) の重複 | real should (縮小) | **fix-B:** `outage-<a>.json` は維持。他の標識は、job 1 が待ちを終える理由の通知として必要な最小数に寄せる (台帳や親 state と同じ事実を二重に持たない)。test が緑のまま縮められない部分は理由を報告して残す |
| R1-6・R1-7・R2-7 | refuted | 処置なし |
| 親 P1 balanced の同時検査 flag | real (裁定 J6 の確定) | **fix-B:** v2 の slot argv は write-heavy と balanced に `--verify-performance-concurrent` を付ける (read-heavy は v2 に無い)。v1 には付けない |
| 親 P2 report の v2 の注記文が block の再現に触れる | real nit | **fix-AD:** v2 の `assumption` 文を「時間分離を支えに数えない」趣旨に合わせる (v1 の文は不変) |

fix の単位 (所有は素集合): **fix-B** = 単位 B の所有 path。規模上限 400 行。**fix-AD** = 単位 A と D の所有 path。規模上限 250 行。
既存 test の期待値は変えない (段 5 で入った v2 の新 test は、裁定に合わせた修正を可とする)。
変異の登録の追加: **M-B8** (fix-B) v2 の slot argv で balanced に同時検査 flag を付けない → balanced の argv test。**M-D5** (fix-AD) v2 の測り直し stock を report が拒否する → 測り直し系列の report test。

## 追補 (親、2026-09-26 23:55 JST)

- **P3 (real must-fix、親の読み):** v1 の親指示文は model 不一致のとき proposal も reject も公開せず session を閉じ、系列は待ちの期限切れで欠測になる。v2 の起動器は
  「正常終了で提案も却下も無い」を空出力 (A を消費して続行) と扱うので、model 不一致が A の消費に化け、同じ不一致が続けば系列が a-exhausted の生成器の結果として数えられる
  (成果物影響: model の違う role の系列が主標本に入る)。**fix-B2:** 起動器は空出力と判定する前に `<materials root>/round-<a>/model-mismatch.md` と
  `<materials root>/critic-<k>/model-mismatch.md` (k は request の next_evaluation − 1) の有無を見て、あれば系列を `unclassified-missing` で終える (A を消費しない)。
  所有 = `tools/pegasus/b5_contrast_launch.py`・`orchestrator/tests/test_b5_contrast_launch.py`。規模上限 120 行。変異 **M-B9**: この検査を外す → 不一致 file がある終了で系列が欠測になる test。
- 焦点走 f1 の赤 189 件の大半は contract-loader-drift (未 commit の p3_s4_loop.py が HEAD blob と不一致) で非帰属。統合を commit (cd059a477) して f2 で再走する。
