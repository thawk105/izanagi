---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: worktree-t2853-archive-inventory-figure-redraw
seq: 1
title: [T-2853] 残り (1') 保全口の inventory に R1 の入力一式の残りを足し、(5') 生成器のある 17 図を描き直して値の一致を確かめた — inventory は verifier の等価 argv・repo commit・完全 SHA の pin と宣言値・patch の bytes と sha256・verifier module の sha256 を D2160・B-8 の runner と同じ名前で持ち、標準評価経路では build 時の source evidence と照合できたものだけが complete になる。17 図は rc=0、値の差 0、PNG は bytes まで一致 (コード + test + insight、branch worktree-t2853-archive-inventory-figure-redraw)
---

## 本文

- 依頼: [T-2853] 残りのうち (1') と (5') の描き直し。fig1 の生成器と fig15 の repo 外入力の写しは外。記録 `output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md`、設計判断 {{D:trace-archive-r1-inputs}}。
- 軽量版の dev-wave: 段 2・3 は省き (設計の択一は段 4 で親が決定)、評価経路の file なので段 6 の敵対レビュー 2 本・変異・受入は残した。実装面は Codex author (実装 1・fix 2)。
- 段 6: レビュー 2 本がそろって NO-GO で同じ must-fix (patch と HEAD を検証の後に取るので build 時の source とずれても complete になる) を出し、段 4 の「一致を gate にしない」を撤回して照合を入れた。焦点走 1 回目は 10 赤 (test の fixture に Silo の proof source が無く certified が偽 8 件、起動箇所の登録漏れ 2 件 = F39 の再発)。fix 1 の後、親の実測と焦点再レビューが独立に「現行 pin は 7 桁なので完全一致の照合は本番で恒常的に failed」を見つけ (F601 の再発)、fix 2 で build 側と同じ前方一致にした。焦点再レビュー 2 巡目で GO。
- (5'): login `pegasus02` で 17 図を job dir へ描き直した。fig2c・fig4 の生成器は出力 prefix が repo 外だと拒否するので worktree 内の一時 dir を経由した。provenance の leaf の差 142 件はすべて時刻・出力 path/sha・argv・生成器や検査器の sha・説明文の版更新・入力 2 件 (fig12 の planner-v4.md、fig2c の依存) で、未分類 0。node 時間 0。
- 変異: 12 件 (段 4 の 9・段 6 の 3) すべて KILLED、対照 1 件 SURVIVED。開発の検査の job Elapse 計 1,198 s ≈ 0.33 node 時間。
- 段 7 の記録レビュー (Codex read-only 1 本) が must-fix 2 (complete の保証の射程、再現 argv の差の内訳) を含む 5 件を出し、全件直した。
- 単独走 (D325): 変更 test file 2 本とも M1 形 (焦点走の 1 本をその file だけにした、test_t2853_trace_preservation.py 18 passed / test_ccbench_spawn_sites.py 73 passed)。

## 次の一手差分

### 更新

- [T-2853] **P1・(1)(1') の保全口と (2)(3) と (5) の計画・17 図の描き直しは済み (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクと実行手順を要するので、実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。失敗候補と否定的結果を含めて公開してよく (D2212 項 6)、provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。初段 (量・保存費の見積り、trace の保存・公開方針、再実行の 3 経路) は `output/insights/2026-09-22/t2853-repro-package-estimate/README.md`、(2) job dir にだけあった論文根拠データの写し (repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/`、sha256 全件一致) と (3) 系列ごとの実行手順・R1 の入力一式は `output/insights/2026-09-23/t2853-repro-package-archive/README.md`、(1) の標準評価経路の trace 保全口は D2233 (env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in)、(5) の主要図の再実行計画は `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` で済んだ。**(1') 保全口の inventory に R1 の入力一式の残り (verifier の等価 argv・repo commit・完全 SHA の pin と宣言値・patch の bytes と sha256・verifier module の sha256) を D2160・B-8 の runner と同じ名前で足し、標準評価経路では build 時の source evidence と照合できたものだけを complete にした ({{D:trace-archive-r1-inputs}})。(5') のうち生成器のある 17 図の描き直しは値の差 0 で済んだ** (`output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md`)。残り: (1'') 今後の論文根拠の実験 (P0・P1・P3・TPC-C) を走らせる前に、その実行経路 (job body) で保全口の opt-in を有効にする (保全先と容量は見積り稿 §7)。verify fan-out の兄弟 node の反復は保全対象外のまま。(4) P1 の関数単位の候補を受ける R2 の入口 (P1 の実装と同じ wave で)。(5'') fig1 の生成器の作成 (Codex author の別 wave)、fig15 の repo 外入力の写し、R2 は論文投稿前に投げる単位を決めて見積りを示し、2 node 時間以上ならユーザー確認後に投入する (D2212 項 4。計画稿の時点で、図 1 本で Elapse 単価から確認が要るのは fig10、fig13・fig4 は単価が無く未判定)。(6) 公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時 (目標投稿 2027-02-01、概要提出 2027-01-25)。新しく論文根拠になった job dir は、実験と並行で同じ手順 (保存先 `tools/`) で写す。
  base: 0e80b882158c60ee7129d215b5428204b4549074749e8738d8454e1a396194b4
