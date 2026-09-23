---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: worktree-t2853-rerun-plan
seq: 1
title: [T-2853] 残り (5) 主要図の再実行計画 — 論文の 20 図ごとに経路 (描き直し / R2 / 独立探索のやり直し) を決め、元の測定の所要から node 時間を出所つきで積み上げた。最小の経路は描き直し (node 時間 0)、G が要る図は無く、図 1 本で Elapse 単価から確認が要るのは fig10 (fig5/7 は推奨しない、fig13・fig4 は単価が無く未判定) (docs のみ、計算なし、branch worktree-t2853-rerun-plan)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `verbatim/request.md`): [T-2853] の残り (5)。(1)(1') 保全口と R1 の入力一式は [T-2849]、(4) P1 の R2 入口は P1 の wave の担当なので触れていない。記録 = `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md`。decisions fragment は作っていない (計画は insight を正本にし、確認の線は既存の D2212 項 4・D2219 項 1 をそのまま当てた)。
- 母集合は `docs/paper-story/figures/README.md` の図一覧の 20 図 (ComSys 原稿の `\includegraphics` は fig2b・fig4・fig9・fig14・fig15)。描き直しで再現できるのは生成器のある 17 図。fig1 は生成器が repo に無い (値の出所 `p2-5-summary.json` は追跡下)。fig2・fig3 は後継図を使うので対象外。
- R2 を推奨するのは 9 図 (fig2b・fig2c・fig4・fig6・fig8・fig8b・fig10・fig11・fig13)。fig15 は TRACE=1 の非 certifying 観測なので R2 ではなく「固定条件の観測の再実施」(1.67 node 時間、元の認可は 1 回限り)。fig5・fig7 は D1645 の用途制限が残るので推奨しない。fig9・fig14 は D2211 項 10 の保留。R1 の対象になる図は無い (D2160・B-8 は図を持たない)。
- 所要の出所は (a) NQSV の Elapse、(b) driver 記録、(c) WAL 時刻差、(d) 投入〜完了、(e) walltime 上限に分けた。図 1 本で (a) の単価から 2 node 時間以上 = fig10 (3.40、(a) × 5 node)、fig5/7 (2.02)。fig13 は (a) が無く未判定 (確保枠 (e) 48 h、(d) の 18.68 h は待ちを含む参考値。単価の無いまま投げるなら確保枠を示して確認を取る)。fig4 の旧機の時間台帳 6.37 h は Pegasus の node 時間ではないので未判定。(a) が無い fig1・fig2b・fig2c・fig8・fig8b の「不要」は暫定。fig4・fig13 を除く R2 推奨 6 図 (fig8 は fig8b に含める) を束ねると 9.52。
- 現行の A-2・A-6・B-7 の policy は 5 node を確保する (`eda92f107`・`2a9ba783f`)。fig6・fig11 の元の走は 1 node 時代だったので、5 node 形の見積りは B-7 の Elapse を当てた試算にした。
- 段 6 (Codex read-only review 1 本、20:22〜20:26 JST): NO-GO (must-fix 6・should 3・nit 1)。親が現物で裏取りし 9 件 real と裁定して直した — fig13 の値は Elapse でない、旧機の台帳を node 時間と同列に足した、fig15 は R2 の形でない、fig15 の入力は追跡下に同じ SHA-256 の逐語写しがある、「全 20 図で描き直し」は表と矛盾、fig1 の再生と G の費用の混同、fig4 の sort_best の選定履歴、fig8 の driver 記録、fig2c の WAL 時刻差。焦点再レビュー 1 巡目 (20:28〜20:31) は NO-GO (closed 9 / partial 1、新規 4 件) で、walltime 上限から確認「要」を導いた点を未判定に直し、cohort 2 の Elapse・6 図の量化・受入を含まない旨を直した。2 巡目 (20:33〜20:35) は NO-GO (14 件すべて closed、新規 must-fix 1 = Elapse の無い図の「不要」を代理値から確定している) で、fig1・fig2b・fig2c・fig8・fig8b の確認を「暫定で不要、投入形を決めて Elapse で確定」に直した。DW-O16 の上限 3 巡に達したので、この修正は親が置換の件数と grep で閉じた (insight §7)。
- 調査子 (Claude Explore、sonnet) 3 本の報告のうち「fig2c は検証なし」は WAL の `verify_done` (各 variant) で親が訂正した。所要の値は親が結果稿・job 会計・WAL で照合した (`verbatim/wal-span.log`)。
- 実装面の差分ゼロ (insight・verbatim・本 fragment のみ) なので変異 matrix は免除 (DW-S04)。受入全走の結果は land の受領証。本 wave の計算ノード使用は受入だけ。
- セッション異常: 隔離 worktree の Bash 検査が複合構文・変数展開を含む git/python 呼び出しと、heredoc と WAL path の同居を拒否したので、1 命令ずつに分け、script は Write で作った。model 未指定の Explore 起動は hook が拒否し、sonnet を明示して起動し直した。

## 次の一手差分

### 更新

- [T-2853] **P1・(1) の保全口と (2)(3)(5) の計画は済み (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクと実行手順を要するので、実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。失敗候補と否定的結果を含めて公開してよく (D2212 項 6)、provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。初段 (量・保存費の見積り、trace の保存・公開方針、再実行の 3 経路) は `output/insights/2026-09-22/t2853-repro-package-estimate/README.md`、**(2) job dir にだけあった論文根拠データの写し (repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/`、sha256 全件一致) と (3) 系列ごとの実行手順・R1 の入力一式は `output/insights/2026-09-23/t2853-repro-package-archive/README.md` で済んだ。(1) の標準評価経路の trace 保全口は D2233 で入った** (env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in、検証 1 反復の一時 dir を cleanup の前に file ごとに zstd で保全し inventory を書く。未設定なら挙動不変、保全の失敗は原本を残し評価結果を置き換えない。insight `output/insights/2026-09-23/t2849-comparison-harness-impl/README.md`)。**(5) の主要図の再実行計画は `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` で済んだ** (20 図ごとの経路と出所つきの所要。最小の経路は描き直しで node 時間 0、G が要る図は無い、図 1 本で Elapse 単価から確認が要るのは fig10、fig13・fig4 は単価が無く未判定)。残り: (1') 保全口の inventory は file ごとの sha256・bytes・行数、workload flags、genome、trace binary の sha256 までで、R1 の入力一式の残り (verifier の argv・repo commit・pin・patch・verifier module の sha256) を D2160・B-8 の runner と同じ組で残す部分は未実装。今後の論文根拠の実験 (P0・P1・P3・TPC-C) を走らせる前に、保全口の opt-in を有効にする実行経路とあわせて入れる。(4) P1 の関数単位の候補を受ける R2 の入口 (P1 の実装と同じ wave で)。(5') 計画の実行: 生成器のある 17 図の描き直し (node 時間 0)、fig1 の生成器の作成 (Codex author の別 wave)、fig15 の repo 外入力の写し、R2 は論文投稿前に投げる単位を決めて見積りを示し、2 node 時間以上ならユーザー確認後に投入する (D2212 項 4)。(6) 公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時 (目標投稿 2027-02-01、概要提出 2027-01-25)。新しく論文根拠になった job dir は、実験と並行で同じ手順 (保存先 `tools/`) で写す。
  base: fe166602e5d8e07cf5a8fa9d3190b60898218e3d444c10d735c8cbecfe3213e4
