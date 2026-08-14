---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t1092-receipt-diagnostics
seq: 1
title: acceptance-receipt 段の失敗理由を stdout と stderr へ出す (コード + テスト、branch worktree-dev-wave-t1092-receipt-diagnostics)
---

## 本文

- 裁定 = 2026-08-13 第 12 回 /rulings 確定内容 #1 (authority: user、23:44 JST、(a) 診断先行)。
  fixflakes の成否と独立の後続として残す指示に従い、単独 wave で実施した。
  材料の正本は `output/insights/2026-08-15_t1092-receipt-diagnostics/`。
- **親の段 1 実測が 2 つの最有力仮説を反証した。** 受入 lease の TTL 切れ (許容 age 2100 秒に対し
  実 226 秒) と、走行中の main 追い越し (reflog で 08-13 の 15:00〜20:00 に main ref の更新ゼロ) の
  いずれも成立しない。git 履歴・全 log・source を持つ親が約 14 の失敗地点を特定できなかったこと
  自体が、この wave の純増検出力の実証になった。
- **親 brief の誤りを敵対レビューが 3 件突き、親が裏取りして訂正した。** (1) 事故走行の実装は
  `59b8beb6` で `detail` の出現が 0 件 = 診断機構を持たない世代であり、「現行 14 site のどれか」は
  成立しない。(2) lease age の 151 秒は lease mtime 起点でないため成立しない。(3) main 不動の根拠は
  commit の author 日時では証明にならず、reflog へ差し替えた。いずれも結論は維持。
- **親の provisional 裁定 (P1) を段 4 で破棄した。** 親は「stdout へ出す」という確定裁定を
  「`2>&1` で同じ log に落ちるから stderr で同等」と読み替えていた。敵対レビューが
  「確定裁定の読み替えである」と指摘し、親がこれを受け入れた。既存 stderr 行を残したまま
  stdout へも 1 行出す形にした。安全性は実測で確認 (waiter stdout を解析する機械 consumer は
  無く、`tools/dev_wave_land.py` は blob path としてしか参照しない)。
- **親の fix 指示が既存テストを 1 件壊した ({{F:fail-closed-instruction-reversed-published-success}})。**
  受入証を書き終えた後の signal を失敗へ倒しており、緑の走行を理由なく捨てる = この wave が
  無くそうとしていた harm そのものだった。fix 第 3 巡で訂正し、fix prompt の制約に
  「過剰に拒否する方向の変更も禁止」を明記した。
- **変異 probe で 1 件が生存し、base からの穴を露出させた。** 受入 lease の TTL 判定 `>=`→`>` を
  誰も検出しなかった。等価変異ではなく残 300 秒ちょうどで受理→拒否に変わる境界変化で、
  既存テストは 299 秒しか試していなかった。DW-M02 の再照準として境界を固定した
  (production は 1 行も変えない)。同型の未固定境界 2 件 (detail の 256 / 2048 bytes 上限) も固定した。
- **並行 wave との合流で漏洩を 1 件検出した ({{F:merged-new-failure-path-outside-redaction-discipline}})。**
  main 側 [T-1076] が同じ 2 ファイルを変更していたが自動マージは競合なしで通り、焦点走も緑だった。
  Codex `role=author` の合成監査で、T-1076 が新設した失敗経路が共通の attestation 形式を使わず
  例外メッセージを運用 log へ出しうる状態と判明し、同じ merge commit の中で閉じた。
- 段 6 の fix は 3 巡 (DW-O16 の上限)。敵対レビュー 2 本の blocker 2 件は親が降格した。
  fingerprint 例外が `unexpected-error` へ落ちる件は base からの穴かつ「診断生成」ではなく
  receipt 本体生成であり段 4 不変条件の対象外。入れ子 detail の path 再掲載は、cleanup 成功時に
  同内容が同じ log に出るため新しい漏洩経路ではなく、`observed` を削ると残すべき原因値を失う。
- 段 8 自己改善の候補は 0 件。
- 工数 = codex 子 11 本 (plan 1 / consult 2 / author 1 / fix 4 / review 2 / merge 監査 1)、
  すべて `outcome=accepted`。model は段 3 luna 側のみ `gpt-5.6-luna`、他は `gpt-5.6-sol`。
  受入 lease の待ちは発生せず (投入時に保持者なし)。
- **受入全走 1 回目が帰属赤 1 件で止まった。実測でフレークと判定し、帰属しなかった
  ({{T:signal-lease-test-attestation-race}})。** `1 failed, 11033 passed, 65 skipped`。
  赤は `test_public_main_real_signal_releases_lease` で、子へ SIGTERM を送り rc=143 を期待するが、
  実際は `stage=acceptance-scheduler-attestation rc=70 detail={"observed":[],"reason":"marker-count"}`
  が先に出た。判定根拠は 4 点 — (1) 当該テスト本体は main と HEAD で byte 同一 (sha 一致、1837 bytes)、
  (2) `_scheduler_from_marker_payloads` / `_default_inspect_acceptance_log` / `_inspect_acceptance_log`
  の 3 関数も main と byte 同一で本 wave の差分が到達しない、(3) 焦点走 277 件では緑、
  (4) 単独再走で `1 passed` rc=0。48 worker の全走でだけ signal 到達が attestation より遅れる競走である。
- セッション異常 = 待ち手が 1 度**偽の完了**を返した (成果物も `.done` も無く生産者は稼働中)。
  成果物実在・`.done` 実在・生産者の生死の 3 点照合で偽と判定し、PID 直指定で張り直した。
  また親の進捗報告が数回、実測でない推定時刻を書いていた (実測より進んでいた)。以後は実測のみ。

## 次の一手差分

### 完了

- [T-1092] `acceptance-receipt` 段の 14 失敗地点に一意な reason と判定観測値を付け、
  stderr の既存行に `detail=` を足し stdout へ診断 1 行を出した。判定条件・rc・stage 名・
  受理集合は不変。焦点走 199 passed → 277 passed (赤ゼロ)、変異 9/9 KILLED (SURVIVED 0)。
  設計は {{D:acceptance-receipt-failure-diagnostics}}。
  remaining: none
  base: fce9c6a523e5887fca556cc7212fc7f92a302ed9465e6582a9f5aff4cb1f991d

### 新規

- {{T:receipt-content-generation-diagnostics}} **P3・新規**: `_acceptance_receipt_bytes` の
  receipt 本体生成 (`_fingerprint_json` 等) で例外が出ると `unexpected-error` へ落ち、
  どの段で落ちたか分からない。base からの穴で rc は同じ 70。診断段の対象外として降格した分。
- {{T:signal-lease-test-attestation-race}} **P2・新規・フレーク**:
  `test_public_main_real_signal_releases_lease` は 48 worker の受入全走でだけ赤になる。
  子へ SIGTERM を送り rc=143 を期待するが、負荷下では signal 到達より先に
  `acceptance-scheduler-attestation` の `marker-count` が発火して rc=70 になる
  (テスト用 tmp repo の child argv は scheduler marker を出さない)。単独走・焦点走では緑。
  受入を止める帰属赤として観測されるため、期待を「143 または attestation 失敗」に広げるのでなく、
  marker を出す child か attestation を待たせる seam を設ける方向で直す。
- {{T:scheduler-attestation-detail-redaction}} **P3・新規**: `acceptance-scheduler-attestation` 段の
  既存 detail は絶対 path (`log-open` / `log-read`) と `repr(value)` (`inspection-result`) を
  載せている。本 wave の非漏洩規律を既存段へも広げるか諮る。
