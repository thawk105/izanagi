# 段 4 裁定 — dev-wave-t244-p3-liveness

段 2・3 は `DW-C00` の軽量版判定で省略 (受理集合不変・正しさ防壁不接触・実装面は使い捨て probe 1 本)。
本裁定は親 brief の (P1)〜(P3) を確定し、`DW-M01` の変異を実装前に登録する。

## (P1) E leg の範囲 — **login の `--preview-wire` だけを採る**

- 採用理由: N2 の実測により ledger は `outcome` 文字列と `evidence_digest` の**意味を一切検査しない**
  (`_validate_result_matrix` は "rejected"/"tombstoned" の分岐と型検査のみ)。したがって計算ノードで
  実 iteration を回して得た outcome を載せても、**ledger 側の受理・counter・seal の生死判定は
  1 bit も変わらない**。`DW-G01` の「最安」に従う。
- **成果物影響:** compute leg を採らないため、「実 iteration の実行 outcome が ledger に載った」ことは
  名乗れない。名乗れるのは「実 driver が出した**候補 wire bytes**が載った」までである。実行 outcome の
  結線は D96 分割 wave (8c wiring) の担当。この限定を probe 出力・insight・worklog に明記する。

## (P2) 合格条件 — 4 点 + **独立実装制約**を追加

| # | 判定 | 実効 gate (`orchestrator/campaign/reflux_origin_ledger.py`) |
|---|---|---|
| C-a | `BatchCommitted` / `BatchResultsPrepared` / `BatchSealed` の 3 event が receipt を返す | `_commit_locked` |
| C-b | 同一 wire × R=2 が `replicate_ordinal` 0 / 1 の別 member として載る | `replicate != expected_replicate` (`_apply_event`) |
| C-c1 | seal 後に読み出した `candidate_bytes` が投入 wire (`"11111"` の ascii bytes) と完全一致し、`reflux_ir` 正準形である | `salted commitment opening mismatch` / `non-canonical candidate IR wire` (`_apply_event` / `_validate_candidate_wire`) |
| C-c2 | seal 後に読み出した `evidence_digest` が `--preview-wire` が**実際に出した** `diff_digest` と一致する | `salted commitment opening mismatch` |
| C-d | 負の control: R=2 の candidate commitment を同一にすると拒否される | `len({item.candidate_commitment ...}) != cardinality` |
| C-e | counter: `queries_used` が 0 → 2 へ、`iterations_used` が 0 → 1 へ動く | 同上分岐 |

**独立実装制約 (I6、新設):** probe は commitment・`origin_id`・`cell_key`・正準 JSON を
**ledger の private helper (`_member_preimage` / `_salted_commitment` / `derive_origin_id` 等) を
呼ばずに独立実装する**。先例 = `test_reflux_origin_ledger.py` の `_independent_origin` /
`_independent_cell` / `_canonical`。
→ **理由:** ledger の helper を共用すると、ledger 側を変異させても probe 側の期待値が同じだけ動き、
probe が緑のまま = **恒真な probe** になる。M-3 がこれを機械的に検出する。
使ってよいのは `_fixture_store_for_test` (store seam) と公開 dataclass / `commit_event` 相当の
`_commit_locked` 経路だけとする。

## (P3) 軽量版 — 採用。ただし段 6 の敵対レビューは 2 本回す

遷移は `1→4→5→6→7→8→9`。本 wave の産物は「生死が取れた」という**主張そのもの**であり、
恒真 probe / 名乗り過剰が中心リスクであるため review は省かない。

## 変異事前登録 (`DW-M01`、B-057)

対象は tracked file の一時変異 (`DW-O19` の復元規律に従う。全走は親)。無効化時の赤理由が
一つに絞れることを上表の gate 位置で確認済み。

| # | 変異位置 | 変異内容 | 期待 | 単一理由性の確認 |
|---|---|---|---|---|
| M-1 | `_apply_event` BatchCommitted 分岐の distinct 検査 | `len({...}) != cardinality` 項だけを恒偽化 | probe **C-d が赤** | 同 `if` の `cardinality < batch_cardinality_min` 項は残す。重複 commitment を拒否する層は前後に無い (query ordinal 検査・Qmax 検査は通る) |
| M-2 | `_apply_event` seal 分岐 `expected_replicate = next_replicates.get(raw, 0)` | 常に `0` を返す | probe **C-b が赤** (`replicate ordinal is not origin-canonical`) | replicate ordinal を検査する層は他に無い |
| M-3 | `_member_preimage` | wire bytes を preimage から落とす | probe **C-c が赤** (`salted commitment opening mismatch`) | probe が独立実装なら赤。**緑なら I6 違反 = 恒真 probe** として fix 対象 |
| M-4 | (正例) 変異なし | — | probe **rc=0、C-a〜C-e 全 PASS** | 過剰拒否の検出 |

受理集合を縮小する wave ではないため、追加の過剰拒否正例は M-4 で足りる。

## 実測で判明した追加事実 (段 4 で裁定へ反映済み)

`_validate_candidate_wire` は `candidate_bytes` が `izanagi-trigger-gate-ir/v1` の**正準 wire**
であることを要求する (`reflux_ir.encode_wire(parse_wire(raw)) == raw`)。したがって ledger に載る
候補 bytes は working_diff ではなく **5-bit wire 文字列**である。実 E driver の産物
(`diff_digest`) は `evidence_digest` として載せる。これにより「実 driver 出力が ledger に載る」
という本 wave の純増検出力は **C-c2** が担う。実測: `parse_wire/encode_wire` は `"11111"` を
不動点として返す。
テスト強化 wave ではないため `DW-M08` の新旧両走は対象外。

## 段 4 追補 (段 5 の 1 巡目で実装子が正しく fail-closed したため親が再裁定した)

**事実:** `_result_evidence_preimage` (`reflux_origin_ledger.py:622-631`) は `outcome` を
**`("accepted", "rejected", "tombstoned")` の閉じた語彙**に制限し、`accepted` / `rejected` では
`evidence_digest` を**必須**とする。1 巡目の実装子 prompt が例示した `"preview-only"` は
受理されない。実装子はこれを検出し、受理集合を勝手に広げず・値を発明せず、**何も書かずに停止した**。
これは段 4 の「指示にない受理集合の拡大・縮小をするな」に**適合した正しい挙動**である。

**親 brief N2 の訂正 (`DW-O12`):** brief は「ledger は `outcome` の意味を検査しない」と書いたが、
正しくは「**語彙は閉じており evidence の有無も強制される**。ただしどの語を選ぶかの妥当性
(実際に accepted だったのか) は自己申告で、`evidence_digest` の中身も dereference されない」である。
(P1) の結論 — compute leg を足しても ledger 側の生死判定は変わらない — は**変わらない**。
実行 outcome の妥当性は ledger の外で担保されるべきものであり、それを担うのは D96 分割 wave の
8c wiring だからである。

**再裁定:** `outcome` は **`"accepted"`** を使う。`evidence_digest` は preview の `diff_digest`。
そのうえで、実行結果との誤読は**値ではなく記述で**塞ぐ (新 I7)。

- **I7** probe の docstring・stdout・receipt JSON に、`outcome="accepted"` は
  **ledger の受理語彙上の値であって実 iteration の実行結果ではない**ことを明記する。
  receipt にはこの限定を機械可読な field (例 `outcome_semantics`) としても持たせる。

## 段 4 追補 2 — 変異の検出器 (段 6 preflight で確定。段 4 時点では未確定だった)

`DW-M05` は変異 harness を `tools/mutation_harness.py` に束縛し、runner を
`python -m pytest` または固定 HEAD の `tools/run_tests.py` に限る (`mutation_harness.py:451-464`)。
本 wave の検出器である `liveness_probe.py` は pytest node ではないため、**そのままでは
harness で駆動できない**。独自 harness を書く案は `DW-G01` (使い捨ての最安確認に専用機構を
作らない) に反するので却下する。

**確定:** probe を subprocess で起動し rc=0 と C-a〜C-e 全 PASS を assert する
**最小の pytest ラッパ 1 本**を新設し、それを変異 harness の runner とする。
新設は段 6 の Codex 実装子が行う (親は実装面を書かない)。

- 変異 M-1 / M-2 / M-3 の kill 判定は、このラッパ node が赤くなることで数える。
- M-4 (正例) は無変異でこのラッパ node が緑であることで数える。
- **この決定は段 4 時点ではなく段 6 preflight で下した。** worklog には裁定予定ではなく
  この実行順を書く (`DW-O12`)。

## 段 5 実装子への境界

- 編集してよいのは `output/insights/2026-08-05_t244-p3-liveness/` 配下の**新規ファイルのみ**。
- `orchestrator/` 配下・`reflux_origin_authority_v2.json`・docs・既存 tracked file は**読むだけ**。
- commit しない。docs を書かない。
- probe は 100 行以内 (`DW-G01`。**数え方 = コメント行と空行を除いたコード行**。実装子 prompt と
  逐語を揃えるため段 6 で訂正した)。`--preview-wire` の出力を引数か stdin で受ける形にし、
  probe 自身が重い処理を起動しない。
