# [T-1705] 段 4 裁定・プラン v2・変異事前登録

## 親が実コードで裏取りした事実

- `_bound_price_schedule` (`orchestrator/tests/test_codex_reasoning_ab.py:6519-6553`) の 2 slot は
  **どちらも `arm="max"`** である。既存 cost テストは arm 間比較を一度も覆っていない。
- attempt 行は `block_id` (str) と `attempt` (int) を持ち、`_apply_pair_invalidations`
  (`tools/codex_reasoning_ab.py:9730-9742`) が同じ組を pair unit の key として既に使っている。
- `material_manifest_sha256` は集約入口 (`tools/codex_reasoning_ab.py:10373-10376`) で利用可能。
- `_slot_dimensions` (`:9218-9307`) の戻りに `block_id` は**含まれない**。pair identity は
  attempt 行側から取る。

## real / refuted と採否

| # | 所見 | 裁定 | 採否 |
|---|---|---|---|
| A1 | 非 gate・受理集合不変の回帰検査が不足 | **real** | 採用 (must-fix) |
| A2 | axis の count 複製を複数試行 axis で検査していない | **real** | 採用 (must-fix) |
| A3 | no-float 検査と既存 `rounding` 不変検査が取付位置に届かない | **real** | 採用 (must-fix) |
| A4 | 比較範囲値を hard-code しても通る | **real** | 採用 (must-fix) |
| A5 | 親 brief の test anchor が不正確 | **real・nit** | 親が brief を訂正。実装影響なし |
| B1 | 二 key 一致は paired 比較に十分でない (identity 入れ替わり) | **real** | 採用 (must-fix) |
| B2 | `basis_key` が比較 universe を識別せず別成果物間で衝突 | **real** | 採用 (must-fix) |
| B3 | 予定テストが実際に異なる arm を覆わない | **real** | 採用 (must-fix) |
| B4 | cache write 未計上量の arm 間系統差 | **real** | **scope 外**。receipt schema の新登録世代が要る (§10 が未着手と明記)。worklog へ裁定候補として記録 |
| B5 | 平均と合計で必要条件が違う | **real** | 採用 (規則の限定として)。平均 field は追加しない |

**refuted はゼロ。** 両レンズの所見はすべてコードで確認できた。

## プラン v2 (段 2 プランからの差分だけ)

段 2 プランの二段構造、field の含める/除く判断、additive 方針、却下案はすべて維持する。次を追加する。

1. **`accounted_total_key` に pair unit identity を加える。** 四 count に加え、
   `observed` / `unavailable` / `not-incurred` の status ごとに、寄与した `(block_id, attempt)` の
   **ソート済み集合**を持たせる。axis 行は自分に集約された全 attempt 分、per-attempt 行は自分 1 件分。
   count だけの一致では、arm A と arm B が別々の pair unit を観測していても key が一致してしまう。
2. **`basis_key` に `comparison_universe` を加える。** `material_manifest_sha256` を入れる。
   取得できず `null` のときは、規則文字列で「同一 aggregate result 内でのみ比較可能」と明示する。
3. **`rule` 文字列を、保証する範囲だけに限定する。** 保証するのは
   「partial な accounted component total どうしの比較」までであり、試行あたり平均・完全費用・
   実請求額は保証しない。この限定を規則の文言に含める。
4. **テスト fixture を足す。** 既存 `_bound_price_schedule` の期待値は変えない。
   **異なる `arm` を持つ新しい fixture** と、**1 つの axis に 2 試行以上入る fixture** を追加する。
   `benchmark_task_id` / `stage` も 2 種以上にする。
5. **受理集合不変の回帰検査を明示的に置く。** `valid`、`failure_reasons`、`experiment_complete` を
   比較宣言の有無・一致不一致にかかわらず固定する。
6. **no-float 検査は最終成果物 dict 全体を walk する。** helper の直接返値だけでは届かない。
   既存 top-level `rounding` の値・型も別途固定する。

## 変異事前登録 (DW-M01)

実装前に登録する。各変異は新設 helper と配線点に位置し、同じ入力を拒否する層は前後に無い
(いずれも新規 additive field であり、既存 validator は参照しない)。無効化時の赤理由は一つに絞れる。

| ID | 変異 | 期待 | 束縛するもの |
|---|---|---|---|
| M1 | 比較不一致時に `reasons.append(...)` を足して gate 化する | KILLED | **受理集合** (`valid` が false へ動く) |
| M2 | `basis_key` から `comparison_universe` を落とす | KILLED | 成果物の値 (B2) |
| M3 | `accounted_total_key` から pair unit identity 集合を落とし count だけにする | KILLED | 成果物の値 (B1) |
| M4 | axis の `accounted_total_key` へ最終集約 count でなく最初の per-attempt vector を写す | KILLED | 成果物の値 (A2) |
| M5 | `basis_key.comparison_scope.benchmark_task_id` を literal へ hard-code する | KILLED | 成果物の値 (A4) |
| M6 | nested `rounding.decimal_places` を `8.0` (float) にする | KILLED | 成果物の型 (A3) |
| M7 | `basis_key` へ `requested_model` を含める | KILLED | 正規化の目的 (§10) |
| M8 | `unavailable` の per-attempt 行から `comparability` を落とす | KILLED | 成果物の値 (D932 の三分) |

M1 だけが受理集合を束縛する。M2〜M8 は成果物の値・型を束縛する。
anchor (old 逐語) と期待 node は fix 後の最終 commit で `DW-M07` に従い再検証してから本走する。

## 不変条件 (実装子へそのまま渡す)

- 新しい `ValidationError`・`raise`・拒否条件・gate・failure reason を追加しない。
- 既存テストの期待値を変更しない。反転・緩和・skip・削除を禁じる。
- 凍結 snapshot の bytes・固定 path・固定 SHA-256・固定 price version literal を変えない。
- `coverage_status` は `partial`、`certification_status` は `not-certified` のまま。
- `basis_key` に `requested_model`・`unit_prices`・`arm`・`accounted_amount` を含めない。
- verifier / correctness の経路に触れない。


## 段 6 追記 — レビュー結果と追加の変異事前登録 (fix 前に登録)

レンズ C (裁定充足・受理集合): **所見 0 件。** A1〜A4・B1〜B3・プラン v2 の 1〜6 をすべて closed と判定。
禁止事項違反・新しい境界例外・差分と報告の食い違いも検出せず。

レンズ D (検出力・意味論): **検出力の穴 3 件。すべて real、すべて must-fix。**

| # | 穴 | 放置時の成果物影響 |
|---|---|---|
| D1 | 非 null `material_manifest_sha256` が 1 種類しかなく、異なる manifest を同じ universe へ固定する変異が生存する | 別実験の行が同じ比較集合を参照し、実験間差を arm 間差として読む |
| D2 | pair unit identity の `attempt` 成分が全 fixture で `1` のため、`attempt` を literal 固定する変異が生存する | retry 世代間で観測 identity が入れ替わっても key が一致し、対応しない試行を比較可能として参照する |
| D3 | `rule` を単語の存在だけで検査しており、極性と null 条件分岐を固定していない | 保証していない平均・完全費用・実請求額まで保証すると読める文言へ反転しても通る |

いずれも受理集合は変えない。成果物の**参照範囲と保証文言**を変える。

### 追加変異 (M9〜M11)

| ID | 変異 | 期待 | 束縛するもの |
|---|---|---|---|
| M9 | pair unit identity の `attempt` 成分を literal `1` に固定する | KILLED | 成果物の参照範囲 (D2) |
| M10 | `comparison_universe.material_manifest_sha256` を literal へ固定する | KILLED | 成果物の参照範囲 (D1) |
| M11 | `rule` の null locality 条件を反転する (null で制限せず、非 null に制限をかける) | KILLED | 成果物の保証文言 (D3) |

M9〜M11 も受理集合を束縛しない。M1 だけが受理集合を束縛する変異である。
