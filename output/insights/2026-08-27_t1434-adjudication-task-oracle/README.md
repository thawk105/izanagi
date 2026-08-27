# [T-1434][T-189] adjudication 層の task-specific oracle 対応 (2026-08-27)

- 対象: `tools/codex_reasoning_ab.py` の `_load_adjudication` / `_aggregate_verified` と、
  `docs/phase3-t189-model-routing-preregistration.md` の到達度記述。
- wave: `dev-wave-t1434-adjudication-oracle`
  (branch `worktree-dev-wave-t1434-adjudication-oracle`、base `dd66213978d3d30eed567484ec013216bff6926b`)
- 実装 commit: `c63d26011`

## この wave が閉じたこと

事前登録文書の残余 (b)。`_load_adjudication` は mapping reveal 後に走るのに、verdict 行の
`equivalent_to` を task manifest **全体の union** で検査していた。この関数は
`packet_id -> run_id -> slot` の join を持つので packet ごとの task が同定できている。
その task 自身の `known_finding_ids` で検査する形へ受理集合を狭めた。あわせて同じ join の
`oracle_kind` を combined verdict へ `combined_verdict_sha256` の計算前に束縛した。

## 閉じていないこと

§8 の独立 oracle ledger は**依然として未作成**である。その固有 hash 契約、finding schema
(severity / must-fix / 根拠 artifact / 検出条件 / canonical identity)、task 固有 acceptance
(`unbound` のまま)、§8 の記述的 coverage の集計は、いずれもこの wave の scope 外である。
到達度は `実装済み` ではなく **`部分実装`** とした。

## 実測で分かった一番大事なこと

**組込み `TASK_MANIFEST` は POS/NEG の双方へ同じ `known_finding_ids` (11 件、
`A-1..A-4, B-1..B-6, R-1`) を入れる。** したがって task 別集合と manifest 全体 union は
同一集合であり、この wave の narrowing は組込み manifest の入力では 1 度も発火しない。
**同じ理由で、既に「機構は着地」と記録されていた `_aggregate_verified` の task 別検査も、
現行入力では 1 度も union より狭い受理集合を作っていなかった。**
「機構は着地」は存在の主張であって発火の主張ではない。

この事実は、テスト設計を決定づけた。負例は **manifest union には含まれ、対象 task の集合には
含まれない** finding ID を使わなければ、既存の union 検査だけで落ちて新実装とは無関係になる。

## verbatim

- `verbatim/s1-brief.md` — 段 1 brief (**段 3 で 4 件が反証された。訂正は段 4 裁定を正本とする**)
- `verbatim/s2-plan.md` — 段 2 プラン (codex, read-only, xhigh)
- `verbatim/s3-lensA.md` — 段 3 敵対相談 レンズ A (正しさゲートの健全性)
- `verbatim/s3-lensB.md` — 段 3 敵対相談 レンズ B (機構の実効性と恒真化)
- `verbatim/s4-ruling.md` — 段 4 裁定 (**所見 13 件すべて real。変異事前登録 M1〜M9 を含む**)
- `verbatim/s5-author.md` — 段 5 実装子 (codex, workspace-write, xhigh)
- `verbatim/s6-reviewA.md` — 段 6 敵対レビュー A (所見 0 件)
- `verbatim/s6-reviewB.md` — 段 6 敵対レビュー B (must-fix RB1 / RB2)
- `verbatim/s6-fix.md` — 段 6 fix 子 (RB1 の単一理由化)
- `verbatim/s6-refocus.md` — 段 6 焦点再レビュー (対応表、GO)
- `verbatim/mutation-matrix.md` — 変異 matrix の結果 (別 commit)

## 段 3 が親 brief を覆した 4 件

1. **join 前提が誤り。** verdict 検査ループは `mapping` の辞書化と `slot_by_run` の構築より
   **前**に走る。既存の検査位置へ `benchmark_task_id` を渡すことはできない。
2. **「真部分集合」は一般には偽。** 等しくなる場合が 3 つある (組込み manifest / task 1 件 /
   対象 task が union 全体)。
3. **「bytes で pin する台帳・trust root は存在しない」は偽。**
   `output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json` が
   `tool_sha256` = `58f1176e0ff705ade85ac0cec0c15b77a26f8eaa2d75bb3f7d711519ed6657f7` を持つ。
   現行 `tools/codex_reasoning_ab.py` の SHA-256 は
   `777840d105088a418daa6c4ae8ae747df58d511c071b4a9ed6d18106cc9a36de` で**一致しない**。
   F39 の分類は**歴史記録**であり、更新閉包 0 件という結論自体は維持した。
4. **成果物影響が実コードと不一致。** §8 の記述的 finding coverage の分子は実装されていない
   (`output/` に `judgments` を持つ material manifest は 0 件)。実際に変わるのは
   `valid` / `experiment_complete` と、無効時に null 化される主台帳である。
