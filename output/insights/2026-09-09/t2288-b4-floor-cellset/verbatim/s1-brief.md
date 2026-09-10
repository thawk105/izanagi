# 段 1 brief (v2) — [T-2288] B-4 権威 floor の発行に向けた凍結 spec のセル集合表現

v1 は段 2 投入後に親が b10 の反例を実測したため破棄した (段 2 の子は SIGTERM で中断、成果物なし)。

## 研究前進

B-4 材料レポートが到達できる分析 verdict は現在 `protocol_violation` 1 種だけで、Phase 3 主経路の
片翼が止まっている。完了判定は「事前登録 §5 の floor 欄に検証を通る権威 floor 成果物の pin が入り、
材料レポートが floor present で分析を評価する」こと。本 wave はその土台で、**D1641 が凍結した
セル集合「3 workload × contention セル」を凍結 spec で表現できるようにする最小差分**だけを担う。
止めている実測: `floor_pair_driver._bind_checkout_inputs` (1122-1196) は `provenance.calibration` の
1 件を全 cell へ照合し、`calibration.workload != dict(perf.workload)` で拒否する。よって 1 spec の
cells は同一 workload しか持てない。issuer 側は複数 workload 前提で組まれている
(`_derive_identity` の `workload_identifier` は `_aggregate_identifier("set", ...)`)。

## 依頼前提の訂正 (実測)

依頼文の「現在は floor=None が渡る」は **陳腐化**。`p3_b4_material_report.py:215` は §5 を読んで
`resolve_preregistered_authoritative_floor` を呼ぶ。同 resolver (issuer 1216-1250) は §5 の floor 欄が
逐語 sentinel `未記入` のときだけ `None` を返し、それ以外は pin 文法・path・sha256 を検査して
fail-closed する。**配線は済んでおり、残るのは発行である。** 発行の前提は本 wave の外に 3 件欠けている
(いずれも実測) — accepted calibration は rr50 / t48 の 2 件だけ (tracked な `calibration/v2` 全 27 file を
列挙して確認)、tracked build receipt は 0 件 (`git grep -l "s8b-binary-admission" -- output` が docs の
言及のみ)、D1641 の 2 campaign 実測は未実施。**よって本 wave で発行そのものは行えない。**

## 親が実測した反例 (v1 を破棄した理由)

b10 の formal run は read-heavy / balanced / write-heavy の 3 workload を測ったが、
`output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json`
の `calibration` は 3 workload すべてに**同一の** `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`
(balanced / rr50 / t48) を束縛し、束縛 field は `env_tag` / `threads` / `clocks_per_us` / `records` /
`saturated` / `path` / `sha256` などで **`workload` を含まない**。
また事前登録 §5 の「校正済み `PerfConfig` (records / threads / reps / extime) の artifact パスと hash」欄は
**単数**であり、同じ §5 のセル集合が 3 workload であることと合わせると、1 calibration が 3 workload を
覆う読みを支持する。つまり `floor_pair_driver` の workload 一致要求は、同じ repo の先例と整合しない。

## 確定済みユーザー裁定 (緩めない)

D1641: 担当 3 者は thawk105 名義で AI 委任、測定を認可、凍結項目 12 行の値を確定
(セル集合 = 3 workload × contention セル / 保守側最大の対象 = 凍結セル集合 × 2 時間窓の全部 /
成果物名に env_tag・protocol・threads・workload・campaign 識別子 / 校正済み `PerfConfig` は
calibrator の出力を採る)。D1377 (caller の自己申告を凍結値の位置へ入れない)。
D1759 (受理 producer 版は単一定数 1 値)。D1696 (spec 側 validator を一般拡張しない)。
D1530 (未接続 interface を単独で建てない)。事前登録 §5.1 の解除条件は 1 つも緩めない。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- (P1-a) **択一は 3 案ある。親は (γ) を有力と見るが確定していない。**
  - (α) workload ごとに 3 spec → 3 成果物 + §5 側の集約規則。コード変更なしだが §5 の pin が
    1 件であることと衝突し、集約規則という新機構が要る。
  - (β) cell ごとに calibration を束縛する。最も厳しいが、rr5 / rr95 の calibrator 走行が別途必要で、
    §5 の単数欄と衝突する。
  - (γ) calibration の束縛から **workload 一致要求だけを外す** (`env_tag` / `clocks_per_us` /
    `threads` / `records` / `quality.status == "accepted"` は維持)。既存 accepted calibration 1 件で
    3 workload の cell を持つ spec が作れる唯一の案。b10 の先例と §5 の単数欄に整合する。
    **ただし受理集合を広げる。** 正当化できるのは「calibration が保証するのは records 飽和と
    環境であって workload 混合ではない」を一次資料で示せた場合に限る。
- (P1-b) issuer は無変更で足りる (`workload_identifier` は集合集約、`threads` は
  `next(iter(threads_values))` なので cell 間の threads 単一性は維持が必要)。
- (P1-c) 変更は `SPEC_SCHEMA` の bump だけで足り、`PLAN_SCHEMA` / `WINDOW_SCHEMA` /
  `SUMMARY_SCHEMA` は据え置ける ((γ) なら wire 形が変わらないので bump 自体が不要かもしれない)。
- (P1-d) DW-G04 の発火 artifact は「既存 accepted calibration 1 件を共有する 2 workload の cell を持つ spec」
  で足りる ((γ) のときだけ既存 artifact で成立する)。
- (P1-e) 権威 floor の発行そのもの、§5 記入、事前登録本文の改訂は本 wave の scope 外。

## 不変条件

規律 2 を緩めない。`quality.status == "accepted"` 要求、`saturation.records` と cell の
`perf_config.records` の一致、`env_tag` / `clocks_per_us` の一致、`calibration=None` を返す
attestation mode の意図的拒否 (1170-1176)、cell 間の threads 単一性は**いずれも維持**する。
受理集合を広げる差分は 1 点 (workload 一致要求) に限り、広げた範囲を裁定文へ明記する。
fail-closed を fail-open にしない。既存テストの期待値を変えない。§5 を埋めない。
事前登録本文を書き換えない。仮想リスク向けの gate・検査・台帳・一般化を足さない。

## 成果物の形

`orchestrator/campaign/floor_pair_driver.py` と `orchestrator/tests/test_floor_pair_driver.py` の 2 file。
insight (一次資料 + 変異台帳)、worklog / decisions fragment。
実測は焦点走 (driver / issuer / material_report) + 受入全走。

## 変更面の実アンカー (file:line、現 main cbcdb6c91)

| アンカー | 現状 |
|---|---|
| `floor_pair_driver.py:56` | `SPEC_SCHEMA = "floor-pair-spec/v3"` |
| `floor_pair_driver.py:647-657` | `_parse_calibration_reference` (path / sha256 / attestation_mode) |
| `floor_pair_driver.py:660-672` | `_parse_provenance` — `calibration` は単数 |
| `floor_pair_driver.py:798-816` | `_parse_cells` — cell は `cell_id` と `perf_config` だけ |
| `floor_pair_driver.py:1122-1196` | `_bind_checkout_inputs` — 単一 calibration を全 cell へ照合 |
| `floor_pair_driver.py:1184-1196` | cell ごとの照合ループ。`workload` 一致要求はここ |
| `p3_b4_floor_artifact_issuer.py:737-812` | `_derive_identity` — `workload_identifier` は集合集約 |
| `p3_b4_floor_artifact_issuer.py:748-750` | docstring が `floor_pair_driver.py:759-776, 1136-1147` を行番号 pin |
| `test_floor_pair_driver.py:628-634` | 4 semantic schema 定数の同時 pin |
| `test_floor_pair_driver.py:636-651` | v2 spec 拒否 test |

## 分割方針

実装面は 1 file + その test で一枚岩。段 5 は Codex `role=author` 1 単位。並列分割しない。

## 受入・実測環境

焦点走・受入全走はいずれも `run_tests.py` の dispatch 経路 (計算ノード)。所在の正本は worklog、
機体固有情報は `docs/pegasus-runbook.md`。本 wave は新規 Pegasus 実行体を要さない。

## 起動時の重複検査 (依頼の明示要求)

T-2316 は稼働中だが編集面は `p3_b4_launcher.py` と `test_p3_b4_launcher.py` に限定 (codex prompt の
逐語を `ps -eo args` で実測)。本 wave の編集面と素集合。他の `p3_b4_*` 稼働 wave は無し。
