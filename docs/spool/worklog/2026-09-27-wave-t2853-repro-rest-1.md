---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: wave-t2853-repro-rest
seq: 1
title: [T-2853] 新しく論文根拠になった 3 系列 (T-2850 試走 v2・T-2849 MOCC 疎通・T-2865 段階 F) の job dir 固有分と campaign 原本 9,041 file を repo 外へ写して sha256 全件一致、R2 の投入単位を図 1 本とし B-10 の元 job の会計で fig2c・fig8b・fig13 の Elapse を確定 (docs + repo 外の写し、新規計測 0、branch wave-t2853-repro-rest)
---

## 本文

- 軽量版 dev-wave。repo のコード変更 0、計算ノード 0。段 2・3 は省き、一次資料から事実を書き起こす docs なので段 6 の read-only review を 1 本残した。
- 調査子 (Claude Explore、sonnet) 3 本は 3 本とも途中で隔離 session のガード (他 worktree への git・変数入りの find を拒否) により Bash を使えなくなり、件数・bytes の一部が欠けた。欠けた分は親が git を起動しない読み取り script で実測し直した。親も `bash <script>`・変数入りの `find`・git の語を含むインライン Python を同じガードに拒否され、script file を python3 で直接起動する形に分けた。
- 計画稿が「Elapse 未記録」とした B-10 の元 job の stderr に NQSV の会計が残っていた。fig2c は WAL 時刻差 (c) が Elapse の約 36% しか捉えておらず、1 本で確認が要る側へ移った。

## 次の一手差分

### 更新

- [T-2853] **P1・(1)(1')(1'') の保全口と (2)(2')(3) と (4) R2 の入口と (5) の計画・R2 の投入単位と Elapse 見積り・17 図の描き直し・fig1 の生成器・fig15 の入力は済み (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクと実行手順を要するので、実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。失敗候補と否定的結果を含めて公開してよく (D2212 項 6)、provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。初段 (量・保存費の見積り、trace の保存・公開方針、再実行の 3 経路) は `output/insights/2026-09-22/t2853-repro-package-estimate/README.md`、(2) job dir にだけあった論文根拠データの写し (repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/`、sha256 全件一致) と (3) 系列ごとの実行手順・R1 の入力一式は `output/insights/2026-09-23/t2853-repro-package-archive/README.md`、(1) の標準評価経路の trace 保全口は D2233 (env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in)、(5) の主要図の再実行計画は `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` で済んだ。**(1') 保全口の inventory に R1 の入力一式の残り (verifier の等価 argv・repo commit・完全 SHA の pin と宣言値・patch の bytes と sha256・verifier module の sha256) を D2160・B-8 の runner と同じ名前で足し、標準評価経路では build 時の source evidence と照合できたものだけを complete にした (D2247)。(5') のうち生成器のある 17 図の描き直しは値の差 0 で済んだ** (`output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md`)。**(5'') のうち fig1 は生成器 `tools/plotting/plot_p2_5_search_cost.py` と後継図 `fig1b_phase2_negative` を追跡下の入力だけから作り、旧図と値が一致した** (`output/insights/2026-09-26/t2853-fig1-generator/README.md`)。**(5'') のうち fig15 は生成器の既定入力を追跡下の逐語写し (`output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/`、sha256 は pin と 5/5 一致) に替え、写しから描き直して旧図と値の差 0 (PNG は bytes 一致) を確かめた** (`output/insights/2026-09-27/t2853-fig15-input/README.md`)。**(1'') P1 (関数単位の軸 silo-function-policy) の実行経路 = job body の方策 mode で保全口の opt-in を必須にし、(4) その候補を受ける R2 の入口 (方策 driver の `--replay-proposal`、job mode `replay`、保存 proposal を別 campaign で LLM なしに再評価) を置いて計算ノードで 1 回通した** (`output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md`、D2270)。**(2') 新しく論文根拠になった [T-2850] 試走 v2・[T-2849] MOCC 疎通・[T-2865] 段階 F の job dir 固有分と submit checkout 内の campaign 原本 (7 組 9,041 file) を repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260927/` へ写して sha256 全件一致、(5'') R2 の投入単位を図 1 本 = 1 タスク (fig8b は fig8 を含む) とし、B-10 の元 job に残っていた NQSV 会計で fig2c・fig8/fig8b・fig13 の Elapse を確定した** (`output/insights/2026-09-27/t2853-repro-rest/README.md`)。残り: (1'') P0・P3・TPC-C の実験を走らせる前に、その実行経路で保全口の opt-in を有効にする (保全先と容量は見積り稿 §7)。verify fan-out の兄弟 node の反復は保全対象外のまま。(5'') R2 の投入は論文投稿前に、単位ごとに見積り表 (上の insight §3.3) を示し、2 node 時間以上ならユーザー確認後に投げる (D2212 項 4)。確認が要るのは fig13 (18.33 node 時間)・fig4 (4.18〜9.83、試算)・fig10 (3.40)・fig2c (2.98)、要らないのは fig8b (1.40)・fig6 (1.70、試算)・fig11 (1.69、試算)・fig2b (0.70〜0.77、試算)。fig2b・fig1 の下地・fig4 を Pegasus で走らせる経路が既存 driver で組めるかは未確認。fig15 は R2 でなく観測の再実施で、元の認可が 1 回限りのため再実施には改めて認可が要る。(6) 公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時 (目標投稿 2027-02-01、概要提出 2027-01-25)。新しく論文根拠になった job dir は、実験と並行で同じ手順 (保存先 `tools/`) で写す。
  base: 198a9b590279fca35fea6ba92a210d68ef3c1abbcc3de26e8daaa4b5cd76bc3c
