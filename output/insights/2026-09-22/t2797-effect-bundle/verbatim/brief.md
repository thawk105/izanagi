# [T-2797] 段 1 brief — B-5 生成器対照の発効束を完成させ、倍率 k と総 wall 倍率を添えて 1 行で再提示する

基準: local main `8fd2a2f5c775954d6a32cee019ac7ce276298e4d` (wave 木 HEAD と一致、開始 gate rc=0)。依頼逐語は同 dir の `request.md`。

## 研究前進
論文 §8 の B-5 (固定 backoff hole での LLM 生成器の条件付き優越 = 主経路「CC 自動合成に LLM が要るか」) の本走を、ユーザーが 1 行で承認できる状態にする。
完了判定: (i) 事前登録 §12 の全項目が「値・hash・出所」または「文書固定 / 未実装」の明示で埋まった draft 束 (JSON + 表)、(ii) その束が hash で束縛する
本走の投入経路が repo に実在し test 済み、(iii) (b) rep 1 高値と (c) N1 の結論、(iv) k と総 wall 倍率を添えた 1 行再提示。発効 commit・校正・本走は対象外。

## 確定済み裁定 (攻撃対象外)
D2200 項 1 (段階認可、AI 手番 = 発効束の完成。倍率・発効・投入は 1 行再提示でユーザー)、D2215 (Tier0)、D2216 (親運用 p = 4、2,700 s)、D2217 (W = ceil(21,259 s × k)、
W_stock = ceil(5,447 s × k)、k ≤ 4.06)、D2198 (評価経路・A/B 消費点・重複 skip 拒否)、D2199 (lock・submit-tree の運用事実)、T-2830 (node-local lock、land 済み)、
D28 (1 run 内 warmup 破棄は非対応、run 間系統誤差は floor が吸収)、D2202 (B-8 の発効束の形: draft JSON → 承認後に status だけ effective)。

## 依頼の前提を覆す新事実 (親の実測、段 4 で再裁定)
依頼は「残りは (a) 採取・(b)・(c) の 3 つ」とするが、本走を投入する経路が試走専用のままである。
- N-a driver は header に試走 cohort と purpose を固定する (`orchestrator/campaign/b5_generator_contrast.py:44` `COHORT_PILOT`、`:573` `"purpose": "pilot"`、`:583-584` limits 文)。
  report は registered 判定を実装済み (`b5_generator_contrast_report.py:193-216` は purpose 一致と `block == (series-1)//4+1` を要求、`:453-550`) だが、本走の台帳を registered として作れない。
- N-b launcher は試走 4 job の形だけを受ける (`tools/pegasus/b5_contrast_launch.py:112-129` write-heavy・series 1・block 1、`:209-215` walltime literal 8h / 3h)。D2198 は「108 系列 launcher」を見送り、D2216 が「schedule・launcher は発効束の段で扱う」と送った。
- N-c LLM arm の prompt 生成器は repo 外の試走専用 script (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/llm_round.py`、318 行、sha256 `8b29d95c7e8c97de71b92bbb2b911f09865b6c6aeb5facefffc697b866202021`)。
  「write-heavy 系列 1」「試走 (T-2797)」の文言と試走 worktree・ledger の絶対 path を埋め込む。知識射影 `output/insights/2026-09-20/t2797-b5-contrast/llm/leakproof-context-b5.md` (sha256 d72bfe20…) も write-heavy の動作点表だけを持つ。
- N-d model: role 子 3 本は alias (`.claude/agents/{planner-v4,coder-v4-autonomous-k2,critic}.md` の `model: opus` / `effort: high`)、親は `~/.claude/settings.json` の `opus[1m]` / `xhigh`、Claude Code 2.1.278。
  Claude Code は subagent の会話記録 `~/.claude/projects/<proj>/<session>/subagents/agent-<id>.jsonl` の assistant 発話ごとに API が返した exact ID (`"model":"claude-opus-5"`) を、`.meta.json` に `agentType` と `toolUseId` を残す。
  試走 session `f54395e2-5efa-42e2-adb8-5937d55183d1` の planner-v4 subagent も `claude-opus-5` だった (事後に機械で読めた)。記録は client 内部形式で安定 API ではない。
- N-e 費用: 試走は write-heavy だけ (検査が最も軽い)。現行検査器の実測 (B-8、`output/insights/2026-09-21/t2807-b8-effective/verbatim/verify-records.txt`) は balanced 720 万 commit → 約 220 s、
  read-heavy 1,970 万 commit → 約 496 s (いずれも ≈ 25〜30 µs / commit、extime は要確認)。1 session に動作点 trace 検査が 5 回あるため、read-heavy の系列 job は試走基準 21,259 s を大きく超えうる。
  W (全 arm 同一) と総 wall 倍率は workload 別に見積り直す必要がある。gen_S の上限は 86,400 s。
- N-f (b) の材料: 試走台帳の各 session に rep 別 tps (`ledgers/<arm>/events/*.json` の `bench_payload.tps`、53 session)。較正の within-run 10 rep
  (`output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr{5,50,95}_rmw0.json`、無 backoff genome) は rep 1 が rr5 で最大 (+7.0%)、rr50 で最小 (−3.4%)、rr95 で最大 (+2.6%)。
- N-g (c) の機序: B-5 mode の `p3_s4_loop` が投入印 (`pipeline-submitted.json`、`p3_s4_loop.py:2604`) の後に `duplicate-skip` を返すのは `run_campaign` が skip した場合だけ (`:2618-2621`、stock 経路は `:2355-2381` の `skipped`)。
  driver は stdout の `outcome=duplicate-skip|skipped` で `submitted=False` に戻す (`b5_generator_contrast.py:364-368`)。slot key と attempt が identity に入るので layout は fresh。

## 親の provisional 裁定 (段 3 の攻撃対象)
- (P1) scope: 本走の投入に最小限要る実装 — driver の registered 化、job body の受け渡し、launcher の registered job 生成、LLM 巡 tool の本走版 — を本 wave に入れる。
  §12 は「実行 script・生成器の bytes と hash」「§10 の欠ける部品を満たす実装の所在 (commit)」「全役割の prompt」「知識射影」を要求し、D2216 が schedule・launcher をこの段へ送ったため。
  新しい gate・検査・台帳 field・report 変更は足さない。試走経路の挙動と既存 test は不変。
- (P2) schedule: block b ∈ {1,2,3} は系列 4(b−1)+1〜4b (report の既存制約)。各 block を 3 stage に分け、stage s では block 内の全 (workload, 系列) について順序の s 番目の arm を走らせる。
  LLM の位置は pos(w, b) = ((w_idx + b − 1) mod 3) + 1 (w_idx: write-heavy 0 / balanced 1 / read-heavy 2)。(w, b) の 4 系列には L を pos に持つ 2 順序を交互に割り付ける。
  これで各 workload で 6 順序が各 2 回 (§7.1)、各 stage の LLM 系列はちょうど 4 = p (D2216) になる。block-stock 3 job は各 block の stage 1 に同時投入する。
  次の stage は前 stage の全 job 終了後、次の block は前 block の最終測定から 1 時間以上後に投入する (手順。機械検査は足さない)。
- (P3) interface: driver に `--purpose {pilot,registered}` (registered の cohort は定数 1 個、例 `b5-registered-v1`、既定は pilot のまま) を足し、job body は `IZANAGI_S4_B5_PURPOSE` を検証して渡す。
  launcher は既存 pilot 経路を変えず registered 用の入口 (schedule の決定論的生成と出力、block・stage 指定の dry-run / submit、job ごとの submit-tree、`--walltime-factor k` から W / W_stock) を足す。
- (P4) LLM 巡 tool を repo に置く (試走版の一般化: ledger root から workload・系列を読み、動作点は `calibrated_perf(workload)`、知識射影は workload 別)。exact model ID の機械記録は
  同 tool の subcommand が上記会話記録から `agentType`・`toolUseId`・`message.model` の集合・記録 file の sha256 を巡ごとに書く形にする。束は exact ID `claude-opus-5`・Claude Code の版・
  agent 定義 3 file と親設定の sha256 を固定し、alias で起動する事実と「記録は client 内部形式」の限界を併記する。
- (P5) (b) の判定基準を数える前に固定する: 試走 53 session で (i) rep 1 を除いた 4 rep の median と 5 rep の median の相対差が 1 つでも 1.0% (floor 3% の 1/3) 以上、または
  (ii) rep 1 の有無で pipeline の CV 判定 (再測定・unstable) が変わる session がある、なら warm-up 変更が要ると判定する。要るなら §5.3 の session 定義の変更なので、実装せず設計付きで再提示へ回す。
  要らなければ D28 と同じ理由の実測根拠として記録し、構成は変えない。lock 待ち ≈ 0 の LLM session 7 本 (試走 §6.3) を部分集合として別に数える。
- (P6) (c) N1: コードは変えない。到達しない理由 (slot・attempt ごとの fresh layout で `run_campaign` が skip しない) と、到達した場合の帰結 (系列は分類不能欠測、B が 1 少なく記録、
  report の B 照合が invalid を出すかどうか) を実コードで確かめて記録する。invalid が workload 全体の比較を落とすなら DW-G05 の成果物影響を 1 行で書いたうえで段 4 で再裁定する。
- (P7) k と総 wall 倍率: workload 別の 1 session 固有費を「出所列 (実測 / 換算 / 試算)」で分けて見積もり、推奨 k と総 wall 倍率を添えて提示する。read-heavy の LLM 系列が k ≤ 4.06 でも
  86,400 s に収まらない見込みなら、束の成立を妨げる事実として 1 行再提示に載せる (実装で回避しない)。
- (P8) 親 session の起動の自動化は作らない。親へ渡す指示文の template (md) を束に固定し、起動は手順として書く。
- (P9) 束の形は B-8 先例: `output/insights/2026-09-22/t2797-effect-bundle/README.md` + `verbatim/b5-effective-bundle.draft.json` (status draft)。file の hash は内容 sha256 で、
  land 後の main でも内容が同じ限り有効。事前登録本文は変えない (§0、未発効)。対象 commit は本 wave の land commit を再提示で名指す。

## 不変条件
規律 2 (verify legacy 1 + 動作点 trace 5、anomaly 即 reject、Tier0 通過は certified でない) と規律 1 (性能値は trace-disabled のみ) を変えない。random / sweep の生成器と値、
A / B 消費点、LLM_WAIT_S・SESSION_BUDGET_S、Tier0・lock・walltime 式は変えない。事前登録本文の bytes を変えない。計算ノードへの B-5 投入はしない (試走・校正・本走とも)。

## 変更面 (実アンカー)
| 所在 | 担い手 | 内容 |
|---|---|---|
| `orchestrator/campaign/b5_generator_contrast.py` `:1-5` `:43-55` `:555-586` `:857-913` | Codex 実装子 A | purpose / cohort、limits 文、CLI |
| `tools/pegasus/p3_s4_loop_pegasus.sh` `:54-86` `:648-663` | Codex 実装子 A | `IZANAGI_S4_B5_PURPOSE` の検証と受け渡し |
| `tools/pegasus/b5_contrast_launch.py` (全体、pilot 経路は不変) | Codex 実装子 A | registered schedule・stage 投入・walltime |
| `orchestrator/tests/test_b5_contrast_launch.py`、`test_b5_generator_contrast.py`、`test_p3_s4_loop_job_contract.py` | Codex 実装子 A | 上記の test |
| 新規 LLM 巡 tool (置き場は段 2 で決める) + test | Codex 実装子 B | 試走版の一般化と model 記録 |
| `output/insights/2026-09-22/t2797-effect-bundle/` (README、draft JSON、schedule・sweep 順・重み material の出力、workload 別知識射影 md、親指示 template md) | 親 | 採取と記録 |
| `docs/spool/` fragment (worklog / decisions) | 親 | 記録 |

## 受入・実測環境
焦点走・変異・受入は Pegasus 計算ノード (`tools/run_tests.py`、`tools/dev_wave_wait.py acceptance`、所在は worklog)。(b)(c) と採取は login 上の read-only 読み取り。B-5 の計算 job は投げない。

## 分割
段 2 plan 1 本 → 段 3 相談 2 本 (A: 設計と scope の攻撃、B: 統計・費用と事前登録との整合の攻撃) → 段 5 実装子 2 本 (A / B、file 所有を分ける) → 段 6 レビュー 2 本。採取・(b)・(c) は親。
