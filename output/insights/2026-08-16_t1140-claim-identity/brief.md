# 段 1 brief — [T-1140] 床値 claim identity を protocol 単位の排他にする

wave: dev-wave-t1140-claim-identity / base main tip: 10813338 / 2026-08-16 JST

## 確定済みユーザー裁定 (2026-08-16 一括裁定 #12・#14)

- #14 [T-1140]: 「同層で扱う。T-330 (c) と予約照合の 3 つを 1 wave へ」
- #12 [T-330]: 「(c) を先に (F321)。(a) は F321 修正後に再提示」

裁定 (c) の本文 = 「強制の対象を先に直す」= F321 決定 3-2 (claim identity が protocol 単位でない)
と 3-3 (reservation が自己申告) を、既に発火している床値経路に対して先に直す。
**択 (a) (loop.py の sink-local 強制) は本 wave の scope 外。** F321 修正後に再提示する。

## scope

- **S1 — claim identity を protocol 単位へ。** 床値 campaign の claim 排他の単位を
  「この run」から「この campaign の同一性」へ変える。実装本体は
  `orchestrator/campaign/campaign_claim.py`、call site は
  `orchestrator/campaign/s8b_floor_campaign.py:4716-4742` に限定する。
- **S2 — reservation 照合を強める。** `check_reservation` が現実と突き合わせていない
  `binding.host` / `binding.script_sha256` / `binding.nonce` を照合対象へ入れる。
  実装は `orchestrator/campaign/reservation.py`。
- scope 外: `loop.py` の強制 (T-330 択 a)、`s8b_oracle_driver.py` の G12 claim (既に protocol 単位)、
  run_dir 命名、OTHER (linux-baremetal, `single_process=False`) 経路。

## 不変条件

1. **規律 2 — 排他を強める方向のみ。** 今日拒否される入力を受理へ変える変更を一切入れない。
   辻褄合わせのための fail-open・例外・環境変数の逃がし道を作らない。
2. `single_process=False` の contract の挙動を 1 bit も変えない。claim 取得は
   `is_reservation_required` が真のときだけ発火する現行条件を保つ。
3. `_fresh_run_id` の他 2 consumer (`campaign_run_id`=4759、run_dir 名=5113) は run 単位のまま。
   識別子の意味を二義化しない (DW-O13/D75) — 「run の識別子」と「campaign の同一性」を
   別名で分ける。
4. 凍結 bytes を変えない。claims は `test_frozen_artifacts.py` の FROZEN_MANIFEST に不在 (実測)。
5. `s8b_floor_campaign.py` の編集面を 4716-4742 に限定する。稼働中の t523 wave が
   4716-4719 を書き換えており、衝突面を最小に保つ。

## 実測済みの前提 (brief 前に測った)

- **F321 は実行で再現する。** 同一 protocol を 1 秒ずらすと claim が 2 本とも取れる
  (`20260816T030000Z-aaaaaaaa.claim` / `...030001Z-aaaaaaaa.claim`)。
  probe = `/work/1/SFC/tanab/dev-wave-jobs/t1140-claim-identity/premise_probe.py`
- **正しい先例が同 repo にある。** `s8b_oracle_driver.py:1005 _claim_identity` は
  {manifest_sha256, freeze_sha256, schedule_sha256, campaign_id} の canonical sha256 で時刻を含まない。
- **`ReservationBinding` は host/script_sha256/nonce を既に保持し、形状だけ検査する。**
  `check_reservation` (reservation.py:216-267) が照合するのは PBS_JOBID・boot_id・時刻・残容量のみ。
  → S2 の入力は実成果物の field に実在する (DW-O13 充足)。
- **`acquire_claim` は one-shot・再入不可** (campaign_claim.py:167-227)。
- **発火 caller は実在する** — 床値 campaign 本体 (DW-G04 充足)。

## pin 閉包 (DW-O09、実測)

| pin | 位置 | 影響 |
|---|---|---|
| ClaimRecord のフィールド集合を exact set で固定 | `test_s8b_floor_campaign.py:3949` | field を増やすなら更新が要る |
| claim の job_id/host/boot_id を固定 | `test_s8b_floor_campaign.py:6408-6412` | 値の意味は不変の想定 |
| **identity 導出そのものを `_fresh_run_id` で再現** | `test_s8b_floor_campaign.py:3791` | S1 で必ず更新が要る |
| FROZEN_MANIFEST | `test_frozen_artifacts.py:41` | claims は不在 = 影響なし |

## 親の provisional 裁定 (攻撃対象)

- **(P1)** claim identity は oracle driver 同型の canonical sha256 とし、run 由来の情報
  (時刻・PID・UUID) を一切含めない。入力は少なくとも protocol_sha256 と freeze_sha256。
  両者は call site の 4665/4679 で既に手元にある。
- **(P2)** resume 経路も同じ protocol 単位 identity にする。現行 resume は
  `Path(resume_dir).name` を identity にするため、元 run の claim が残っている以上すでに
  refused になる。よって受理集合は狭まらない。**要検証** — `single_process=True` かつ
  `allow_resume=True` の contract が実在するなら、そこで受理集合が狭まる。
- **(P3)** nonce の照合には scheduler 所有の create-only receipt が要る。本 wave の期限内に
  受理可能な source が実在しなければ、nonce は設計メモに留め host / script_sha256 の 2 件を
  実装する (DW-G04: 発火条件を満たす artifact path を書けないものは実装しない)。
- **(P4)** ClaimRecord に field を足さず、`campaign_identity` の導出だけを変える案を既定とする。
  足す案を採るなら `test_s8b_floor_campaign.py:3949` の exact set pin を同時に更新する。
- **(P5)** t523 との 4 行の衝突は land 順で解決する。本 wave が先に land すれば t523 が
  main 取り込み時に解決する。**意味的な取り消しを防ぐため、排他の単位は leaf
  (`campaign_claim.py`) 側で強制する** — call site の identity 文字列が merge で run 単位へ
  戻っても、leaf が protocol 単位でない claim を拒否できる形にする。

## 成果物影響 (DW-G05)

- **S1 を実装しない場合**: 床値 campaign が proof chain に載せる「single_process = 単独実行」の
  主張が恒真のまま残り、certified 選択の下限根拠である床値 throughput が二重投入下で
  得られていないことを保証できない。既存の床値**値**は疑わない (二重投入の記録は無い、F321)。
- **S2 を実装しない場合**: 未検証の `binding.host` が claim へ転記され、材料レポートの
  provenance に「どのホストで測ったか」として載り続ける。script SHA 不一致も検出されない。

## 純増検出力 (性質で検索した既存被覆との差分)

既存: 同一 identity の claim 衝突の拒否 (`test_s8b_floor_campaign.py:3785`、ただし `_FIXED_NOW` を
両側に使うため**同一秒のみ**)。`test_campaign_claim.py` は O_EXCL・fsync・release 不在のみ。
`test_reservation.py` は job_id・boot_id・時刻・残容量のみ。

純増:
1. 同一 protocol を**異なる時刻・異なる run** で二重取得しようとしたときの拒否
2. 現在 hostname が `binding.host` と不一致のときの拒否
3. 実行中 script の SHA256 が `binding.script_sha256` と不一致のときの拒否
4. (P3 が通れば) nonce が scheduler 所有 receipt と不一致のときの拒否

## 並列分割

- **Unit A**: `campaign_claim.py` (protocol 単位排他の leaf) + `s8b_floor_campaign.py:4716-4742`
  の最小 call site 差分 + `test_campaign_claim.py` / `test_s8b_floor_campaign.py` の該当テスト
- **Unit B**: `reservation.py` (host / script_sha256 / nonce 照合) + `test_reservation.py`

ファイル面は交わらない。Unit B は `s8b_floor_campaign.py` を触らない。

## 受入・実測環境

Pegasus。テストは `python3 tools/run_tests.py` (受入全走は `--force-dispatch` なし、
余計な flag を足さない)。変異本走は `tools/mutation_harness.py --runner-mode dispatch`
+ `--force-dispatch`。

## 重さの判定

軽量版にしない。正しさ防壁 (単独性の proof chain) に触り受理集合を変えるため、
段 2・3 と段 6 の敵対レビュー子を省かない (DW-C00)。
