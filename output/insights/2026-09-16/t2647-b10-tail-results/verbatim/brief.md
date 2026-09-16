# 段 1 brief (親、逐語)

- **研究前進**: 本体論文系列の見送り台帳 B-10 (機序説明の帯域外への拡張) のうち、静的 backoff 右 tail 本走 (09-15 cohort) の結果を、論文の結果節・表・限定へ落とす材料として results 系列に固定する。完了判定 = 新 file `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` が原成果物 3 件 (SHA-256 実計算) から作られ、`docs/paper-story/README.md` の results 表に 1 行登録され、`check_docs` 緑・受入全走 child-green で land。
- **scope**: 新 file 1 + README の results 表 1 行。README 項目 3 (既存) は変えない。両論文系列の版・claim-evidence・figures・phase doc・decisions は触らない。gate・検査・台帳・一般化の追加なし (ユーザー指示)。
- **確定済みユーザー裁定** (引数): 言い方は prereg §4.5 の固定表現に限る。`performance_certified: false` のまま採用根拠にしない (規律 2)。論文図は作らない (insight §4 の 3 条件未充足)。D2050 の 2 本目 cohort の地位には触れない。
- **不変条件**: results 系列の規則 (D1631) — append-only、1 file = 1 cohort、数値・日付・判定は一次資料だけ、転記元 SHA-256 を書く、protocol の出力を成功宣告へ拡張しない (D12)。
- **一次資料 (直読済み・値は一致)**: `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/` の `.json` (5f426ecb…) / `.dat` (758b3121…) / `-complete.json` (7192d1da…)。集団 verdict、18 区間 declining、24 cell 平均、cv 範囲、identity の 3 job 一致、正しさ 120/120 certified・anomaly 0、perf bin 8 相異/workload、job id・開始時刻 (JST 15:19)・ホスト bnode017/018/019・所要を成果物から取った。
- **brief 前に実測した新事実**: (a) izanagi 側の source commit は成果物のどこにも記録されていない (残るのは事前登録 commit `cad6f46d8` の束縛と 3 job 一致の `freeze_trees_sha256`) → 限定として書く。(b) 正しさ検査 (`legacy` mode) の条件は性能測定と別の小設定 (`correctness_flags`: 4 thread・200 tuple・rratio 50・rmw true・extime 1・max ope 5) → 限定として書く。(c) `.dat` は 1 行ヘッダ + 120 行 (t2266 insight の「27 行目以降」は本稿へ写さない)。
- **provisional 裁定 (攻撃対象)**: (P1) file 名 `2026-09-16-b10-static-tail-not-observed.md`。(P2) README results 表 1 行の登録は「稿を置く」行為の一部 (A-2/B-7 全稿が登録済み・B-7 commit 362d23a40 が同 commit で 1 行追加)。(P3) 正しさ条件差 (b) を限定に含める。(P4) 段 2 plan は省く (骨格は A-2/B-7 と依頼で固定)、段 6 に read-only 敵対レビュー 2 本 (レンズ A: 過大主張・言い方の固定・scope 逸脱、レンズ B: 一次資料との一致・欠落・限定の網羅)。
- **並列分割**: 実装面ゼロ、親が単独で起草。子は段 6 のレビュー 2 本だけ。
- **変異 matrix**: 実装面差分ゼロ → DW-S04 で免除。受入全走は免除しない。
- **受入・実測環境**: 所在 = worklog、`tools/dev_wave_wait.py acceptance --lease-optional` の自動判定 (計算ノード混雑時は login)。

(注: 実際の段 6 では P4 のレンズ割当を入れ替え、A = 数値・逐語検算、B = 主張範囲とした。)
