# [T-2797] B-5 生成器対照の発効束 (draft) — 事前登録 §12 の採取、本走の投入経路の最小実装、rep 1 と N1 の確認、倍率 k と総 wall 倍率の再提示 (2026-09-22)

D2200 項 1 の段階認可のうち、残っていた AI 手番「発効束の完成」を行った。依頼の逐語は `verbatim/request.md`。発効 commit・校正・本走は承認後で、本 wave は投げていない。
束の本体は `bundle/b5-effective-bundle.draft.json` (status `draft`) と本 README の表である。設計判断は本 wave の decisions fragment (題「B-5 本走の投入経路と発効束の draft …」、land の fold で D 番号が付く)。

## 0. この wave が主張すること・しないこと

- **主張する:** 事前登録 §12 の全項目について、値・hash・出所、または「文書固定 / 実走後にしか存在しない」の区別を `bundle/` に固定した。束が hash で束縛する本走の投入経路
  (driver の registered 出力、job body の受け渡し、launcher の schedule と stage 投入、LLM arm の prompt 生成器と model 記録器) を repo に実装し、焦点走で緑を得た (§12)。
  (b) rep 1 高値は登録した感度基準で session 定義の変更を要求しない。(c) N1 はコードを変えずに記録する。
- **主張しない:** 本走の認可・発効 (ユーザーの承認後)。Tier0 の実 build での生死確認 (校正 job で行う)。実走の prompt と観測 model ID (実走後にしか存在しない)。
  費用の見積りは実測・換算・試算を分けた見込みで、上限の保証ではない。rep 1 の結論は write-heavy 試走の範囲の感度分析で、全 workload で warm-up が不要だという証明ではない。
  **規律 2 は緩めていない** (verify legacy 1 + 動作点 trace 5、anomaly 即 reject、Tier0 通過は certified でない)。

## 1. 1 行再提示 (ユーザー裁定)

> **B-5 事前登録 v1 (raw sha256 `66cc3911…9afd669`) を、発効束 `output/insights/2026-09-22/t2797-effect-bundle/bundle/b5-effective-bundle.draft.json` (対象 = 本 wave の land commit、cohort `b5-registered-v1`、LLM は親 session を `claude --model claude-opus-5` と専用 settings で起動して `claude-opus-5` に固定、schedule = 逆順組の 3 block × 3 stage・同時 LLM 系列 4) で発効し、倍率 k = 3 (W = 63,777 s、W_stock = 16,341 s)、総 wall 上限 = 試走の job Elapse 総和 61,261 s の 40 倍 (2,450,440 s ≈ 680.7 h)、D39 決定 2 の改訂 (B = 10 / A = 30、3,600 s の系列上限と収束・逆方向枯渇停止の不適用) の下で、校正 job (Tier0 の live 確認) → 本走 117 job の投入を認可する — 承認なら「承認」の 1 語で足りる。**

承認時に確認する事項 (事前登録 §12 の 7 項) の本束での答えは §11。

## 2. 依頼の前提を覆した事実と、段 3 の訂正

依頼は「残りは (a) 採取・(b)・(c) の 3 つ」としていたが、段 1 の実測で本走を投入する経路が試走専用のままだと分かった (段 4 で scope を再裁定、`verbatim/s4-adjudication.md` D-1)。

- driver は header に試走の cohort (`t2797-beta-v1`) と `purpose: "pilot"` を固定していた。report は registered 判定を実装済みだが、本走の台帳を registered として作れなかった。
- launcher は試走 4 job の形 (write-heavy・系列 1・block 1、walltime 8h / 3h) しか受けなかった。D2198 は「108 系列 launcher」を試走に不要として見送り、D2216 が発効束の段へ送っていた。
- LLM arm の prompt 生成器は repo 外の試走専用 script (`llm_round.py`、sha256 8b29d95c…) で、「write-heavy 系列 1」「試走」の文言と試走 worktree の絶対 path を埋め込んでいた。知識射影も write-heavy の動作点表だけだった。
- role 子 3 本は alias (`model: opus`) で起動していた。Claude Code の公式 docs では alias の解決先は「時間とともに更新される」ので、alias のままでは事前登録 §4.1「可変 alias のまま発効させない」を満たさない。
- **訂正 (段 3):** brief は「read-heavy の検査費で試走基準の walltime を大きく超えうる」としたが、引用した B-8 の検査秒 (balanced 約 220 s、read-heavy 約 496 s) は extime 10 秒の trace で、B-5 の 3 秒 trace へ直接は使えない。換算後の見込みは §10。

## 3. 置いたもの

| 所在 | 内容 |
|---|---|
| `orchestrator/campaign/b5_generator_contrast.py` | `--purpose {pilot,registered}` (既定 pilot)。registered は cohort `b5-registered-v1` と limits 第 2 文だけが変わる。pilot の header は不変 |
| `tools/pegasus/p3_s4_loop_pegasus.sh` | `IZANAGI_S4_B5_PURPOSE` (任意、pilot / registered 以外は拒否)、registered のときだけ driver へ `--purpose registered` |
| `tools/pegasus/b5_contrast_launch.py` | `registered-schedule` (§6 の配置を JSON で出す純関数) と `registered` (block・stage 指定の dry-run / submit、job ごとの submit-tree、walltime = D2217 の式)。pilot 経路は不変 |
| `tools/b5_llm_round.py` | 試走版の一般化 (`context` / `inputs` / `coder` / `proposal` / `reject` / `critic`) と `record-models` (会話記録の model ID の記録器、拒否 gate ではない) |
| 各 test (`test_b5_contrast_launch.py`・`test_b5_generator_contrast.py`・`test_p3_s4_loop_job_contract.py`・`test_ccbench_spawn_sites.py`・新規 `test_b5_llm_round.py`) | 事前登録した変異 MA1〜MA16・MB1〜MB8 を検出する node (§12) |
| `bundle/` | 束の draft JSON、schedule、sweep 全順序、random 値表と重み material、知識 manifest の写し、workload 別知識射影 3 file、親指示 template、親 settings、費用模型の出力 |
| `rep1/` | (b) の計算の入力表と session ごとの指標 |
| `verbatim/` | 依頼・brief・段 2〜6 の codex 入出力・段 4 裁定 |

## 4. 事前登録 §12 の対応表

| §12 の項目 | 本束の値・所在 | 状態 |
|---|---|---|
| 本走認可の日付・D 番号・承認対象の commit | 承認後の発効 commit で `effective` 節に書く。承認対象 = 本 wave の land commit と本束 | 承認待ち |
| 事前登録 raw bytes の SHA-256 と保存先 | `66cc3911e0e4026de7ff6d33d419c362d40130944ec1f30be1ec2f2ac9afd669` (51,385 B、Git blob `58c4eacb…`、最終変更 commit `c6e45385…`)。保存先は repository 履歴の同 path | 固定 |
| repository・CCBench・文法・環境・toolchain の版 | 子が使う CCBench pin `511c9538…` (gitlink `e9e477ca…` とは別)、文法 module sha256 `d013131d…`、環境契約 `env_contract.lookup('pegasus')` = contract `e576e9cd…`・較正 record `calibration-753f535a…`・clocks 2100・numactl なし。toolchain は試走の計算ノードで観測した gcc / g++ 11.4.0 (Ubuntu 11.4.0-1ubuntu1~22.04.3)、cmake 3.22.1、python 3.10 (sha256 `d6bca2b8…`) を本走の要求値とする | 固定。本走 job ごとの toolchain は prebuild receipt に記録され、要求値と異なる job は発効束への不適合としてその系列 (または block-stock) を集計時に欠測扱いにし救済しない (手順であって機械 gate ではない) |
| 実行 script・生成器・解析規則の bytes と hash | draft JSON の `files_sha256` (31 file: driver・report・子・pipeline・loop・文法・格子・動作点・環境契約・射影・知識 manifest 解決・bench の CV 判定・verifier 9 file・launcher・job body・LLM 巡 tool・role 定義 3 file・事前登録・較正 record) | 固定 (内容 hash で束縛) |
| LLM の exact ID と推論・生成設定 | 予定 exact ID `claude-opus-5`。親は `claude --model claude-opus-5 --settings bundle/b5-parent-settings.json` (alias `opus` → `claude-opus-5` の対応変数と親 effort xhigh)、role は定義どおり effort high。生成 parameter は §5 | 固定 (観測 ID は実走時に巡ごとに記録) |
| 全役割の prompt | template は `tools/b5_llm_round.py` 内 (sha256 は `files_sha256`)。親への指示は `bundle/b5-llm-parent-template.md`。生成済み prompt は各系列の開始 stock 値を含むので実走前には存在しない (tool が巡ごとに sha256 を出力・保存) | template 固定 / 生成物は実走後 |
| 知識射影 | 知識 manifest `bundle/knowledge-manifest-wal-only.json` (digest `396cd559…`)、planner 射影の照合先 `output/insights/2026-09-18/t2746-k2-loop-round2/materials/knowledge-input.json` (sha256 `05f2b267…`)、workload 別 context 3 file (§5) | 固定 |
| 入力 schema・初回入力・欠測時の表現 | draft JSON の `input_schema` / `initial_input` / `missing_values`。初回は whiteboard 空・診断 key なし・current_perf = 同 job の開始 stock、欠測は null と「null (欠測)」で 0 にしない | 固定 |
| random の整数重み表とその hash、seed preimage | 重み sha256 `876b1b47…`、M = 2350927428781729131458637903205781083070、preimage `b5-generator-contrast-v1\|random\|<w>\|<r>\|<a>\|<c>`、`bundle/weights-material.json`、36 系列 × 30 機会の値表 `bundle/random-values.json` (棄却 0 回) | 固定 (試走の凍結値と一致) |
| sweep の系列別全順序 | `bundle/sweep-orders.json` (36 系列 × 28 点、write-heavy 系列 1 は試走と一致) | 固定 |
| 108 系列の schedule | `bundle/registered-schedule.json` (§6) | 固定 |
| 各評価・score・stock session の識別子 | slot key `b5-generator-contrast-v1\|b5-registered-v1\|<arm>\|<workload>\|<series>\|<kind>\|<n>\|attempt-<t>` | 固定 (規則) |
| correctness / Tier0 / bench の exact 引数と失敗時処理 | §7 と draft JSON の `execution_contract` | 固定 |
| job walltime とその根拠 | D2217 の式、推奨 k = 3 (§10) | 推奨 / 承認待ち |
| D39 決定 2 の改訂と総実行 wall 上限への明示承認 | B = 10 / A = 30、3,600 s 上限と収束・逆方向枯渇停止の不適用 (§3.4)。総 wall 上限の推奨 = 61,261 s × 40 (§10) | 承認待ち |
| 既知結果台帳の差分と §10 の部品の所在 | §11 の差分表。§10 の部品の所在は draft JSON の `implementation.section10_parts` | 固定 |

## 5. 役割別の推論・生成設定

| 役割 | 起動 | model の指定 | 予定 exact ID | effort | tool | 生成 parameter |
|---|---|---|---|---|---|---|
| 親 (1 系列 1 session) | `claude --model claude-opus-5 --settings bundle/b5-parent-settings.json` | `--model` の完全 ID | `claude-opus-5` | xhigh (settings) | 通常の Claude Code | 指定口なし・観測不能 (client 既定) |
| planner-v4 | 親の Agent 呼出し (`model` 引数なし) | 定義 `model: opus` → settings の `ANTHROPIC_DEFAULT_OPUS_MODEL` で `claude-opus-5` | `claude-opus-5` | high (定義) | なし | 同上 |
| coder-v4-autonomous-k2 | 同上 | 同上 | `claude-opus-5` | high | なし | 同上 |
| critic | 同上 | 同上 | `claude-opus-5` | high | Read / Grep / Glob / Bash | 同上 |

- 公式 docs (Claude Code の sub-agents / model-config) で確かめた解決順は「起動時の `model` 引数 > 定義の `model:` > `CLAUDE_CODE_SUBAGENT_MODEL` > 親の model」。定義の `effort:` は
  `CLAUDE_CODE_EFFORT_LEVEL` に負けるので、起動手順でこの 2 変数が未設定であることを確かめる。
- `ANTHROPIC_DEFAULT_OPUS_MODEL` は alias と完全 ID の対応を決める変数で、API キーでも従量課金への切替でもない。親 session の process にだけ入り、利用者の shell には入らない。
- role 定義 3 file の `model:` を完全 ID へ書き換える案は採らない (3 file の sha256 が `.codex/role-adapters/*.json`・`orchestrator/codex_roles/review_ledger.py`・test・図の provenance に束縛されている)。
- **観測 ID の記録:** `record-models` は巡ごとに role の会話記録 (`~/.claude/projects/<proj>/<session>/subagents/agent-<id>.jsonl` と `.meta.json`) から、assistant 発話の `message.model` の全件・
  client の版・`agentType`・`toolUseId`・両 file の raw sha256 を記録する。試走 session (`f54395e2…`) の planner-v4 も事後にこの形で `claude-opus-5` と読めた。記録は client の内部形式で、
  安定 API・暗号学的な証明・実入力の送達証明ではない。
- **不一致時の処置 (事前に登録):** role の記録のどれかで `matches_expected` が false なら、親はその原提案の proposal も reject も公開せず session を閉じ、系列は handshake の期限切れ
  (`proposal-wait-timeout`、分類不能欠測) で終わる。救済・再抽選しない。critic は「次の原提案の request が出て、その評価番号が増えたときに、還流する直前の評価の分だけ」走らせ、
  最後の評価の後は走らせない (driver は最後の評価の後に handshake を待たず score へ進むため。段 6 裁定 R2、試走も 10 評価に対し critic は 9 本)。したがって走らせた critic の不一致もこの経路で欠測になる。
  `matches_expected` の判定に client の版の形式は入れない (版は記録だけ、段 6 裁定 R1)。
- **A だけを消費する拒否 (段 6 裁定 R3):** planner / coder の出力が空・不正・検査落ちなら、親は候補を直さず呼び直さず `reject` (A 消費)。子側の前処理拒否・Tier0 不通過では評価が出ず、
  同じ評価番号の次の request が来る。どちらも critic は走らせない (親指示 template §3)。
- workload 別の知識射影は試走版の動作点表・測定手順・冒頭説明だけを差し替えた (試走版との差は label の 4 行で、`diff` の出力を `bundle/leakproof-context-pilot-vs-write-heavy.diff.txt` に置く。拡張子は実装面と判定されない形にした。workload 間の差は名前と read ratio だけ)。
  知識集合は workload で選別しない。prompt の試走版からの変更は段 4 裁定 D-3 の (1)〜(7) と、critic の入力で欠測の指標 (fitness・anomalies・median・反復数・反復列・CV・rounds・settled・abort 率・
  LLC miss 率・IPC) をすべて 0 や None でなく「null (欠測)」と書く変更 (D-3 (5) の CV を他の指標へ広げたもの、実装子 B が報告、段 6 裁定 R10) である。一覧は draft JSON の `prompt_changes_from_pilot`。
  coder への「整数リテラル」の指示は、受理文法より狭い試走の構成事実として保持する。

## 6. schedule (段 4 裁定 D-2)

逆順の組 A = {LRS, SRL}、B = {LSR, RSL}、C = {RLS, SLR} (L = llm、R = random、S = sweep-matched、左から stage 1・2・3)。workload 番号 w (write-heavy 0 / balanced 1 / read-heavy 2)、
block b (系列 4(b−1)+1〜4b) で除く組を e = (w + b − 1) mod 3 とし、残る 2 組を X・Y として block 内の 4 系列に X 第 1・Y 第 1・X 第 2・Y 第 2 の順序を割り付ける。stage s ではその block の
全 (workload, 系列) の順序の s 番目の arm を走らせ、block-stock (workload ごと 1 job、series = block) は stage 2 に置く。

親が `bundle/registered-schedule.json` (sha256 `01df7ed0…`) から独立に数え直した性質: 36 順序行・117 job (各 arm 36 + stock 9)、(block, stage) ごとの job 数 12 / 15 / 12、
LLM 系列はすべての (block, stage) で 4 本 (= p、D2216)、各 workload で 6 順序が各 2 回 (§7.1)、各 (workload, block, baseline) で LLM が先・後に 2 対ずつ、block と系列の対応に不一致 0。
段 2 の配置案 (workload・block ごとに LLM の位置が一定) は相談 A の指摘 (workload 内で block と LLM 位置が交絡) で差し替えた。

**手順 (runtime 検査は足さない):** 次の stage は前 stage の全 job 終了後、次の block は前 block の全 job 終了から 1 時間以上後に投入する。実開始・終了は job と台帳の時刻から記録する。
report は実行順と block 間隔を検証しない (`validation_scope` に明記済み)。暦時間は queue 待ちを除き概ね 2〜3 日 (9 stage の最長 job の和 + block 間 2 時間)。

## 7. 実行契約 (exact 値は draft JSON の `execution_contract`)

- **子の起動:** `python3 -B -m orchestrator.campaign.p3_s4_loop (--stock-control | --run-iteration <凍結 proposal>) --isolate-worktree --fetchcontent-prebuild-receipt <receipt> --calibrated-perf --perf-workload <w> --verify-performance --b5-slot <slot key> --b5-sidecar-dir <dir>` に、
  llm の候補は `--allow-coder-derived-build --knowledge-manifest <m> --coder-role coder-v4-autonomous-k2 --knowledge-classification known_result_conditioned_derivative --knowledge-de-novo-claim false`、
  random / sweep の候補は `--machine-generated-proposal` を足す (`b5_generator_contrast.slot_argv`)。
- **Tier0 (D2215):** perf build 1 本 + 固定スモーク `--thread_num=4 --ycsb_tuple_num=200 --extime=1 --ycsb_rratio=50 --ycsb_zipf_skew=0.9 --ycsb_rmw=true --ycsb_max_ope=5` (clocks・numactl は環境契約)、
  timeout 32 s、通過 = rc 0・commit > 0・throughput 有限正、不通過は A だけを消費。
- **correctness:** legacy trace 1 回 (tuple 200 / thread 4 / rr50 / skew 0.9 / rmw true / max_ope 5 / extime 1) + 動作点 trace 5 回 (動作点と同じ records・threads・rratio・skew・rmw・max_ope、extime 3)。
  どれか 1 回でも anomaly なら即 reject で bench を取らない (規律 2)。verifier は pipeline からの Python API 呼出しで、module 9 file の sha256 を束縛する。benchmark の seed は渡さない (生成器の preimage は bench の乱数制御ではない)。
- **bench:** trace-disabled の perf build、動作点で 5 rep、CV > 0.05 で静定して測り直し最大 3 round、採用は CV 最小の round、session 値は採用 round の中央値、bench lock は node-local (T-2830)。
  品質欠測 = rep 数不一致・unstable・settled 不成立。warm-up rep なし (§8)。gen_S では perf が使えず llc_miss_rate / ipc は null (critic の帰属は throughput / abort / CV に限る)。

## 8. (b) rep 1 高値の確認 (D2200 項 1 (2) 2)

**判定基準 (段 1 brief で数える前に固定、段 4 で文言を限定):** 試走 53 session で (i) rep 1 を除いた 4 rep の中央値と 5 rep の中央値の相対差が 1 つでも 1.0% (floor 3% の 1/3) 以上、
または (ii) rep 1 の有無で pipeline の CV 判定 (CV > 0.05 で静定再測、`orchestrator/calibrator/analyze.py` の `DEFAULT_NOISE_CV`) が変わる session があれば、session 定義の変更の要否を設計付きで再提示する。
1.0% は管理上の感度基準であり、超えたことを warm-up が原因だという証明とは扱わない。

**計算 (親、login の読み取り):** `rep1/rep-table.tsv` は試走台帳 `output/insights/2026-09-20/t2797-b5-contrast/ledgers/*/events/*.json` のうち kind が stock-start / evaluation-result /
score-session の event から `jq` で `bench_payload.tps` (採用 round の 5 rep) を抜いた表 (53 行、sha256 `81ec2c3f…`)。`rep1/rep1-per-session.tsv` は session ごとの
d = |median(rep2..5) / median(rep1..5) − 1|、5 rep と 4 rep の CV (標本標準偏差 / 平均)、rep 1 が最大か、rep 1 / median(rep2..5) − 1 (見出し 2 行 + 53 行、sha256 `7f2d12ce…`)。

| 集合 | session 数 | d の最大 | d ≥ 1% | CV 5% 判定の変化 | rep 1 が最大 | 全 session の round 数 |
|---|---:|---:|---:|---:|---:|---|
| 試走全体 | 53 | 0.6960% (random 探索 3、値 5) | 0 | 0 | 36 | すべて 1 |
| lock 待ちがほぼ無い LLM 7 session (評価 9・10、score 1〜5) | 7 | 0.3337% | 0 | 0 | 7 | すべて 1 |

- 5 rep の CV の最大は 3.58%、rep 1 を除いた 4 rep の CV の最大は 2.23% で、どちらも 5% を下回る。
- lock 待ちのない 7 session でも rep 1 は 7 / 7 で最大 (残り 4 rep の中央値より +0.95〜+2.41%)。**rep 1 高値は共有 lock の待ちだけでは説明できない。** 原因は特定しない。
- 較正記録の within-run 10 rep (無 backoff genome、`output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr{5,50,95}_rmw0.json`) では rep 1 / median(rep2..10) − 1 が
  rr5 +7.01% (最大)、rr50 −3.35% (最小)、rr95 +2.60% (最大) で、一様に高いわけではない。
- 段 2 plan の子と段 3 相談 A も同じ台帳から独立に集計し、最大 0.6960199%・1% 以上 0 件・CV 境界変化 0 件で一致した。

**結論:** 保存済みの試走 53 session では、登録した感度基準から session 定義の変更を要求する差は見つからなかった。**現行の 5 rep 構成 (warm-up rep なし) を維持する。**
これは write-heavy 試走の範囲の感度分析であり、balanced / read-heavy や全候補で warm-up が不要だという一般証明ではない。
D28 は 1 run 内の冒頭区間の破棄を扱い、独立な 5 run の第 1 run を除く操作とは別である。試走 insight §6.2 の「median 採用なので fitness は動かない」は不正確で、
正しくは「動くが最大 0.70%」(旧 insight は書き換えず、本節で訂正する)。

## 9. (c) 投入済み duplicate-skip の B 計上 (Tier0 insight §8 の N1)

**結論: コードは変えない。** 事前登録と D2200 項 1 (2) 4 の「重複 skip 拒否と B 消費を維持」に照らした確認結果は次のとおり。

- **通常運用では到達しない。** B-5 mode の子は投入印 (`pipeline-submitted.json`) を書いた後に `run_campaign` を呼び (`orchestrator/campaign/p3_s4_loop.py` の B-5 分岐)、
  `summary.skipped > 0` のときだけ `duplicate-skip` を返す。`run_campaign` (`orchestrator/campaign/loop.py`) が skip するのは、その layout の WAL を再生した終端済み集合 `done` に
  同じ variant がある場合だけである。slot key (cohort・arm・workload・系列・kind・番号・attempt) が campaign identity に入り、1 呼出しは 1 genome なので、fresh な layout では `done` は空である。
- **到達しうるのは前提破れだけ:** 同じ slot を同じ submit-tree で再起動する、既存 campaign を持ち込む等。いずれも事前登録 (救済・再抽選の禁止) と D2216 の運用で禁じた操作である。
- **到達した場合の帰結 (初回 attempt が投入後に skip したとき):** driver は stdout の token で `submitted=False` に戻し (`b5_generator_contrast.py` の `classify_slot`)、B を増やさず、
  `pipeline-submitted` event を書かず、`proposal-rejected` と系列終端 `unclassified-missing` (score なし) を書く。report の件数照合 (評価件数 = 終端 B) は双方が同じだけ少ないので通り、
  sidecar 回収も `proposal-rejected` を終端として扱うので投入印を拾わない。**B は 1 少なく記録され、report の invalid では検出されず、その系列は score 欠測になり、含む比較は判定不能になる。**
  優越の誤判定は起きない (欠測は比較を成立させない方向にだけ働く)。retry attempt で skip した場合は `submitted_once` により B は保持される。
- D2198 の B 消費点 (投入印の書かれた attempt で B を消費) との不一致はこの到達しない経路だけに残る既存の限界として記録し、台帳・report・gate は足さない (依頼の scope 外)。

## 10. 費用・k・総 wall 倍率 (事前登録 §3.3 / §11、D2217、D2200 項 1 (3))

**出所の区別:** 実測 = 試走・B-8・較正の記録にある値。換算 = 実測値を別条件へ比例で移した値。試算 = 仮定を置いた模型の値。いずれも上限の保証ではない。生の計算出力は `bundle/cost-model.txt`。

| 量 | 値 | 出所 |
|---|---|---|
| 試走の job Elapse 総和 | 61,261 s (17.02 h) = random 17,286 + sweep 17,269 + llm 21,259 + block-stock 5,447 | 実測 (試走 insight §6.3) |
| write-heavy の 1 session | 499〜510 s | 実測 (lock 待ちのない LLM 7 session) |
| 現行検査器の単価 | balanced 約 29.6〜30.6 µs/commit、read-heavy 約 25.0〜25.1 µs/commit | 実測 (B-8、**extime 10 秒** の trace) |
| balanced の 3 秒 trace の commit 数 | 1.58M (fixed 5 µs) 〜 4.18M (無 backoff) | 実測 (旧較正 `a2_perf_verify_cost_t48_skew0p9_rr50_rmw0.json`、当時の検査器) |
| read-heavy の 3 秒 trace の commit 数 | 5.91M〜5.99M | 換算 (B-8 の 10 秒 trace を時間比例で 3 秒へ) |
| 1 session | balanced 277〜727 s、read-heavy 817〜1,007 s | 試算 (C = 60 + 5 × (3.4 + 検査秒)、検査秒 = commit 数 × 25〜31 µs を**整数秒へ切り上げた値**。切り上げない式の値は balanced 274.5〜724.9 s、read-heavy 815.75〜1,005.45 s) |
| 親の待ち (LLM 系列) | 7,800 s (10 巡)、23,400 s (A = 30 の各機会を 780 s と仮定) | 実測 7,360 s の丸め上げ / 試算 (登録上の 1 機会の上限は 2,700 s で、この値は上限ではない) |
| job の準備 | 600 s | 試算 |

| workload | 非 LLM 系列 (16 session) | LLM 系列 | LLM 系列 (A = 30 まで) | block-stock (5 session) |
|---|---:|---:|---:|---:|
| write-heavy | 8,760 s | 16,560 s | 32,160 s | 3,150 s |
| balanced | 5,032〜12,232 s | 12,832〜20,032 s | 28,432〜35,632 s | 1,985〜4,235 s |
| read-heavy | 13,672〜16,712 s | 21,472〜24,512 s | 37,072〜40,112 s | 4,685〜5,635 s |
| read-heavy (旧単価 80 µs/commit のストレス例) | 39,912 s | 47,712 s | 63,312 s | 12,885 s |

**k (D2217 の W = ceil(21,259 × k)、W_stock = ceil(5,447 × k))。** k = 2: W 42,518 s (11:48:38)、W_stock 10,894 s (03:01:34)。k = 3: W 63,777 s (17:42:57)、W_stock 16,341 s (04:32:21)。
k = 4.06 (gen_S 上限): W 86,312 s、W_stock 22,115 s。**推奨 k = 3。** 換算の中心なら k = 2 で足りるが、k = 3 は read-heavy の LLM 系列の旧単価ストレス例と A = 30 の使い切りを重ねた
試算 (63,312 s、各機会 780 s の仮定) と、block-stock のストレス例 (12,885 s) まで覆う。同じ処理が小さい k の walltime 内に完走する場合、k を上げても実 Elapse は増えず予約が長くなるだけである
(小さい k で打ち切られていた job は、大きい k では長く走るぶん実 Elapse が増える)。walltime の不足は n や正しさ条件を下げる理由にしない (§11)。

**総 wall 倍率 (§11「試走の実測所要への倍率」、計上対象 = job Elapse の総和、親の待ちを含む)。** 分母は試走の raw job Elapse 総和 61,261 s とする (session 比例の外挿値 569 h とは混ぜない)。
本走 1,773 論理 session の見積り: 換算の低い側 360.8 h (21.2 倍)、高い側 465.9 h (27.4 倍)、高い側に A = 30 使い切りの親待ち (各機会 780 s の仮定) を重ねると 621.9 h (36.6 倍)。
**推奨倍率 40 倍 = 2,450,440 s (680.7 h)。** 高い側 + A = 30 使い切りの親待ち試算に約 1 割の余裕 (retry・品質再測定・失敗の追加費用) を見た値で、旧単価ストレス例を全 workload に当てた場合や、
各機会が 780 s を超えて 2,700 s の上限近くまで待つ場合は覆わない。
上限に達したら事前登録どおり n や正しさ条件を下げず、未完走の比較を対称に判定不能として終える。

別欄 (総 wall に含めない): 親の能動作業 36 系列 × 10 巡 × 10〜13 分 ≈ 60〜78 h (A = 30 なら最大 3 倍)。予約容量 (108 W + 9 W_stock) は k = 3 で 1,954 node 時間相当で、消費の上限ではない。

## 11. 既知結果台帳の差分と、承認時に確認する事項 (事前登録 §8 / §12)

### 11.1 本 wave で閲覧した既知結果と、それを見た後の設計選択

| 閲覧した既知材料 | 閲覧者・時点 | それを見た後に決めた設計 |
|---|---|---|
| 試走 (β) の台帳 53 session (rep 別 tps・score・abort 率)、試走 insight §6 / §8 | 親 (Claude Opus 5、本 wave の manager) 2026-09-22 08:5x〜09:2x JST、段 2 plan・段 3 相談 A / B の Codex 子 09:14〜09:33 JST | rep 1 の判定 (§8、基準は数える前に固定)、5 rep 構成の維持 |
| Tier0 wave の固定スモーク実測・変異・受入 (T-2797 前段 insight) | 同上 | 変更なし (Tier0 は作り直さない) |
| B-8 本走の検査記録 (workload 別の commit 数・検査秒、extime 10 秒) | 親 08:5x JST、相談 B 09:26〜09:31 JST | 費用の換算 (§10)、推奨 k = 3・総 wall 40 倍 |
| 較正記録 (a2 の検査所要、between-run noise の within-run 10 rep) | 親 08:5x〜09:1x JST、相談 A / B | 費用の換算 (§10)、rep 1 の補足 (§8) |
| 試走 LLM arm の逐語 (prompt・role 出力・critic 診断・知識射影) | 親、段 2 plan、相談 A、実装子 B | prompt の一般化 (D-3)、知識射影の workload 別化 |

本 cohort (`b5-registered-v1`) の結果はまだ存在しない。過去の性能観測・certification・floor を新 cohort へ移植しない。既知候補と同じ値が fresh に生成されることは許す (事前登録 §8)。

### 11.2 承認時に確認する事項 (事前登録 §12 の 7 項への本束の答え)

1. **D39 決定 2 の実質改訂:** B = 10 / A = 30、3,600 s の系列上限の撤去、収束・逆方向枯渇停止の不適用 (driver の fresh layout と A / B 台帳が機械化済み、D2198)。
2. **凍結する実験構成:** model `claude-opus-5` (起動構成で固定、§5)、prompt template (`tools/b5_llm_round.py`) と親指示、知識射影 (manifest digest `396cd559…`・workload 別 context)、D2155 の還流 (診断 6 field)、
   random の分布 (重み sha256 `876b1b47…`)、28 点 sweep (系列別全順序)、n = 12 (108 系列 + block-stock 9 job)。
3. **score と失敗処理:** 事前登録 §6 / §3.3 のまま (適応 backoff stock への fallback、anomaly の横断失格、機械欠測、品質欠測、重複の fresh 評価)。Tier0 不通過は A だけを消費 (D2215)。
   model 観測の不一致は系列の欠測 (§5)。
4. **費用:** 1,773 論理 session、総 wall 上限の推奨 = 61,261 s × 40 = 2,450,440 s (680.7 h)、walltime k = 3 (§10)。縮小案は無い。
5. **未閉鎖の主張:** (d) クロスプロトコル最良、(e) 同一 variant の横断退行は本束で閉じない。
6. **本走の具体的認可:** 対象 = 本 wave の land commit と、承認に基づき本束の status と effective 節だけを変える発効 commit。校正 job (Tier0 の live 確認) と本走 117 job は発効 commit の
   固定 checkout で走らせる。列挙した hash が一致しても、それ以外の commit は承認の対象外 (段 6 裁定 R4)。
7. **D52 / D1409 との境界:** 本比較を認可しても headline の復活や「非列挙」の定義変更にしない。

## 12. 経緯 (段 2〜5 と焦点走)

- **段 2 plan (Codex、read-only、gpt-6-astra / medium、09:14〜09:25 JST):** 実装単位 A (driver・job body・launcher) と B (LLM 巡 tool) の分割、N1 の帰結の訂正 (report の invalid では検出されない)、
  B-8 の検査秒が extime 10 秒の trace であることの指摘。`verbatim/s2-plan.md`。
- **段 3 相談 (Codex 2 本、09:26〜09:33 JST):** A (正しさ・整合) は must-fix 2 (exact model の事前固定と不一致時の扱い、役割別の生成設定の採取) と should 5 (schedule の交絡と逆順組の配置、
  rep 1 の結論の限定、prompt の意味を持つ文の扱い、等価な公開順変異、既知結果差分の閲覧者欄)。B (過剰・削除) は must-fix 5 (repo 内製品化の必須性、producer 側の新しい拒否条件、N-e の過大評価、
  総 wall の分母、exact model の固定)。裁定は `verbatim/s4-adjudication.md` (14 所見の採否、D-1〜D-10、変異の事前登録 MA1〜MA16・MB1〜MB8・M0)。
- **exact model の事実確認:** Claude Code の公式 docs (sub-agents / model-config / cli-reference / setup) を subagent が逐語付きで確認した (§5 の解決順・alias の更新・対応変数・effort の優先順位)。
- **段 5 実装 (Codex author 2 本、09:45〜09:58 JST):** A は所有 8 file のうち、登録簿の launcher の説明文の更新が所有外の `test_hooks.py` の golden (説明文まで完全一致) と衝突すると報告した
  → 親は説明文の更新を patch から除いた (登録簿は不変、説明文は試走 submitter のまま)。B は「tool は subprocess を起動しない」と「既存の知識解決関数を使う」の衝突 (既存関数が内部で読み取り専用の
  git を起動する) で知識解決を止めた → 親が「tool 自身が process を起動しない」の意味と裁定し、fix B1 (12:08〜12:11 JST) で試走版と同じ手順に完成させた (不一致時は `assert` ではなく例外で停止)。
  統合 commit `d327dd30c` (実装 9 file、provenance の事前検査と全史監査 12,524 件で新規違反なし)。
- **焦点走 f1 (計算ノード、request 16446.nqsv、12:14〜12:16 JST、job Elapse 110 s):** 変更 test 5 file + consumer 4 + tools を走査するメタテスト 4 + inventory 4 群の 17 file で
  **2,732 passed / 14 skipped / 0 failed**。新設・変更した test に skip 条件は無い (skip 14 件は既存 test のもの)。
- **段 6 レビュー (Codex 2 本、read-only、12:28〜12:34 JST):** A (正しさ・整合) は NO-GO、must-fix 2 (最後の評価の後の critic の不一致が欠測にならない、A だけを消費する拒否の親手順の欠落)・
  should 2 (toolchain の要求値、prompt 変更一覧の不足)・nit 1 (費用表の丸め)。束の hash 31 件・事前登録の bytes・schedule・random / sweep・rep 1・N1 の数値はすべて一致と確認。
  B (過剰・削除) は NO-GO、must-fix 4 (model 一致判定への client の版の混入、最後の critic、承認対象を後の main へ広げる一文、launcher 用の新設起動目録 test)・should 2・nit 1。
  裁定は `verbatim/s6-adjudication.md` (R1〜R11 をすべて採用)。実装の fix は Codex 2 本 (A1: 起動目録 test を base へ戻し schedule 検査を整理、B2: 版の異常を別欄へ、12:37〜12:39 JST)、
  fix commit `d307eb541`。文書の fix (親指示 template の critic の実行条件と A だけを消費する分岐、承認対象の限定、束の data file の hash 列挙、toolchain の要求値、費用の文言と丸め) は親。
  fix 後も知識射影 3 file と schedule の出力は同じ bytes。
- **親の検算:** schedule の性質 (§6)、workload 別 context の差分 (§5)、random 値・sweep 順・重み material の試走凍結値との一致、知識 manifest の写しの digest、環境契約の解決結果
  (`env_contract.lookup('pegasus')` は contract `e576e9cd…`・較正 record `753f535a…`。後の世代 `94a4b79f…` は lookup の返り値ではない)。

## 13. 一次資料

- 依頼逐語・brief・段 2〜5 の codex 入出力・段 4 裁定: `verbatim/`
- 束: `bundle/` (draft JSON、schedule、sweep 順、random 値表、重み material、知識 manifest の写し、知識射影 3 file と試走との差分、親指示 template、親 settings、費用模型の出力)
- (b) の計算: `rep1/`
- 前段: `output/insights/2026-09-20/t2797-b5-contrast/README.md` (試走)、`output/insights/2026-09-21/t2797-tier0/README.md` (Tier0)、D2198・D2199・D2200 項 1・D2215〜D2217
