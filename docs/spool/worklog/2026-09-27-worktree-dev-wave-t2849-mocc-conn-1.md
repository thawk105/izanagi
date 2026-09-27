---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: worktree-dev-wave-t2849-mocc-conn
seq: 1
title: [T-2849] 残り (3) 第 2 プロトコル MOCC で 5 手法 × 3 workload の疎通を走らせた。15 系列すべて b-complete、stock 比は write-heavy 0.66〜1.06・balanced 0.97〜1.20・read-heavy 0.99〜1.76 (既知最良の参照なし)。read-heavy の候補 slot 25 件中 6 件で正しさ検査が G2 を検出して reject、K0 planner の axis 名の揺れで提案 13 機会中 7 件が拒否。本投入 13.65 node 時間 (insight のみ、コード変更なし、branch worktree-dev-wave-t2849-mocc-conn)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `output/insights/2026-09-27/t2849-mocc-conn/verbatim/request.md`): [T-2849] 残り (3) MOCC での疎通 (20〜40 候補 × 3 workload)。設計判断は {{D:mocc-connectivity-run}}、記録は同 insight の README。
- 起点 = local main `6c3913bc5` (fresh worktree、開始 gate rc=0)。全 job の submit-tree もこの commit。記録の前に branch を local main `8b261bcf8` へ fast-forward した。コード変更なしのため段 2・3・5・6 (実装・変異) を省いた軽量版で、段 6 は insight の事実確認の read-only レビュー 1 本だけ。
- **ユーザーの計算確認 (D2212 項 4):** 単価実測 3 job (write-heavy 212 s・balanced 346 s・read-heavy 760 s / slot、3 件とも certified) から約 10〜14 node 時間 (中心 12.5) と示し、回答は「20 候補 × 3 workload (推奨)」。提示は 2026-09-26 22:4x JST、回答の受領は 2026-09-27 07:27 JST 以前 (正確な時刻は不明)。
- 計算の実績: 本投入 18 job 49,135 s (13.65 node 時間)、単価実測 1,416 s、止まった 1 job 31 s。見積りの上側寄りになった主因は read-heavy の候補 slot が stock より長かったこと (約 960 s vs 760 s)。
- 止まった試行: write-heavy の block 対照 31002 は walltime 30 分が harness の slot 開始条件 (残り 1,800 s 以上) を満たさず、slot 0 のまま `allocation-exhausted`。台帳を job dir へ退避して 45 分で投げ直した。
- セッションの異常: 背景 job の中で main checkout を cwd にした読み取りの Bash を打ち、session の作業 dir が main 側へ移った。書き込みは無く、`EnterWorktree` の path 指定で wave の worktree へ戻した。
- LLM 親 (llm 系列 3 本) は login の起動器で `claude -p` をサブスクのログインで起こした。LLM の週枠 429 は無し。
- 段 6 の read-only レビュー (insight と一次資料の照合) は NO-GO・must-fix 1 件: 止まった job の所要を開始〜終了の差 27 s で書いていたが、会計の Elapse は 31 s。採用して直した。should 1 件 (read-heavy の拒否の axis 名を記す) も採用。
- 工数: Codex read-only レビュー 1 本 (insight の事実確認)。Codex author は 0 (実装面の変更なし)。

## 次の一手差分

### 完了

- [T-2849] 5 手法比較基盤 (S1) と第 2 プロトコル MOCC での疎通が済み、完了条件を満たした。(1) 基盤は D2233、(2) MOCC の差し込みは D2248、(3) 疎通は {{D:mocc-connectivity-run}} と `output/insights/2026-09-27/t2849-mocc-conn/README.md`。
  疎通で見つかった read-heavy の anomaly と K0 planner の axis 名の揺れは別課題 ({{T:mocc-readheavy-anomaly-cause}}・{{T:k0-planner-axis-name}}) に分けた。
  remaining: none
  base: dbe129ce4679d7f11db8a77aafc7dc05a02323f290f0517d9ba3945e486a5762

### 新規

- {{T:mocc-readheavy-anomaly-cause}} **P1・新規 (VLDB: 正しさゲートの実例になりうる)**: MOCC の read-heavy (48 thread・100 万 record・rr95) で、固定 backoff の literal 候補の slot 25 件中 6 件に G2 (write skew、1 反復に巡回 1 件、zipf 上位の key) が出た。
  stock slot 7 件は 0。MOCC 本体の欠陥が固定 backoff の条件 (多くは stock の約 1.6 倍の throughput) で表に出たのか、literal の差し込みの影響か、verifier の誤検出かを切り分ける。材料は `output/insights/2026-09-27/t2849-mocc-conn/README.md` §4 と、保全済みの anomaly 反復の trace (repo 外 `izanagi-repro-archive/t2849-mocc-conn-20260926/main`)。
  切り分けまで論文の主張に使わない。計算が 2 node 時間以上なら実測単価で見積りを示してユーザー確認 (D2212 項 4)。
- {{T:k0-planner-axis-name}} **P1・新規 (K0 LLM 手法の比較の公平さ)**: K0 の planner が axis に `silo-backoff-magnitude` 以外の名前を返し、巡 tool (`tools/t2849_llm_round.py`) の検査で提案が拒否される。
  MOCC 疎通で 13 機会中 7 件、silo の [T-2850] smoke にも 1 件。llm 手法だけが提案機会を失い、比較で不利になる。planner の入力に axis 名を載せる・検査を緩めず planner の出力例を固定値と明示する等の択一がある。
  [T-2850] 試走の llm 系列にも同じ影響が出うるので、試走の投入前に扱いを決める。材料は同 insight §5。
