# 段 6 レビュー裁定

## must-fix 2 件の裁定

### A の must-fix: `test_verify_rejects_one_byte_freeze_tamper` の期待値衝突 → **real、fix 済み**

- 親が repo 外 probe で実測確認した。凍結文書の `"sp_dd"` を `"xp_dd"` へ 1 byte 置換すると、
  `verify_document` が最初に呼ぶ `_validate_schema` の新 authority 検査が先に発火し、
  既存 node が期待する「機械再構成と不一致」に到達しない。無改変の文書は通る (回帰はここだけ)。
- 当該 node は submodule が見えない dispatch 環境では skip されるため受入全走では表面化しないが、
  login node では実際に到達する。潜在回帰として直した。
- fix: 改竄対象 byte を `"what": "S-1` → `"what": "X-1` へ移し、**期待メッセージと例外型は据え置き**。
  加えて `test_verify_rejects_sort_name_tamper_at_authority_layer` を新設し、
  name tamper が authority 層で止まる新しい挙動を明示的に固定した。
- 親の実測: probe で 2 node の本体を pytest 無しに再現し、
  NODE1 = `freeze JSON の内容が現行 generator による機械再構成と不一致`、
  NODE2 = `entries.balanced.sort_best.name/comparator が権威集合と不一致` を確認 (`PROBE_ALL_OK`)。
  fix 後の焦点走は 38 passed / 9 skipped, rc=0。

### B の must-fix: 新 authority module が凍結 source closure に無い → **must-fix としては refuted。backlog へ**

- 実測: `_sort_entry` の `sources` は `_module_source(s6_sort_sweep, ...)` と
  `_module_source(s6_sort_sweep.S, ...)` を pin する (`s1_known_axes_freeze.py:515,516,564,565`)。
- **trigger 軸も同じ性質を持つ。** trigger の `common_module_sources` は
  `trigger_axis` と `s8a_trigger_sweep` を pin するだけで、束縛実装である
  `trigger_gate_binding` を pin していない (`:617-619`)。`_module_source` の全 call site は
  `:374, :423, :515, :516, :564, :565, :618, :619` の 8 箇所で、束縛 module は 1 つも入っていない。
- したがって B の所見は**本 wave が作った欠落ではなく、両軸に等しく存在する既存の性質**である。
  sort 側だけ pin を足すと、T-493 が消そうとした非対称を逆向きに作ることになる。
- 受理集合を決める値 (`CANDIDATES` の 15 組) は既に pin 済みで、pin されていないのは導出ロジックである。
  この点も trigger と同一である。
- ユーザーの「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と `DW-G05` に照らし、
  本 wave では実装しない。**両軸の束縛 module を 1 つの変更単位で pin する** backlog 項目として
  裁定パッケージへ送る (`DW-G03` の独立 2 例が揃っている型)。

## nit の裁定 (いずれも本 wave では実装しない)

- A: 正例が live `CANDIDATES` を入力と期待値の両方に使い、同数の候補置換を独立に検知しない。
  → real。ただし独立 golden の新設は台帳の追加であり scope 外。backlog。
- A: exact-type 分岐の直接の退行テストが無い。→ real だが nit。MUT-1 が型分岐を含む raise 全体を
  覆うため、単独の退行検知が完全に欠けているわけではない。
- A: 実装子報告の「自走 harness を実装した」は「既存 harness へ自動収集される test を足した」が正確。
  → 記録側で正確に書く。
- B: 新規 10 node が `acceptance_duration_ledger.json` に未登録。→ B 自身が
  「未登録は赤にならない」と `conftest.py:1522-1542` で確認済み。受入全走後の実測値追随は
  台帳品質の事項であり land 条件ではない。
- B: 波及列挙の不足。→ real だが、B 自身が「現在の新 module に反応する対象文字列や call site は無い」と
  判定している。親は glob 走査メタ test (`test_plain_runner_coverage.py`) を実走済み (3 passed)。

## 変異事前登録の erratum (DW-M08 に従う)

段 4 で凍結した期待 node 集合を、実装後の実テスト構成に照らして訂正する。**登録の意図は変えない。**

- **MUT-1** — 期待 node を 2 件から **6 件の完全集合**へ訂正する。親が
  `orchestrator/tests/test_sort_comparator_authority.py` と
  `orchestrator/tests/test_s1_known_axes_freeze.py` の関数一覧を実測して確定した。
  6 件はいずれも dispatch 環境で skip されず実走する (焦点走 -v で PASSED を確認済み)。
- **MUT-2** — 変更なし。2 件で閉じる。
- **MUT-3** — **単独変異の証拠から外す**。「常に拒否」へ倒すと、schema の workload loop 後半へ
  到達できなくなる trigger 系 node や、`build_document` を前処理に使う node まで巻き込み、
  赤の理由が一つに絞れない (`DW-M03` の過剰決定)。
  受理集合を狭める wave が要求する**承認外の過剰拒否の正例**は、変異ではなく
  `test_validate_schema_accepts_frozen_sort_entries` と `test_all_fifteen_candidates_bind` の
  2 つの正例テストが担う。両者は焦点走で PASSED を実測済みである。
  この訂正は erratum として残し、初回登録を消さない。
