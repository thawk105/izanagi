# 段 1 brief — [T-619] provenance 既定監査の範囲 (`--ancestry-path` の side-branch 盲点)

## scope

- **恒久形の設計まで**を成果物とする (ユーザー指定)。`tools/check_ai_provenance.py` の
  behavior 変更は本 wave で**実装しない**。段 4 で「実装しない」と裁定する予定であり、
  段 5・6 を飛ばして `4→7→8→9` とする (`DW-S04`)。
- 対象は既定監査の**選択集合の決め方**と、その上に乗る **epoch 適用述語**の 2 層。
- 成果物 = insights の設計文書 + 裁定パッケージ + spool fragment (worklog / decisions)。
  実装差分なしのため変異 matrix と受入全走は対象外 (`DW-S04`)。

## 確定済みユーザー裁定と起票元

- D221 却下項「既定監査の範囲計算 (`--ancestry-path`) を同時に直す — 実測では現に no-op で、
  裁定外の scope 拡張になる。所見として裁定へ返す」。これが [T-619] の起票元。
- [T-619] 自体の裁定は**無い** (rulings inbox を機構名で全文検索して 0 件)。
- 関連: [T-618] = `3f2c43d7` 台帳追加で裁定済み。[T-621] = 監査結果の consumer 不足 (別タスク)。

## 実測 (段 1 前、すべて実 repo)

| id | 事実 |
|---|---|
| M1 | base 層は今日も no-op。`--ancestry-path 50c1ef4e..HEAD` = 1701 = 素の range |
| M2 | 述語差は実 repo で発火する。anchor `f85e16e2` で 62 対 79 (差 17)。差を作るのは dev-wave の land topology (wave 側 merge → main を ff-only) |
| M3 | **epoch 層は現に発火中**。implementation epoch `8c6d3f3b` で 1238 対 1240、差 2 件 = `333605d6` / `6a9c97c4` |
| M4 | その 2 件は既定監査の対象だが `is_descendant(impl_epoch, C)` が False のため Codex author 契約が適用されていない |
| M5 | 述語を reachability へ統一すると `333605d6` は新規違反になる (shipped validator で実測: 実装面 `.py` 2 本、codex author 無し)。**全層 strict 化は no-op ではない** |
| M6 | `_audit_history` は順序非依存。`--reverse` の順序は結論に影響しない |
| M7 | 既定 range の membership を固定する既存 test は 0 本 (性質で検索) |
| M8 | 文書は既に plain 寄り (docstring / `PR-A02` / 入口「既定 full-history を権威とする」)。狭いのは実装だけ |
| M9 | byte 予算の余は `docs/ai-provenance.md` 13、family 6。**契約本文への加筆は事実上不可** |

## 追測 (段 2 起動後に親が測った。段 3 のレンズは必ずこれも検証すること)

| id | 事実 |
|---|---|
| M10 | scope epoch `2f0245c1` (2026-07-17) では ancestry=1579 / plain=1579。**差 0**。scope 層は reachability へ変えても現行 main で何も動かない |
| M11 | CAB epoch `9b26b3bd` (2026-07-29 16:41) では ancestry=1182 / plain=1206。**差 24 件** |
| M12 | その 24 件に `validate_message(..., check_cab=True)` を実測で当てた結果、**CAB 違反は 0 件**。CAB 層を reachability へ変えても現行 main では新規違反が出ない |
| M13 | ゆえに「全 4 層を reachability へ統一する」恒久形の**一回性コストは既知違反台帳 entry ちょうど 1 件** (`333605d6`、implementation 層、M5) である。base 層 0 / scope 層 0 / CAB 層 0 / implementation 層 1 |

**M13 は (P2) を弱める。** 親の provisional では「reachability 統一はコストが読めないので lineage 据え置き」
としたが、実測ではコストは 1 件で読み切れている。段 2 のプランと段 3 のレンズは、(P2) を維持すべきか
撤回すべきかを**この実測に照らして**判定すること。

## 不変条件 (攻撃してよいが、破るなら根拠を出すこと)

1. **規律 2** — 受理集合を広げる方向の変更だけを候補にする。狭める案は正しさゲートの緩和として却下。
2. **D221 の rc semantics を動かさない** — 正常時の rc は新規違反だけで決まる。既知は公開する。
   台帳追加は防壁の恒久緩和であり、ユーザー裁定の領分。
3. **`--message-file` 経路と forward correction (`PR-C01`〜`PR-C03`) の受理集合を変えない。**
4. **`docs/ai-provenance.md` と `docs/provenance/**` へ純増の加筆をしない** (M9)。
   設計の所在は insights + decisions とする。
5. **epoch は 4 つある** (base policy / scope / implementation / CAB)。同名で語らず、
   どの層の話かを毎回明示する (`DW-O13`、D75)。
6. 本 wave は `docs/ai-provenance.md` の bytes を変えない。ゆえに pickaxe needle
   (`scope=` / implementation needle / CAB needle) の最古 hit は不変で、epoch 解決は動かない。

## provisional 裁定 (親の暫定。攻撃対象)

- **(P1)** 恒久形の中核は「既定選択集合 = 素の `policy..HEAD`」である。今日 no-op (M1)、
  文書記述と一致 (M8)、受理集合は単調に広がるだけ (規律 2 に整合)。
- **(P2)** epoch 適用述語 (`is_descendant`) は**この wave では lineage のまま据え置く**。
  reachability へ統一すると既存 1 件が新規違反になり (M5)、台帳追加 = ユーザー裁定が要る。
  独立 2 例が同一 producer 内なので `DW-G03` は族一般化を許さない。
- **(P3)** ただし M3/M4 の穴を沈黙させない。「lineage で epoch 適用可否が決まらない commit」を
  診断として**公開する**案 (rc 影響は裁定) を、恒久形の第 2 部として設計する。
- **(P4)** 素の range に切り替えると、将来 pre-policy fork が land した際に真の legacy commit が
  新規違反として現れうる。その受け皿は D221 の既知違反台帳 (SHA ごとのユーザー裁定) であり、
  新しい免除機構を作らない。
- **(P5)** merge 時 attestation (新 trailer 種別) は D205 のプロトタイプ基準から過剰。設計メモ止まり。

## 成果物影響 (`DW-G05`)

- 放置した場合: policy 導入前に分岐した branch が後日 merge されると、その上の違反 commit は
  既定監査から落ち、**rc=1 であるべき既定監査が rc=0 になり commit gate の受理集合が広がる**。
  さらに epoch 層では現に 2 件が Codex author 契約の適用外にあり (M3/M4)、同型の穴が
  「実装面 commit に codex author が要る」という受理集合で開いている。
- 研究成果物 (certified 選択、材料レポート、試行台帳) の**値は不変**。変わるのは commit gate の
  受理集合と、新規違反が既存分に紛れる残余リスクだけ。

## 並列分割方針

- 段 2: read-only codex 1 本で file:line 粒度の恒久形プランを起草。
- 段 3: read-only codex 2 本を異なるレンズで並列。
  - レンズ A (正しさ防壁): 受理集合が意図せず狭まる経路、fail-open の残り、D221 との相互作用。
  - レンズ B (機構・運用): epoch 述語 4 層の整合、`_build_ancestry` の閉包前提、
    `--message-file` / correction / land 経路への波及、予算と文書所在。
- 段 4 で real/refuted 裁定 → 設計 v2 と裁定パッケージを確定。

## 受入・実測の環境

- 本 wave は実装差分なしのため受入全走・変異 matrix は対象外。
- 段 7 で `python3 tools/check_docs.py` と、docs commit 後の repo scan invariant を走らせる。
- provenance 履歴監査 (`python3 tools/check_ai_provenance.py`) は login node で自動 dispatch される
  (runbook §7)。commit 直前の `--message-file` preflight は免除。
