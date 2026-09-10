# 段 6 裁定 — レビュー C / D の所見

親裁定。2026-08-17 10:31 JST。

## 所見の裁定

| # | 判定 | 採否 | 担当 |
|---|---|---|---|
| C-1 RUN 未観測 + log 切り詰めで実走赤を再試行できる | real | 採用 (must-fix) | fix 子 (両層) |
| C-2 attestation が受入 command と同じ偽造可能 channel にある | real | **一部採用** (下記) | fix 子 + 記録 |
| C-3 main 前進テストが production 到達不能 | real | 採用 (must-fix) | fix 子 |
| C-4 共有 deadline が attempt 2 の command 起動を境界づけない | real | 採用 | fix 子 |
| C-5 M3/M4/M5/M9/M10/M12 の kill 帰属が名目 | real | 採用 (M12 は再分類) | fix 子 |
| D-1 runbook §7.3 が内部 attempt を記述していない | real | 採用 (must-fix) | **親 (docs)** |
| D-2 producer/consumer の closed vocabulary に横断 pin がない | real | 採用 | fix 子 |
| 焦点走の赤 (`claims == 2`) | real | 採用 | fix 子 |

refuted はゼロ。C-1 と C-3 は独立に「新テストが production を検査していない」型を突いており、
段 3 の A-5 と同族である。

## 裁定 9 — C-1 を採用。`child_started=false` に肯定的証拠を要求する

現行は `run_seen` (qstat が RUN を観測したか) に依存する。短い job が `QUE -> END` と遷移すると
RUN を取り逃がし、pytest が実走して赤を出していても `child_started=false` になる。
log が切り詰められて赤痕跡が落ちれば、waiter の裏取りも素通りする。**規律 2 の穴であり must-fix。**

両層で閉じる。

- **producer 側**: `child_started=false` は「job が実行を開始していないことの**肯定的な
  scheduler 証拠**を、判定時点で取得できた」場合に限る。取得できない・曖昧・状態不明は
  すべて `true` へ倒す (fail-closed)。「RUN を観測しなかった」だけでは false にしない。
- **consumer 側**: 捕獲 log に切り詰め・省略の framing があれば、pytest 痕跡の不在を
  **確定不能**として terminal に倒す。

## 裁定 10 — C-2 は一部採用。偽造耐性の新 channel は作らない

採用する (fix 子):

- attestation payload の **duplicate key を拒否**する。
- **改行で終わっていない EOF fragment を完成行として扱わない**。
- **内部矛盾を拒否**する (`child_started=false` かつ `child_rc` が非 null など)。

採用しない (本 wave の scope 外):

- dispatcher が受入 command から書けない場所へ nonce 付き sidecar を作る設計。
  理由 = (i) [T-1299] で source root repository は信頼済み中核と裁定済みであり、
  repo 内 runner の改変はこの信頼境界の内側である。(ii) 偽造で得られるのは
  **再試行 1 回**だけで、赤を緑に変えることはできない (attempt 上限 2、受理集合は不変)。
  (iii) 新 channel は D239/D253 と同格の設計判断であり、独立の敵対検証を要する。
- **残余は機械可読な限界として worklog に明記し、新規タスクとして起票する。**

## 裁定 11 — C-3 を採用。fake を production へ揃える

`wave_land_window.claim` は既存 self lease の payload `main_sha` を更新しない。したがって
attempt 間で main が進むと、waiter の exact main 検査で **terminal になるのが実挙動**である。
現行 fake はこれを模擬しておらず、`test_retry_success_uses_only_success_attempt_values_and_v3_schema` と
`test_retry_red_check_binds_second_attempt_main_and_tip` は production に無い経路を検査している。

- fake を production 挙動へ揃える。
- 「retry 中に main が進んだら terminal」を主張するテストを置く。
- M9 / M10 を**到達可能な stale 値変異**へ再登録する (attempt 1 の値を attempt 2 の受領証・
  red-check へ渡す変異は、main 不変のまま tip / log hash / environment / scheduler で作れる)。

## 裁定 12 — C-4 / C-5 / D-2 / 焦点走の赤を採用

- **C-4**: deadline を `run_acceptance` 入口で確定し、attempt 2 の claim 前と
  **command 起動直前**に再確認する。走行中 command の kill は入れない (裁定 7 のまま)。
- **C-5**: M3 は競合札のある実 lease directory、M4 は renew 後の inode/mtime、
  M5 は attempt 2 terminal 後の実 release を検査する形へ強化する。
  **M12 は `DW-M08` に従い kill でなく diagnostic sensitivity pin へ別枠記録する**
  (受理集合を変えず構造化シグナルだけを pin する変異のため)。
- **D-2**: 両 module を import して prefix と reason 集合の完全一致を検査する横断 meta-test を足す。
- **焦点走の赤**: `test_verdict_attempt_is_never_retried[red-check-failure]` の
  `assert fake.claims == 2` は誤り。red-check 失敗経路は受領証発行前に止まるので
  receipt-reclaim の 2 回目 claim へ到達しない。**実挙動に合わせて期待値を正す**
  (本質の主張 `submissions == 1` は残す)。

## 裁定 13 — D-1 を採用。runbook §7.3 は親が改訂する

内部 attempt により、caller が指定した log は「1 回の受入 command 全体」ではなく
「最後の内部 attempt」になる。初回の一次資料は archive path にある。runbook §7.3 は
attempt ごとに別 path を要求しており、この差を記述していない。

**親が `docs/pegasus-runbook.md` §7.3 を改訂する** (docs-only は親の担当)。書く内容:

- 外部 invocation と内部 attempt の区別、内部 attempt は最大 2 回であること
- 失敗 attempt の log の archive 命名規則
- terminal 時に caller path にあるのは最後の attempt の log であること
- retry journal の所在と読み方

§7.0 の exact pin (dispatch inventory) には触れない。`check_docs.py` を緑に保つ。

## 変異事前登録の更新

- **M12 を kill 期待から外し、diagnostic sensitivity pin へ移す** (`DW-M08`)。
- **M9 / M10 を到達可能な stale 値変異へ再定義**する (main 不変のまま tip / log hash /
  environment / scheduler の前 attempt 値を渡す変異)。
- **M16 (新規)**: producer の `child_started=false` から肯定的 scheduler 証拠の要求を外し、
  「RUN 未観測」だけで false にする → KILLED 期待。
- **M17 (新規)**: consumer の「切り詰め framing があれば不在を確定不能とする」を外す
  → KILLED 期待。
- **M18 (新規)**: attestation の duplicate key 拒否を外す → KILLED 期待。
- **M19 (新規)**: attempt 2 の command 起動直前の deadline 再確認を外す → KILLED 期待。
- M1 と M14、M16 と M17 はそれぞれ両層対であり、同時変異の kill 期待も登録する。

## fix の投入方針 (DW-S06-B)

C-1 が producer / consumer の**両層に跨る横断所見**であるため、
`DW-S06-B` に従い **1 つの Codex 単位へ寄せる**。編集面は 4 file。
統合 snapshot は `s5-diff.txt` に退避済み。
