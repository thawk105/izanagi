---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: worktree-dev-wave-t2853-fig15-input
seq: 1
title: [T-2853] 残り (5'') fig15 の生成器が追跡下の逐語写しを既定入力に取るようにし、写しの sha256 が pin と 5/5 一致することを確かめてから描き直して、旧図と値の差 0 (PNG は bytes 一致) を確かめた (コード + docs、新規計測 0、branch worktree-dev-wave-t2853-fig15-input)
---

## 本文

- 依頼: fig15 (`mocc_witlight_four_arm`) の生成器が repo 外 job dir でなく追跡下の逐語写しを入力に取れるようにし、sha256 の一致を確かめてから描き直して旧図との値の差 0 を記録する。R2 と fig15 の観測の再実施は scope 外。本題だけ。
- 段 2・3 は軽量版で省いた。段 6 はレビュー 1 本 (2 レンズ) が NO-GO で、所見 4 件はすべて docs と brief の記述 (図 README に「repo 外 5 file」「外部原本」の残り、brief の「受理集合は広がらない」は配置まで含めると誤りで広がらないのは内容、新 test は公開 CLI のプロセス実行でなく `main()` の呼び出し)。全件採用し、親が docs を直した。実装面の fix は無し。
  焦点再レビュー 1 巡目は数値の検算が全項目一致のうえ文言 3 件で NO-GO (`tools/plotting/README.md` の「外部原本の閉包」の残りほか)、直して 2 巡目 GO。
- 焦点走 1 回目の赤 1 件 (`test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes`) は、作業ツリーに親の未 commit の docs 編集が載っていたためで、実装差分に帰属しない。docs を記録 commit に入れた後の受入で再確認する。
- 着手後に local main へ入った dev-wave 手順の改訂 (段 5 投入直後に consumer 検索を local main で再走) を遡って当て、consumer 集合は base と local main で同じ 8 file (差 0) だった。
- 変異 M1〜M3 は 3 / 3 KILLED (期待 node と完全一致)、対照 C0 は生存。焦点走 (Elapse 42 s) と変異 12 job (149 s) で計 0.053 node 時間。描き直しは login で node 時間 0。受入全走の結果は記録 commit の後なので本エントリには書かない。
- 記録 = `output/insights/2026-09-27/t2853-fig15-input/README.md` (sha256 照合表・leaf 比較・段の経過・変異)。

## 次の一手差分

### 更新

- [T-2853] **P1・(1)(1') の保全口と (2)(3) と (5) の計画・17 図の描き直し・fig1 の生成器・fig15 の入力は済み (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクと実行手順を要するので、実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。失敗候補と否定的結果を含めて公開してよく (D2212 項 6)、provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。初段 (量・保存費の見積り、trace の保存・公開方針、再実行の 3 経路) は `output/insights/2026-09-22/t2853-repro-package-estimate/README.md`、(2) job dir にだけあった論文根拠データの写し (repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/`、sha256 全件一致) と (3) 系列ごとの実行手順・R1 の入力一式は `output/insights/2026-09-23/t2853-repro-package-archive/README.md`、(1) の標準評価経路の trace 保全口は D2233 (env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in)、(5) の主要図の再実行計画は `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` で済んだ。**(1') 保全口の inventory に R1 の入力一式の残り (verifier の等価 argv・repo commit・完全 SHA の pin と宣言値・patch の bytes と sha256・verifier module の sha256) を D2160・B-8 の runner と同じ名前で足し、標準評価経路では build 時の source evidence と照合できたものだけを complete にした (D2247)。(5') のうち生成器のある 17 図の描き直しは値の差 0 で済んだ** (`output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md`)。**(5'') のうち fig1 は生成器 `tools/plotting/plot_p2_5_search_cost.py` と後継図 `fig1b_phase2_negative` を追跡下の入力だけから作り、旧図と値が一致した** (`output/insights/2026-09-26/t2853-fig1-generator/README.md`)。**(5'') のうち fig15 は生成器の既定入力を追跡下の逐語写し (`output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/`、sha256 は pin と 5/5 一致) に替え、写しから描き直して旧図と値の差 0 (PNG は bytes 一致) を確かめた** (`output/insights/2026-09-27/t2853-fig15-input/README.md`)。残り: (1'') 今後の論文根拠の実験 (P0・P1・P3・TPC-C) を走らせる前に、その実行経路 (job body) で保全口の opt-in を有効にする (保全先と容量は見積り稿 §7)。verify fan-out の兄弟 node の反復は保全対象外のまま。(4) P1 の関数単位の候補を受ける R2 の入口 (P1 の実装と同じ wave で)。(5'') R2 は論文投稿前に投げる単位を決めて見積りを示し、2 node 時間以上ならユーザー確認後に投入する (D2212 項 4。計画稿の時点で、図 1 本で Elapse 単価から確認が要るのは fig10、fig13・fig4 は単価が無く未判定。fig15 は R2 でなく観測の再実施で、元の認可が 1 回限りのため再実施には改めて認可が要る)。(6) 公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時 (目標投稿 2027-02-01、概要提出 2027-01-25)。新しく論文根拠になった job dir は、実験と並行で同じ手順 (保存先 `tools/`) で写す。
  base: a24aaca0d82cecce7dcef0e7ea36f1eb122af53951ff2d52c563a3403f9259a5
