---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: worktree-t2853-fig1-redraw
seq: 1
title: [T-2853] 残り (5'') fig1 (P2-5 誘導探索の否定的結果) の生成器を作り、後継図 fig1b を追跡下の入力から描いて旧図と値の一致を確かめた (コード + 図 + docs、新規計測 0、branch worktree-t2853-fig1-redraw)
---

## 本文

- 依頼: fig1 の生成器を Codex author で作り、凍結 fig1 を上書きせず後継図を別 filename + provenance で描き、旧図と値が一致するかを照合して記録する。本題だけ。
- 段 1 の生死確認 (login、1.3 秒) で新事実: P2-2 の 3 campaign は verifier epoch E0 で、既存の `search_baselines.run_workload` (認証読み出し) は拒否する。生成器は fig2b と同じ `HISTORICAL_RAW` で読み、当時の検証記録をそのまま使う。
- 段 2・3 は軽量版で省いた。段 6 はレビュー 2 本とも NO-GO (p 注記の固定文字列、caption に測定条件と記号の意味が無い、着地 closure が生成器の現 sha256 を比べる、照合が描かない値まで及ぶ)。
  焦点走 1 回目の赤 1 件 (新 test file に自走 harness が無い、`test_plain_runner_coverage.py`) は本 wave 起因で直した。焦点再レビュー 1 巡目の F-M1 (caption の共通条件の根拠) を fix 2 で閉じ、2 巡目 GO。
  不採用: 未到達数の照合 (summary が唯一の記録)、landscape の追加負例 (仮想リスク向け)。
- 段 1 brief の訂正: 「全一致」は summary 記録値との一致を指す。旧図の貪欲の四角が低く読めたのは読み取り側の偏りで、新図にも同じ偏りが出た。段 2・3 省略の理由「受理集合に触れない」は「既存の受理集合と正しさ防壁を変えない」が正しい。
- 焦点走 3 回 (Elapse 133 / 130 / 120 s) と変異 34 job (459 s) で計 0.23 node 時間。受入全走の結果は記録 commit の後なので本エントリには書かない。
- 記録 = `output/insights/2026-09-26/t2853-fig1-generator/README.md` (照合表・段の経過・変異)。

## 次の一手差分

### 更新

- [T-2853] **P1・(1)(1') の保全口と (2)(3) と (5) の計画・17 図の描き直し・fig1 の生成器は済み (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクと実行手順を要するので、実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。失敗候補と否定的結果を含めて公開してよく (D2212 項 6)、provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。初段 (量・保存費の見積り、trace の保存・公開方針、再実行の 3 経路) は `output/insights/2026-09-22/t2853-repro-package-estimate/README.md`、(2) job dir にだけあった論文根拠データの写し (repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/`、sha256 全件一致) と (3) 系列ごとの実行手順・R1 の入力一式は `output/insights/2026-09-23/t2853-repro-package-archive/README.md`、(1) の標準評価経路の trace 保全口は D2233 (env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in)、(5) の主要図の再実行計画は `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` で済んだ。**(1') 保全口の inventory に R1 の入力一式の残り (verifier の等価 argv・repo commit・完全 SHA の pin と宣言値・patch の bytes と sha256・verifier module の sha256) を D2160・B-8 の runner と同じ名前で足し、標準評価経路では build 時の source evidence と照合できたものだけを complete にした (D2247)。(5') のうち生成器のある 17 図の描き直しは値の差 0 で済んだ** (`output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md`)。**(5'') のうち fig1 は生成器 `tools/plotting/plot_p2_5_search_cost.py` と後継図 `fig1b_phase2_negative` を追跡下の入力だけから作り、旧図と値が一致した** (`output/insights/2026-09-26/t2853-fig1-generator/README.md`)。残り: (1'') 今後の論文根拠の実験 (P0・P1・P3・TPC-C) を走らせる前に、その実行経路 (job body) で保全口の opt-in を有効にする (保全先と容量は見積り稿 §7)。verify fan-out の兄弟 node の反復は保全対象外のまま。(4) P1 の関数単位の候補を受ける R2 の入口 (P1 の実装と同じ wave で)。(5'') fig15 の repo 外入力の写し、R2 は論文投稿前に投げる単位を決めて見積りを示し、2 node 時間以上ならユーザー確認後に投入する (D2212 項 4。計画稿の時点で、図 1 本で Elapse 単価から確認が要るのは fig10、fig13・fig4 は単価が無く未判定)。(6) 公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時 (目標投稿 2027-02-01、概要提出 2027-01-25)。新しく論文根拠になった job dir は、実験と並行で同じ手順 (保存先 `tools/`) で写す。
  base: 759e6fcead35df49dc431f047b1f7eaae992073103212f820adb0710a772c82a
