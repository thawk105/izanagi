# [T-472] freeze 由来 gate_predicate consumer の正準述語 membership — 逐語と変異台帳

- wave: `dev-wave-t472-canonical-predicate-consumers` (背景 job f09b5df2、fresh context)
- branch: `worktree-dev-wave-t472-canonical-predicate-consumers`
- 基準 main: `6c50008` / 実装 anchor commit: `0840c8d`
- 統制する裁定: worklog (193) [T-409] 択一 A=(a) の残余 1 (2026-08-05 /rulings)
- 一次成果物 (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/t472-canonical-predicate-consumers/`
  (brief、段 2 プラン、段 3 敵対 2 本、段 4 裁定、実装子報告、段 6 レビュー 2 本、変異 spec / 台帳)

---

## 1. 起票の前提が誤っていた (段 1 前提実測)

worklog (193) の [T-472] 起票は次のように書いていた。

> `s1_direct_comparison.py:515-523` の `system_gate` / `ident_all`、同型の
> `s1_verify_extime_calibration.py` には**旧 blacklist しか掛かっていない**

親が段 1 で実測した結果、**これは誤りである**。

1. `p3_s4_loop.quarantine` は `marker_id == TRIGGER_MARKER_ID` のとき
   `trigger_gate_binding.is_canonical_predicate` で fail-closed する ([T-428] が入れた点)。
2. `TRIGGER_MARKER_ID` は `axis_trigger_gating.MARKER_ID` の別名で、実測値はどちらも
   `'silo-backoff-trigger-gating'`。
3. 2 consumer はどちらも `marker_id=axis_trigger_gating.MARKER_ID` で quarantine を呼ぶ。
   実測: 非正準 `izanagi_gate_pass = true;` → `passed=False`、理由「trigger predicate が正準集合外」。
4. `output/s1-freeze/known_axes_freeze.json` の 6 述語は**全て正準** (mask `8, 31, 4, 31, 8, 31`)。
   [T-428] の land は s1 driver を壊していない。

したがって **受理集合は着手前から閉じていた**。この wave が足したのは受理集合の縮小ではなく、
consumer-local な防御層と、それを固定するテストの検出力である。

### 保証の正しい名前 (段 6 レンズ A の指摘を採用)

追加した 2 gate は **現行凍結値では発火しない regression sentinel** である。
「初回閉包」でも「非正準を初めて塞いだ」でもない。発火するのは、
将来の refreeze drift、`prepare_cell` / `validated_target` の直接 caller、
共有 quarantine 側の退行と組み合わさった場合である。

### 未 pin だった面 (この wave の純増)

- consumer-local な防御層が無く、閉包が共有 helper の `marker_id` 分岐に依存していた。
- `is_canonical_predicate` を参照するテストは `test_trigger_gate_binding.py` だけだった。
- 凍結 6 セルは述語としては **3 種類**しかなく、32 正準述語のうち残り 29 種は
  consumer 境界で固定されていなかった (段 3 レンズ B の指摘)。
- ただし共有 quarantine 側の 32 受理と非正準拒否は
  `test_p3_s4_loop.py::test_trigger_quarantine_accepts_exact_32_canonical_predicates_with_outer_space`
  と `::test_trigger_quarantine_rejects_noncanonical_text_before_structure_inspection` が
  **既に pin していた**。親の段 1 brief が書いた「変えれば赤ゼロのまま開く」は
  direct/shared については誤りであり、段 4 で訂正した。

---

## 2. 実装 (anchor commit `0840c8d`)

| file | 位置 | 内容 |
|---|---|---|
| `orchestrator/campaign/s1_direct_comparison.py` | `prepare_cell`、型・空文字検査の直後 / `check_syntax_contract` の前 | `is_canonical_predicate` 不成立で `DriverError("freeze gate_predicate が正準集合外")` |
| `orchestrator/campaign/s1_verify_extime_calibration.py` | `validated_target`、freeze/構築対象の完全一致検査の直後 / `return target` の前 | 同上を `target["gate_predicate"]` に対して。`CalibrationError` |

校正側の位置は段 3 レンズ A/B の両方が指摘した 2 点で決めた。

- 完全一致検査**より前**に置くと、既存の
  `test_validated_target_rejects_freeze_and_constructed_gate_mismatch` が
  `match="known_axes_freeze"` でなく新文言で落ち、**既存テストの意味が変わる**。
- 検査対象は freeze 側ではなく `target["gate_predicate"]`。返って materialize されるのは
  target 側であり、`==` を偽装する非文字列は freeze 側検査を素通りする (レンズ A の F3)。

拒否文言はいずれも固定文言で、入力述語の本文を含めない (disclosure-free)。

---

## 3. テスト (7 本追加)

`orchestrator/tests/test_s1_direct_comparison.py`

- `test_prepare_accepts_all_32_canonical_predicates[mask-00..mask-31]` — 32 正準述語の受理。
- `test_prepare_accepts_six_frozen_gate_predicates` — 独立 golden
  (`EXPECTED_GATES` / `EXPECTED_IDENT_ALL_PREDICATE`) による凍結 6 occurrence の受理。
- `test_prepare_rejects_noncanonical_freeze_predicate` — 固定文言での拒否。
- `test_prepare_rejects_noncanonical_predicate_with_real_quarantine` — consumer/shared 両層の composition。

`orchestrator/tests/test_s1_verify_extime_calibration.py`

- `test_validated_target_accepts_all_32_canonical_predicates[mask-00..mask-31]`
- `test_validated_target_rejects_matching_noncanonical_predicate`
- `test_validated_target_rejects_noncanonical_target_side` — `__eq__` を偽装した非文字列 target の拒否。

### composition テストが測っているもの・いないもの (レンズ A の指摘)

`_fixture_gate_patch` が書く C++ 骨格は marker と既定 hole だけで、本物の
`patches/silo-backoff-trigger-gating-variant.patch` が持つ CMake flag 配線、abort reason enum、
sentinel reset、reason store、`izanagi_gate_pass` の宣言は**無い**。したがってこのテストが
証拠にできるのは **membership 層の composition** であって、実 patch 適用・C++ 意味・build・
source identity ではない。材料レポートでこのテストを引くときは、この限定を併記する。

### 自己オラクル性 (レンズ B の指摘)

all-32 テストの入力は `emit_predicate()` から作られ、production の `CANONICAL_PREDICATES` も
同じ `emit_predicate()` から構成される。この 2 テスト単独では emitter と正準集合の同時 drift を
検出できない。独立 golden との逐語比較は
`test_reflux_ir.py::test_all_32_predicates_match_independent_golden_byte_for_byte` が担う。
両者を一組の根拠として参照すること。凍結 6 occurrence のテストは独立 golden を使うので
この問題は無い。

---

## 4. 変異台帳

anchor = 実装 commit `0840c8d`。harness = `tools/mutation_harness.py`、runner-mode = `dispatch`。
spec / 台帳の実体は `/work/1/SFC/tanab/dev-wave-jobs/t472-canonical-predicate-consumers/`
(`mutation-spec.json` sha256 `6b88c02fe828669ce9a40551c825127f0ebe714fe65129aa46e15dcd60cc4745`、
`mutation-ledger.json`)。

runner command:

```
python3 tools/run_tests.py orchestrator/tests/test_s1_direct_comparison.py \
  orchestrator/tests/test_s1_verify_extime_calibration.py \
  orchestrator/tests/test_p3_s4_loop.py orchestrator/tests/test_s8a_trigger_sweep.py -rf
```

### 本走 (新テスト集合) — baseline PASSED、7/7 KILLED、node 集合完全一致

| ID | 変異 | 層 | 結果 | 種別 |
|---|---|---|---|---|
| M1 | direct consumer gate 削除 | consumer | KILLED (1 node) | **診断感度 pin** — 共有 quarantine が後段で同じ入力を拒否するため受理集合は不変 |
| M2 | calibration consumer gate 削除 | consumer | KILLED (2 node) | semantic kill — `validated_target` は quarantine を呼ばず return する |
| M3 | direct gate に mask 0 過剰拒否を注入 | consumer | KILLED (`[mask-00]`) | semantic kill (過剰拒否は他層が救わない) |
| M4 | calibration gate に同上 | consumer | KILLED (`[mask-00]`) | semantic kill |
| M5 | 共有 quarantine の membership block 削除 | shared | KILLED (2 node) | semantic kill — 真の受理集合差は `test_s8a_trigger_sweep.py::test_quarantine_scope_does_not_police_hole_content` が担う |
| M6 | M1 + M5 の両層同時削除 | 両層 | KILLED (4 node) | semantic kill — 両層を消して初めて `prepare_cell` が受理へ倒れる |
| M7 | M2 + M5 の両層同時削除 | 両層 | KILLED (4 node) | **冗長** — calibration は M2 単独で kill するため、M7 は冗長 gate の証拠 |

`DW-M03` に従い、M1 は kill 数に合算せず診断感度 pin として別枠に記録する。
実効 semantic kill は M2〜M7 の 6 件である。

### 対照走行 (旧テスト集合) — `DW-M08` の新旧両走、7/7 期待一致

同じ M1〜M7 を、**この wave が追加した 7 テストを `-k` で除外した集合**へ走らせた
(`mutation-spec-oldtests.json` / `mutation-ledger-oldtests.json`)。

| ID | 新テスト集合 | 旧テスト集合 | 純増検出力 |
|---|---|---|---|
| M1 | KILLED (1 node) | **SURVIVED** | 新テストだけが検出 |
| M2 | KILLED (2 node) | **SURVIVED** | 新テストだけが検出 |
| M3 | KILLED (1 node) | **SURVIVED** | 新テストだけが検出 |
| M4 | KILLED (1 node) | **SURVIVED** | 新テストだけが検出 |
| M5 | KILLED (2 node) | KILLED (2 node) | 既存テストで検出済み (差分なし) |
| M6 | KILLED (4 node) | KILLED (2 node) | 新テストが 2 node 追加 (consumer 層の消失は旧集合では不可視) |
| M7 | KILLED (4 node) | KILLED (2 node) | 同上 |

すなわち **consumer-local 層の退行は、この wave 以前のテスト集合では 1 件も検出できなかった。**
共有層 (M5) だけが既存テストの守備範囲だった。

この対照走行は Pegasus queue 混雑による dispatch rc=16 で 1 度 fail-closed 停止し
(`mutation-ledger-oldtests-aborted.json` に記録)、その後 untracked な insight による
clean-tree 拒否でもう 1 度停止した。いずれも harness の防壁が正しく発火したもので、
tree は毎回復元されている。記録 commit 後に新規台帳で走り直した値が上表である。

### 事前登録の誤りと是正 (段 6 レンズ B)

親が段 4 で登録した期待は 4 点で誤っており、走らせる前に是正した。是正しなければ harness は
node 集合の完全一致検査で全て `MISMATCH` にしていた。

1. M2 は テスト 6 だけでなく テスト 7 (`..._target_side`) も赤にする。
2. M5 の登録 node (`test_p3_s4_loop.py::...rejects_noncanonical...`) は、
   存在しない path を渡すテストなので gate 削除後は `FileNotFoundError` で赤くなる —
   **偽の kill** である。真の受理集合差は `test_s8a_trigger_sweep.py` 側が担う。両方を期待集合に入れた。
2. M6 / M7 は shared 層の 2 node も同時に赤くなるので、期待集合は 4 node である。
4. M3 / M4 は「mask 0 の検査を省く」ではなく「mask 0 を過剰拒否する」変異でなければ
   正例テストを赤にしない。一意な後者に固定した。

---

## 5. 受入

- 全走: `IZANAGI_TEST_TRIGGER=final python3 tools/run_tests.py` →
  **5974 passed, 19 skipped (462.03s)**。計算ノード request `889236.nqsv`。
- 対象 4 file: **201 passed**。計算ノード request `889232.nqsv`。
- provenance: `python3 tools/check_ai_provenance.py` → **1168 件、違反なし**
  (既存 waiver 8 件 = `codex-rate-limit`、forward-corrected 1 件)。
- login ノードでの直接 pytest は行っていない (Pegasus runbook の禁止に従い、
  すべて `tools/run_tests.py` の計算ノード dispatch 経由)。

---

## 6. 段 3 / 段 6 で出た scope 外 real 所見 (裁定パッケージへ)

いずれも real と裁定したが、**受理集合か凍結成果物の意味を変える設計択一**であり
[T-472] の射程外のため実装しなかった。詳細は本 insight §7。

---

## 7. 裁定パッケージ — ユーザー裁定を要する 4 件

### U-1 (P1) — `is_canonical_predicate` は `strip()` 同値であり、raw 受理集合は 32 個ではない

`trigger_gate_binding.is_canonical_predicate` は `text.strip() in CANONICAL_PREDICATES` である
(D160 が「strip 同値」を明記)。段 3 レンズ A の実測:

| 入力形 | membership |
|---|---|
| exact emitter 出力 | 受理 |
| 外周 space / tab / CRLF / `\x0b` / `\x0c` / NBSP / U+3000 | **受理** |
| 内部空白差、BOM、NFKC でだけ同値な全角、`str` 部分クラス | 拒否 |

問題は、受理後に**元文字列を `.strip()` せずそのまま `render_hole` へ渡す**ことである。
外周空白が materialized source に残り、`g++ -E -P` 相当のプローブで digest が変化した。
**同じ mask から複数の `src_token` / `variant_id` を作れる余地がある。**

- 成果物影響: 現行 6 値は exact なので既存値は不変。将来の空白付き freeze は
  同じ意味の mask に別 `src_token`・variant・WAL / 試行台帳参照を与え、
  重複候補として certified 選択と材料 proof chain を汚しうる。
- 択一: **(a) raw 完全一致へ戻す** (D160 の改訂を伴う) / **(b) strip 同値は受理するが、
  materialize 前に emitter の正準 bytes へ畳む** / (c) 現状維持。
- 親の推奨: **(b)**。受理集合を狭めずに identity 多重化だけを閉じる。

### U-2 (P1) — `prepare_cell` の `configuration` dispatch に拒否 `else` がない

`prepare_cell` は `system_gate` / `ident_all` / `sort_best` / `backoff_fixed_best` の 4 分岐しか持たず、
それ以外は **flags-only の `PreparedCell` を黙って yield する**。
`configuration="system-gate"` (ハイフン) のような別名を渡すと、述語検査も patch 適用も
quarantine も全て飛ぶ。現行の公式経路は measurement freeze の 18 セル exact schema と
S8b の ratified freeze / manifest 照合が塞いでいるが、**T-472 の目的
(共有 helper の偶発的閉包から consumer を独立させる) に対しては別の上流閉包に依存したままである。**

- 成果物影響: 将来または直接 caller では、構成ラベルと実際の flags-only source が食い違い、
  certified 選択・材料レポート・試行台帳が誤った configuration を参照しうる。
- 択一: **(a) 既知 6 構成 (`backoff_fixed_best` / `ident_all` / `p2_2_flag_opt` / `sort_best` /
  `stock_common` / `system_gate`) の allowlist にして未知を拒否** / (b) 検証済み cell 型だけを受ける /
  (c) 現状維持。
- 親の推奨: **(a)**。受理集合を狭める変更なので、`stock_common` / `p2_2_flag_opt` を
  必ず含めることと、S8b 側の全 caller を先に棚卸しすることが条件。

### U-3 (P2) — freeze 生成・検証層に semantic membership がない

`s1_known_axes_freeze` の取り込みは main/remeasure の**文字列一致しか見ない**。
`verify_document` も同じ producer から再構成するだけである。両 provenance が同じ非正準文へ
連動 drift すれば、**非正準な known freeze 自体を生成できる**。現在これを emitter と
照合しているのはテストだけである。

- 成果物影響: 非正準 freeze ができても新 consumer gate が実走を拒否するので誤 certification は
  防ぐが、known / measurement / holdout freeze と材料 proof chain が無効になり、
  S-1 / S8b は判定不能、校正 artifact は生成不能になる。
- 択一: (a) この面まで広げ、自己 hash・再凍結 cascade を受け入れる /
  **(b) 現 wave は sink-only と明記し、次回 refreeze より前に必須の別 T として閉じる。**
- 親の推奨: **(b)**。現行 bytes を守るため。

### U-4 (P3) — `sort_best.comparator` は閉じた権威集合を持たない別の real 面

`comparator` は C++ hole へ逐語 materialize されるが、trigger の 5-bit IR に相当する
閉じた権威集合がない。`backoff_fixed_best.backoff_us` は非負整数 + flags 一致 + `SWEEP_US` grid
選択なので**同型ではない** (直接 API が off-grid を受ける問題は別)。

- 成果物影響: comparator の連動 drift は source・certified 選択・材料レポートを変えうる。
- 択一: (a) 凍結 comparator provenance を十分な権威とする / (b) 別の閉集合か digest admission を
  定義する / (c) 別 T として起票のみ。
- 親の推奨: **(c)** — [T-472] とは独立の設計課題として起票し、費用は設計段で判定する。

---

## 8. 実装しないと裁定した所見

- **レンズ A should-fix「`ident_all` 固有の退行が固定されていない」**: 不採用。
  `prepare_cell` は `configuration in {"system_gate", "ident_all"}` の**共通枝**で述語を扱い、
  configuration 別の分岐を持たない。したがって configuration 固有の過剰拒否・迂回は
  現行コードでは等価変異であり、テストで区別できない。`ident_all` の受理は
  凍結 6 occurrence テストが既に固定している。U-2 が採択されたら再評価する。
- **レンズ B should-fix「S8b の system_gate / ident_all を実 `prepare_cell` へ通す正例がない」**:
  不採用。S8b の実 prepare canary は `stock_common` を選び、新 gate 枝を通らない。
  実 build を伴う正例は費用が大きい。**S8b 結線は未検証という制限**として本 insight に明記する
  (段 6 レンズ B の代案どおり)。
