# [T-664] 段 1 brief — dev-wave docs 予算の削減候補棚卸し

## scope

`docs/dev-wave/**` (集約上限 25,200) と `.claude/commands/dev-wave.md` (9,500) の byte 予算逼迫に対し、
**上限引き上げ以外の 2 経路**で削減候補を棚卸しし、**裁定パッケージ 1 本**で返す。

- 経路 A = 陳腐化ルールの削除候補 (L2 節の剪定)
- 経路 B = prose の機械検査への移管 (テスト化)

**本 wave では `docs/dev-wave/**`・`.claude/commands/dev-wave.md`・`docs/skill-self-improvement.md` の
本文を 1 byte も編集しない** (ユーザー明示指示)。節の削除・移管の実施はユーザー裁定に限る。

## 実測 (2026-08-08、branch worktree-dev-wave-t664-docs-budget、HEAD 3ae4856c)

| file | bytes | cap | 空き |
|---|---|---|---|
| docs/dev-wave/core.md | 8,655 | 9,600 | 945 |
| docs/dev-wave/workers.md | 4,526 | 5,000 | 474 |
| docs/dev-wave/mutation.md | 3,674 | 3,750 | 76 |
| docs/dev-wave/operations.md | 8,329 | 8,400 | 71 |
| **docs/dev-wave/** 合計** | **25,184** | **25,200** | **16** |
| .claude/commands/dev-wave.md | 9,457 | 9,500 (最長行 140) | 43 |
| docs/skill-self-improvement.md | 5,997 | 6,000 (最長行 100) | 3 |

実効 gate は集約 25,200 (空き 16 bytes)。個別 cap 総和 26,750 は ceiling の 110% (27,720) 以内で、
1 file の cap を上げても集約が先に落ちる。

## 確定済みユーザー裁定 (覆さない)

1. **[T-127] (2026-07-28):** byte 上限の引き上げを提案しない。空けるのは陳腐化ルールの削除・縮約と
   テスト化。「3 bytes のために削り続けたのは苦し紛れ」との指摘あり — 小刻みな削り取りを成果にしない。
2. **[T-313] (2026-08-02、択 (a)、実装待ち):** byte 予算を常時読量 gate へ置換。
   「常に読む層は固定上限を維持、ノウハウ全体の固定文字数上限は撤廃」。**増枠ではない。**
   剪定の歯止め (何をゴミとするか) は未確定。
3. **[T-328] (2026-08-03、択 (b)):** dev-wave の逼迫は縮約でなく入口 + 条件付き reference への外出しで解く。
   ただし **D110 型の外出しを `docs/dev-wave/**` へ適用してはいけない** — 読了契約が leaf 節単位のため
   節をどのファイルへ移しても読了 payload の削減は 0。**D94 却下案 (a) (ファイル再編・新規 reference file)
   は同じ理由で却下済み**であり、本 wave で復活提案しない。
4. **[T-412] (裁定待ち):** 剪定する L2 節の**選定自体がユーザー裁定を要する**。
   D94 決定 (2) / skill-self-improvement routing 3 により、対象は
   **「L2 × 発火実績なし × テスト/機械検査で義務代替済み」の 3 条件を満たす節に限る**。
   「発火実績なし」は ID 件数でなく repo 全体 (insights・memo 含む) の意味検索で反証されないこと。
5. **[T-454] (裁定済み・起票可):** テスト化 pass の scope は確定済み —
   待ち手規約 3 条 + (217) の 3 候補 (`DW-O01` 残留 `.done` / `DW-M05` pgrep 自己一致 /
   `DW-M08` 期待 node 完全一致) + `DW-S06-B` への F112/F124 追記。**この確定 scope を作り直さない。**
6. **安全義務の削除・弱化は不可** (skill-self-improvement)。`check_docs.py` の
   `COMMAND_LIMITS` / `REFERENCE_LIMITS` 直上コメントが記録するとおり、過去に縮約案が
   `DW-S07` の安全義務を byte 予算のため落とした前科がある (手段目的の逆転)。

## 不変条件

- 本文編集ゼロ。成果物は `output/insights/` と repo 外パッケージ、および spool fragment のみ。
- 削除候補は 3 条件それぞれに**証拠**を付ける。1 つでも欠けたら候補にせず「不採」として理由を書く。
- テスト化候補は **DW-O13** に従い「その検査が読む実成果物のどの field か」を書く。書けない案は候補にしない。
- 恒真 (謳うだけで発火しない) 検査を候補にしない。`docs/failures.md` の該当型を攻撃面に入れる。
- 節約 bytes は実測値で書く。見積りには「実測 / 推定」を明記する。
- 既裁定 [T-412] / [T-454] / [T-313] / [T-328] と重複・矛盾する候補は、その関係を明記する。

## 成果物の形

1. `output/insights/2026-08-08_t664-docs-budget/inventory.md` — 全 L2 節と全 prose 義務の棚卸し表
   (節 ID・bytes・層・発火証拠・機械代替の有無)。不採の理由も残す。
2. 同 `package.md` — ユーザー裁定用。択一形式 (R1, R2, …)、各択の解放 bytes・失う保証・推奨。
3. 段 3 の敵対レンズ出力と段 2 プランの逐語。
4. worklog spool fragment 1 件。

## 分割方針

段 2 = codex read-only 1 本で棚卸し起草 (`reasoning=max`)。
段 3 = 異なる 2 レンズで並列攻撃 (`gpt-5.6-sol` → `gpt-5.6-luna`、`reasoning=max`)。
段 4 で親が real/refuted を裁定し package を確定。**実装 (本文編集) はしないので段 5・6 を飛ばし 4→7→8→9。**
受入全走は免除されない (`DW-S04`)。変異 matrix は実装差分ゼロのため射程外。

## provisional 裁定 (親の暫定 = 攻撃対象)

- **(P1)** [T-664] は [T-412] / [T-454] の上位タスクではなく、両者へ材料を供給する棚卸しである。
  package では 3 ID の統廃合案を出すが、統合の是非はユーザー裁定に返す。
- **(P2)** dispatcher (`.claude/commands/dev-wave.md`) は L0 = 常時全文読了であり、削減効果は
  reference 移管より大きい。しかし移管先は既存 reference 節に限られる (新規 file は D94 で却下済み)。
  よって dispatcher の候補は「既存 reference 節へ意味等価に統合できる行」だけになる。
- **(P3)** 集約 25,200 が実効 gate である以上、経路 A・B の価値は「解放 bytes」で測る。
  ただし [T-313] が実装されれば L2 は予算対象から外れ、経路 A の解放 bytes は**価値を失う**
  (剪定の動機は予算でなく「ゴミを増やさない」に変わる)。この依存関係を package に明記する。
