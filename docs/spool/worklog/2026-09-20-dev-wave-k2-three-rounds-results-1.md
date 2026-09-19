---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-k2-three-rounds-results
seq: 1
title: K2 手動 loop 3 巡 (提案 → 評価 → critic × 3、実測の還流 2 回・診断の還流 1 回) の単独 results 稿を一次資料から書き、README の results 表へ 1 行を足した (docs のみ、台帳 ID 未起票、B-6 の材料、branch worktree-dev-wave-k2-three-rounds-results)
---

## 本文

- ユーザー依頼 (2026-09-20) に基づく 1 wave。着手時 local main `b7f970dfa` から fresh worktree、専用 handoff は repo 外 job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-three-rounds-results/HANDOFF.md`。実装差分ゼロ (Codex 実装子なし)、軽量版 (段 2・3 省略、
  `DW-C00` の「一次資料から事実を再抽出する docs-only」につき段 6 read-only レビュー 1 本 + 焦点再レビュー 2 本)。成果物は
  `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` (501 行、限定 21 件) と `docs/paper-story/README.md` の results 行 1 本。
- 素材: 稿は 3 巡 (2026-09-16 [T-2588] / 09-18 [T-2746] / 09-19 縮小走行) の proposal JSON・role 逐語・campaign WAL・受領証・lock・loop_state・digest・AO・
  材料レポート・NQSV 終了要約・裁定 (D2044 項 9 / D2120 項 1 / D2148 項 2・3 / D2155 / ユーザー決定 2026-09-19) から作り、repo 外の権威 bytes 17 file の
  sha256 を再計算して §5.1 に置いた。成立範囲は「提案・評価・critic を 3 回、実測の還流 2 回、critic 診断の型付き入力への還流 1 回」までで、
  巡 3 の実測を次生成へ戻す実走は含まない。同 job stock 対照はどの巡にも無く ([T-2795] 裁定待ち)、3 走の値は改善・退行の根拠にしない。
  知識・診断の因果効果は主張せず (planner 入力は診断 key 以外同一、coder 入力は診断 + `planner_direction` の差だけだが各条件 1 回の別起動)、
  legacy critic のため B-4 非適格。規律 6 は coder 4 出力が `instruction_like_content_detected=false`、planner / critic は散文の自己申告。
- 一次資料と記録 README の差 3 点を稿 §4.3 に置いた (記録側は直さない): 2 巡目 job `4954.nqsv` の Created は原本 06:36:06 (記録 06:35:44)、
  2 巡目の noise floor は「較正記録が無い」でなく較正 file 7 本走査・候補 3 file 条件不一致・within-run `self-inconsistent-calibration` 除外、
  critic-2 の「`campaign.lock` に `spec_content` 無し」は実物の `identity_preimage` 内に 1 件。`knowledge-input.json` は 1 巡目と 2・3 巡目で
  bytes が違う (key 順) が内容同一。知識源 `clocks_per_us` は 1800 で本走 2100 と異なる。
- 段 6 レビュー 1 本 (gpt-6-astra / medium、23 call、502 秒): NO-GO、所見 12 (must-fix 4 / should-fix 6 / nit 2)、real 11 / refuted 1。
  must-fix は (1) 「3 巡が閉じた」が §0.1 の定義 (実測が次生成へ戻る) と不一致 → 成立範囲を実施 3 / 実測還流 2 / 診断還流 1 に固定、(2) §2.3 の
  入力差の列挙が誤り (whiteboard / current_perf は同一)、(3) 知識源の `clocks_per_us` 1800 を「同じ配線」と書いた、(4) 実行者の手続き (射影事故・
  投入前検査・代替照合・未取込み理由) を一次資料の確認と区別せず書いた → 「記録による」を付け §4.3 に集約。焦点再レビュー 1 回目 (closed 9 /
  partial 2 / regressed 1、新規 nit 1) の残りは送付・認識・時系列の出所分離と親 brief の同期、限定 21 の `opus/high` 見落とし。
  焦点再レビュー 2 回目 (closed 3 / partial 1) の残り 1 点 (§2.7 巡 3 の生成行が job の実行 log から「投入前の生成」を言い過ぎ、critic-1 の入力 JSON
  未保存との不整合) は DW-O16 の 3 巡上限に達したため、レビューの対案を逐語で当てて親が real・採用で閉じた (critic-2 / 3 の保存入力の
  `digest_sha256` が各巡の digest と一致することは親が検算)。逐語は job dir `codex/` (review 1 + focus 2、いずれも gpt-6-astra / medium)。
- 受入結果と land は専用 handoff へ集約する。dev-wave 改善候補は段 8 で 0 件 (guard の拒否形は既知で新規の作法欠落ではない)。

## 次の一手差分
