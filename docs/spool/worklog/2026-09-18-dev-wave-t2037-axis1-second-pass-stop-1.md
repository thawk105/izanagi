---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2037-axis1-second-pass-stop
seq: 1
title: [T-2037] 軸 1 OpenAlex の記録手番 — 独立 2 走目の停止 (D2120 項 14) を後継の凍結記録へ反映し、pass 1 の証拠を「限定付きの未検出」の材料として範囲と限界を固定した — 61 leaf が材料・16 leaf は数えない・未走 1、一般化は実測 6 本 + 見込みに限定、`RW1` 据え置き (docs のみ、request 0 件、branch worktree-dev-wave-t2037-axis1-second-pass-stop、変異 matrix 免除 = 実装面差分ゼロ、子ゼロ)
---

## 本文

- ユーザー依頼は「[T-2037] (D2120 項 14、ユーザー裁定 2026-09-17) 軸 1 OpenAlex の記録手番 — 独立 2 走目は止め、pass 1 の証拠だけで『限定付きの未検出』の材料とし、完走条件は満たさず `RW1` のまま、一般化は実測した 5 本の不一致と見込みに限定して docs/related-work 側へ反映する (docs のみ)。[T-2035] の再裁定 (項 14 の前提訂正、`Q6-SY2026` 106 頁) は取り込まず記録のみ。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の記録だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた (記録手番を消費した)。** 成果物は後継の凍結記録 `docs/related-work/claim-survey/2026-09-18-axis1-search-execution.md` と `claim-survey/README.md` の一覧 1 行。5 窓目 (`2026-09-17`) / 6 窓目 (`2026-09-17b`) の記録はどちらも項 14 の裁定より前に凍結していたので bytes を変えず (D1208)、2 走目の停止・材料の範囲・一般化の限定・5 窓目 §3 の一般命題文の読み方の限定を後継記録が持つ。decisions / failures fragment は無し (新しい設計判断・失敗なし)。
- 反映の中身: (1) 2 走目待ち 53 本は起動しない — checkpoint は bundle に残し、検査器・取得器・完走述語・bundle の bytes は不変 (停止は裁定であって機構の変更ではない)。(2) 落ちた leaf は据え置き — 裁定文が名指す 6 leaf は再取得しない。名指さない `Q1` / `Q4` / `Q5` (D1624 の再取得 1 回は 2〜6 窓目で未使用と bundle の attempt 数で実測)・2 走不一致 6 leaf・6 窓目で落ちた `Q6-SY2025` は新しい扱いを決めず既裁定のまま。(3) 材料の範囲 = 条件を通った pass 1 を持つ 61 leaf (完走 8 (年 shard 7 + 非 shard `Q2`) + 停止 53)、契約の条件で落ちた 16 leaf は材料に数えない、未走 1。限定 = OpenAlex のみ・catalog `2026-09-02` の 6 枝・cutoff `2026-12-31`・取得日 9/3〜9/17 の 6 窓・候補判定の 5 層は未実装・1 走の返却集合は完全とみなせない (9/3b)。**不在の文は 1 つも作っていない** (7.7.3 `RW1`)。(4) 一般化 = 実測した不一致 6 本 (2 窓目 `Q3-SY1992` 2 日で 1/8、5 窓目 `Q3-SY1997`〜`SY2001` 12 日で 5/5、いずれも `Q3` の 1〜2 頁 shard) と、残る 53 本 (48 本は pass 1 が 9/5〜9/8) についての見込みに限定。「同一集合の再現は成立しない」を一般命題として書かず、日数の関数として外挿しない。(5) [T-2035] の再裁定 ((a) 未走のまま 77 leaf で限定付き / (b) U12 窓またぎ / (c) catalog 再分割) は記録のみで先取りしない。
- 一次資料の実測 (login node、read-only、request 0 件): bundle manifest SHA-256 = `06fbef369ed0…` (6 窓目走行後の値と一致、mtime 2026-09-17 21:39:35 JST、399 MB)。2 走目待ち 53 の pass 1 の窓別内訳 = 17 (`t2090-openalex-20260903` = 2 窓目) / 29 (`…-20260907`) / 2 (`…-20260908a`) / 5 (`t2035-openalex-20260917a`) — 項 14 の「48 本は 9/5〜9/8」と一致。現行 main `d2ebef7a4` の `tools/check_axis1_search.py bundle` を offline で再走 (06:27 JST、rc=2) し、6 窓目の `bundle-check.json` と byte 一致 (SHA-256 `7a39126b…`)。5 本の不一致数値は 5 窓目の `evidence-detail.txt` 段 B と凍結記録 §3 が一致。
- 段 1 で pin 検査: `orchestrator/axis1_search/validator.py` の `FROZEN_PREDECESSOR_PATHS` は旧 epoch の 2026-08-27 の 2 file + insight 1 dir のみ。claim-survey の file 集合・README 一覧行を pin するテストは無し (テストは catalog JSON と axis3 登録文書の固定 path だけを読む)。`DW-O08` / `O09` / `O10` / `O11` / `O13` は不発火。
- 段 4 裁定: 実装しない (docs のみ、実装面差分ゼロ) → `4→7→8→9`。(P1)「材料の範囲と限界だけを記録し主張文を新設しない」を採用。裁定 inbox の再走査 = D2121〜D2134 に軸 1 の言及なし、未 fold fragment なし、main は着手時と同じ `d2ebef7a4`。
- 検査 (段 7、docs commit 前): 三軸語走査 rc=0 (holdout H1 / H2 の conjunction hit 0、positive control 188)、`check_docs.py` 違反なし。pytest の焦点走は login node の guard が pytest を拒否するため未実施 — claim-survey を読むテストは catalog JSON と axis3 登録文書の固定 path だけで、本 wave の変更 file を読まない (grep で確認)。受入全走は docs commit 後の最終 tip で投入し、結果は land の受領証 (本 fragment 執筆時点では未実施)。
- 工数: codex 子 0 本 (軽量版、docs-only)。親の実測: sha256sum 1、checkpoint 走査 2、bundle 検査器 1 走、三軸語走査 1、check_docs 1。

## 次の一手差分

### 完了

- [T-2037] D2120 項 14 の記録手番を消費した。後継記録 `docs/related-work/claim-survey/2026-09-18-axis1-search-execution.md` が 2 走目の停止・材料の範囲 (61 / 16 / 1)・一般化の限定 (実測 6 本 + 見込み)・5 窓目 §3 の読み方の限定を持ち、`claim-survey/README.md` から引ける。軸 1 は `未完走`・`RW1` のまま。[T-2035] の再裁定は別項のまま残る。
  remaining: none
  base: 7eda4b8b9a3d7ee4fd4753cf28cf068890ff80f7d780b8e491a885832f1fe159
