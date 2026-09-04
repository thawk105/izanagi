# 段 4 裁定 (親、2026-09-04) — 逐語

軽量版 (DW-C00)。設計択一は割れず、正しさ防壁・受理集合に触れないため、段 2・3 の codex 子と段 6 の review 子を省いた。
実装面の差分は 0 なので変異 matrix は免除 (DW-S04)。受入全走は免除しない。

## 所見の裁定

| # | 所見 (子) | 親の裏取り | real / refuted | 採否 | scope |
|---|---|---|---|---|---|
| 1 | plot_backoff の検査は warn-only かつ保存後、fixture は 2 campaign・3 点・2 反復 | source 494-519 行、test 211-249 行、dat 実物 6 点で一致 | real | 記録 + 新規 T | 実装面は scope 外 |
| 2 | ss2pl は実 Figure を検査へ通す test が無い | test 696-700 行の monkeypatch で一致 | real | 記録 + 新規 T | 実装面は scope 外 |
| 3 | t2216 walk の model fixture が scenario 4/10、反復 3/8、cap50 無し | model 172-186 行 (Scenario 10 種)、test 777-800 行で一致 | real | 記録 + 新規 T | 実装面は scope 外 |
| 4 | s1_9pair の fixture に文脈セル ident_all / stock_common が無い | plot 51-67 行、test で PLOT_CONFIGURATIONS 4 種のみ生成を確認 | real | 記録 + 新規 T | 実装面は scope 外 |
| 5 | §9 が warn-only の _overlap_check を雛形に挙げている | FIGURE_CONVENTIONS.md 76-77 行で一致 | real | 採用 (本 wave で §9 を訂正) | scope 内 (規約書の訂正) |
| 6 | 生成器横断の meta test が無い | orchestrator/tests の参照 10 file が全部図種別で一致 | real | 不採用 (仮想リスク向け検査の新設は command 引数で scope 外) | scope 外 |
| 7 | 既存規定は F812 だけで規約書には無い | docs/dev-wave・decisions・roadmap・phase3 を grep、D1546 本文以外に無し | real | 採用 (§10 を純増) | scope 内 |

## (P1) (P2) の確定

- (P1) 「実寸」の定義は brief どおり。値の実数一致は求めない。§10 に明記した。
- (P2) 4 件はいずれも実在の欠陥 (実データで落ちる) ではなく被覆漏れ。全 6 図種の実図は生成済みで、fail-closed 検査を持つ 5 種はそれを通っている。優先度 P3 で新規 T にする。放置時に certified 選択・レポート・台帳の値は変わらない (DW-G05)。

## plan v2

1. FIGURE_CONVENTIONS.md: §9 訂正、§10 新設、「新しい図種を足すとき」に手順 1 件追加。
2. insight (本 dir) に棚卸し表・裏取り・限界を凍結。
3. worklog fragment: [T-2216] 完了、新規 T 4 件。
4. check_docs → 三軸語走査 → provenance 監査 → commit → 受入全走 → land。
