# 段 2 相当の plan (軽量版、親起草) — 変更面と導出方法

## 変更 file (4 本、すべて docs)

1. **新規** `docs/related-work/claim-survey/2026-09-19-axis1-materials-index.md` (凍結記録、request 0 件)
   - §0 身元 (作成日、登録 epoch、登録 commit、catalog SHA、bundle root、bundle manifest SHA = 18b と同じ値、
     数値の出所 = `output/insights/2026-09-17/t2035-axis1-openalex-window6/bundle-check.json` の `status.leaf_diagnostics` と
     `leaf-states.txt`。**検査器の再走はしない** — 18b が 2026-09-18 10:41 JST に offline 再走して window6 の出力と byte 一致を
     確認済み (SHA-256 `7a39126b…`)。本記録は request 0・bundle 非接触)
   - §1 何を起動したか = 何も (表: 全行 0)
   - §2 78 leaf の全列挙表: 列 = leaf ID (短縮 `Q3-SY2002` 等、正式 `AX1-20260902-E1-Q3-SY2002@openalex`)、区分 (A 材料 complete 8 /
     B 材料 停止 53 / C 落ち 条件 5 非 shard 3 / D 落ち 2 走不一致 6 / E 落ち drift 2 / F 落ち 条件 5 pass 1 5 / G 未走 1)、
     検査器 `state` / `reason_code` / `resume_action` / checkpoint 有無、完了 pass / 期待 pass。
     **区分の出所を 2 層に分けて明記**: A/B/G と C/D は検査器の最終状態コードから機械的に決まる。E/F は検査器では同じ
     `leaf_page_evidence_missing` + `resume_action=None` で区別できず、窓 4 記録 (`declared_total_drift`、`Q6-SY2014` / `SY2015`) と
     窓 3 / 5 / 6 記録 (条件 5 で `blocked_on_ruling`、`Q3-SY2025` / `SY2026`、`Q6-SY2021` / `SY2024` / `SY2025`) の逐語から採る。
   - §3 枝ごとの被覆: `Q1` 落ち / `Q2` 材料 / `Q3` = SPRE1991 + SY1991〜SY2024 のうち材料 = 29 (complete 6 + 停止 23)、落ち 8 (2 走不一致 6 + 条件 5 の 2025・2026)
     / `Q4` `Q5` 落ち / `Q6` = SPRE1991 + SY1991〜SY2026 のうち材料 = 31 (complete 1 + 停止 30)、落ち 5 (drift 2 + 条件 5 の 2021・2024・2025)、未走 1。
     → 数は表から機械的に再計算して書く (下の derivation)。
   - §4 限定 (18 §3 / 18b §3 を逐語で引き継ぐ: OpenAlex のみ・6 枝・cutoff・6 窓・候補判定 5 層未実装・1 走の返却集合は完全とみなせない・
     年 shard 枝の 2025・2026 年分は材料に無い・不在の文は 1 つも作らない・`RW2` は主張できない)
   - §5 未走 query の明記 (`Q6-SY2026`: 106 頁・21,040 件・1060 credit・D2150 項 4 で未走のまま置く、裁定待ちではない)
   - §6 次に残るもの (18b §5 をそのまま指す)、§7 凍結物への注記の限界 (D1208)、§8 母集合の外
2. **追記** `docs/related-work/claim-survey/README.md` の一覧表に 1 行 (`2026-09-19` の行)
3. **追記** `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」に 4 件目 + 「現在この節に積んでいる項目は 3 件である」→ 4 件
   - 内容: 最新版 2026-09-17 §8 C-4 と冒頭 §「先行研究調査そのものは、前版の時点で止まっている」(「3 窓ぶん」「2026-09-08 に打ち切り」
     「この版でも動いていない」) は執筆時点では真だが、2026-09-17 にユーザー直接指示で窓 5・6 が走り (T-2035、entry 1589 / 1631)、
     D2120 項 14 (2 走目停止・落ち据え置き) と D2150 項 4 (`Q6-SY2026` 未走のまま・77 leaf 限定) が裁定され、材料の範囲は
     18 / 18b / 本記録が持つ。**変わらないこと**: `RW1`・未完走・世界の不在を主張しない・候補判定 0 件・arXiv / DBLP 0 request・
     取得件数を「調べ終えた件数」と読まない・軸 3 は `RW0`・2 本目論文の B5 は別 (D1936 項 16)。
4. **spool fragment** `docs/spool/` (worklog、[T-2035] 完了) — 形式は `docs/spool/README.md`

## derivation (親が実行済み、`leaf-table.txt`)

`bundle-check.json` の `status.leaf_diagnostics` から `@openalex` 78 件を取り、state / reason_code / resume_action で A/B/C/D/G を機械分類、
E/F は名前で分ける。件数 = A 8 / B 53 / C 3 / D 6 / E 2 / F 5 / G 1 = 78。61 + 16 + 1 = 78 (18b §3 と一致)。

## 触らないもの

`docs/paper-story-backoff/` 全部、既存凍結記録、catalog、`tools/`・`orchestrator/`、bundle (repo 外)。
