# [T-2632] 段 1 brief (2026-09-20、親、訂正前の逐語)

- 研究前進: 論文の B-4 (還流 ablation) 実験は、赤 precursor ごとに proposal・走行・共通参照点を束縛できないと母集合 (analysis_manifest) を組めず開始できない (D2100・D2120 項 5)。本 wave は「現存資料で束縛できるか」を各辺で確定し、耐久 carrier 新設 / D39 決定 3 変更の裁定が要るかを決める。完了判定 = insight README に辺ごとの閉包表 (path + sha256) と結論 1 つ。
- scope: read-only precheck、実装差分ゼロ。対象 = tracked な合成ループ campaign 3 件 (base 0b53a387 / sort 3be89e0d / trigger 3f72ecd5) の全 whiteboard 行 7 件と、現行保存形式が新規走行で残す carrier (WAL・loop_state・campaign.lock・agent_outputs journal (opt-in)・trigger provenance report・K2 手動 loop の insight 収録物)。§5 の 2 欄記入・床値・bootstrap 集合定義・carrier / 台帳 / gate / 検査の新設はしない。
- 確定済み裁定: D2100 (12 field は現行保存形式に出所なし、静的分類)、D2120 項 5 (1)〜(3)、D1986 項 4 (少数は記述報告まで)、D1936 項 8 (追加基盤不採用)、D39 決定 3 (whiteboard 5 field、proposal 非保持 = D1846)、D1483 (§5 の順序)。
- 不変条件: 規律 2 / 3 / 6 / 7 を緩めない。所属真偽値を後付けで真にしない。「再現できない」と「事実でない」を分ける。数値・hash は現物 bytes から取る。
- 成果物: `output/insights/2026-09-20/t2632-b4-evidence-provenance/README.md` (+ `verbatim/` に親の実測 script 出力とレビュー逐語)。辺ごとに「閉じた / 現存資料では閉じない」と、閉じない場合の不足を裁定パッケージとして書く。
- 分割方針: 軽量版 docs-only。一次資料から事実を再抽出する wave なので段 6 の read-only codex review 1 本 (2 レンズを 1 本で担う: (a) 束縛の意味論 = 何が何を hash しているか / (b) 現物の再計数と不在断定の射程) を残す。段 2・3 と実装子は省く。
- 受入・実測環境: login node (pegasus02) での読み取りのみ。計算ノード dispatch なし。受入全走は docs-only (output/insights のみ) のため `dev_wave_wait.py acceptance` の要否を段 7 で DW-O18 に従い判定。
- (P1) 「現行保存形式では proposal ↔ 走行の辺は閉じない」= 親の provisional 裁定・攻撃対象。反証候補: agent_outputs journal (opt-in、`source_sha256` + `--agent-variant`)、trigger の provenance report (iteration → variant、proposal_path は非耐久)、K2 insight の materials (proposal-4.json + wal-refs.json)。
- (P2) 「走行 ↔ 参照点の辺は、参照点 object (certified snapshot / throughput receipt) の producer が無いので現存資料では定義できず閉じない」= provisional。反証候補: WAL commit/bench_done record を snapshot/receipt と読む解釈 (T-2102 が「この量の記録は WAL 終端 commit record にしか無い」と確定)。
- (P3) 「現物 7 行はすべて success なので precursor は 0 件、辺の閉包は空虚に真であり、裁定に必要なのは『形式として閉じるか』の判定」= provisional。base の whiteboard 4 行に対し WAL variant 3 件 (重複解決 `_resolve_duplicate`、id を持たない) という事実は形式の反例。
- 段 1 の再評価: DW-O08/O09/O10/O13 不成立 (凍結物・gate に触れない)。DW-O05 は段 6 直前に読む。
