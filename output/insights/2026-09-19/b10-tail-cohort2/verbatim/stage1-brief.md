# 段 1 brief — B-10 静的右 tail 第 2 cohort (独立再現) の投入

日付: 2026-09-19 21:49 JST。wave: dev-wave-b10-tail-cohort2。worktree branch `worktree-dev-wave-b10-tail-cohort2`、起点 local main `a99425b66` (clean)。

## 研究前進
論文 B-10 (機序説明の帯域外への拡張) の静的右 tail 特性化について、cohort 1 (2026-09-15) の verdict
`not-observed-in-any-workload` に対する**独立再現 1 本**を得る。完了判定 = cohort 2 の 3 job が
`completion.json` を出し、本番 CLI の集団報告 3 成果物が repo 外に生成され、cohort 2 の results 系列稿
(cohort 1 稿と同型・一次資料束縛) と fig8 再現欄の材料 (group id・verdict・成果物 SHA) が commit されること。

## scope
1. 事前登録 `docs/b10-backoff-static-tail-preregistration.md` に日付付き追記 (cohort 2 の地位 = 独立再現、cohort 1 verdict を主、cohort 2 verdict は再現欄に併記、合成しない) を**結果を見る前に** commit。既存本文は 1 byte も変えない。§5 spec bytes 不変 (spec SHA `08f5849b…` を test が pin)。
2. その commit を `--preregistration-commit` として `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2500-tail-formal` で 3 workload を 3 job (各 1 ノード) に投入 (機構は cohort 1 と同一)。
3. 完走後、本番 CLI (`b10_backoff_static_tail_formal.py report`) で集団報告を repo 外へ生成。
4. cohort 2 の results 系列稿 `docs/paper-story/results/2026-09-<日付>-b10-static-tail-cohort2-<verdict slug>.md` と README 表の 1 行、insight、spool fragment。
scope 外 (依頼どおり): 901〜998 µs 帯 (D2044 項 14)、v2 consumer 移行 (D1936 項 36)、追加 gate、fig8 生成器の改変 (実装面 → 別 wave の Codex author)、cohort 1 稿の改変。

## 確定済みユーザー裁定
- 2026-09-19: 「第 2 cohort は独立再現。cohort 1 の verdict を主として保持し、cohort 2 の verdict は再現欄に併記する。合成はしない」。
- D2050 (2026-09-16): 2 本目は地位を結果より前に明記してから投入 (本 wave はその充足)。
- D2044 項 14 / D1936 項 36: 帯と v2 移行は現状維持。

## 不変条件
- 絶対規律 2/3/7: 正しさは trace-enabled の別走行 (driver 内蔵)、`performance_certified: false` 維持、cohort 1 の判定は不変・遡及変更なし。
- 事前登録 §4.1/4.2/4.5/4.6: 格子 8 点 × 3 workload × 5 反復、§4.5 固定表現 (「表現可能域 9999 µs までに飽和を観測しなかった」以外の言い方をしない)。
- 投入後〜完走まで worktree に 1 byte も書かない (F936: job は起動時点の作業ツリーを再照合)。
- 探索走 campaign は cohort 1 の再導出 (2026-09-16) と同じ v1 balanced (`…-783ccbe8`) を渡す (mode `legacy` 一致は 3 本とも実測済み)。

## 実測した前提 (2026-09-19 21:4x JST)
- cohort 1: group `b10-backoff-grid-20260915T061814Z-545445`、job 998865/6/7、投入 09-15 15:18 JST・完走 15:33 (各約 14 分)、repo commit `0600887d9`、隔離 worktree の repo root から投入 (insight 2026-09-15/t2266-tail-band §5)。
- 事前登録の作業ツリー bytes = `cad6f46d8` の blob (sha256 `8084be04…`、71,231 bytes)。driver `load_preregistration` は作業ツリー bytes == 束縛 commit の blob を要求 → 束縛 commit は追記後の新 commit。
- DW-O09 pin 閉包: `8084be04…` の hit は fig8 provenance (cohort 1 の歴史記録、生成器は外部入力の complete.json から読む)・cohort 1 results 稿 (凍結)・insights (歴史) のみ。live 比較は `test_b10_backoff_static_tail_formal.py:49-51` (HEAD blob vs 作業ツリー + spec SHA pin) と `test_b10_backoff_grid_submit.py:139` (§8.2 の literal)。追記は両方を壊さない (§8.2 と §9 の見出しを増やさない)。
- gen_S: ENA/ACT、running 29・queued 12。探索走 campaign 実在。
- 模擬/実の差: 投入・完走・集団報告はすべて実 (模擬なし)。

## (P1) 親の provisional 裁定 — 攻撃対象
- (P1-a) 追記は末尾の日付付き節に加え、§0 「本書の版と発効」へ 1 行の日付付き記載を**挿入**する (§0 自身の更新契約「変更理由と変更時点を本節へ明記」を満たすため。09-10 追補はこれを欠き insight 2026-09-16 §3.2 が real 所見にした)。既存行の変更・削除は 0。
- (P1-b) cohort 2 の束縛は「追記込み commit」であり、cohort 1 の束縛 `cad6f46d8` とは blob が異なる。spec SHA は同一。cohort 2 稿はこの差を §1.1 に明記する。
- (P1-c) cohort 2 の集団報告は同じ本番 CLI・同じ引数形で、出力先は `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-<日付>-cohort2/` (cohort 1 の `group-report-20260915` と同じ親、別 dir)。
- (P1-d) results 稿の verdict slug は結果を見てから file 名に入れる (cohort 1 稿と同型)。地位・併記の形は結果前に事前登録追記で固定済みなので、file 名の slug は後付け判断にならない。

## 成果物の形
- commit 1: 事前登録追記 (docs-only)。投入前に単独 commit。
- commit 2 (完走後): results 稿 + README 表 1 行 + insight (`output/insights/2026-09-19/b10-tail-cohort2/`) + spool fragment (worklog)。
- 実装面差分ゼロ → 変異 matrix 免除 (DW-S04)。受入全走は免除しない。

## 段 4 相当の裁定 (consult 所見 9 件、2026-09-19 22:05 JST)
- 所見 1 (§0 挿入は append-only でない): real・採用。§0 への挿入を取り消し、§0 が求める記載を末尾追記の冒頭に置いた。cad6f46d8 の 71,231 bytes が新 file の先頭部分として sha 一致 (実測)。P1-a は**採らない**に改める。
- 所見 2 (併記先と「改めない」の区別): real・採用。項 2 を「主結果固定 + 既存稿・図は凍結 + 第 2 cohort の稿と fig8 再現欄に両 cohort を区別して併記」へ置換。
- 所見 3 (未完走時の開示): real・採用。項 4 に未完走・報告生成失敗時の §7 開示と verdict 不在の明記を追加。
- 所見 4 (前向き性の対象): real・採用。冒頭に「対象は未投入の第 2 cohort だけ」を追加。
- 所見 5・6 (別 blob 束縛・test pin): refuted に同意。commit 後に test 2 本を実走する。
- 所見 7 (「3 本目」): real・採用。削除し「第 3 cohort の実施・地位は本追記では定めない」に置換。
- 所見 8 (探索走 path): 明確化を採用。exact path と用途、cohort 1 投入時 argv 非保存を明記。
- 所見 9 (brief の §4.5 一般化): real・brief 修正。不変条件を「verdict ごとに §4.5 の分類と表現制約を守る」と読む。項 7 も同趣旨に改めた。
- P1-b: 採る。P1-c: 条件付きで採る (報告時に出力先の 3 成果物不在と、同一 group の 3 campaign 入力を確認)。P1-d: 条件付きで採る → **results 稿の file 名は結果前に中立名 `2026-09-<日付>-b10-static-tail-cohort2.md` に固定** (verdict slug を file 名に入れない)。

## 並列分割方針
軽量版 (docs-only)。段 2・3 省略。**ただし** 追記は結果後に訂正できない事前登録なので、commit 前に read-only codex 1 本で追記文を攻撃させる (段 3 相当・1 本)。段 6 は cohort 2 稿に対する独立 read-only レビュー 1 本 (DW-C00 の docs-only 再抽出型)。実装子ゼロ。
