# [T-2867] silo-function-policy 軸の LLM 対 非 LLM 生成器の対照 — D2258 の流用可否・事前登録の草稿・見積り (2026-09-27、計算なし)

- 位置づけ: D2259 (B-5 v2 は見送り、「なぜ LLM か」は関数単位の軸で取り直す) の後継。事前登録の草稿は `docs/silo-policy-generator-contrast-preregistration.md`
  (以下「草稿」、**未発効**)。本 insight は起草の記録で、可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- wave: branch `worktree-dev-wave-t2867-llm-contrast`、起点 local main `ad114fba0` (2026-09-27 14:4x JST に開始 gate rc=0)。docs だけの変更で、コード・テスト・`.claude/agents/`・
  `orchestrator/campaign/p3_s4_loop_policy.py`・`tools/pegasus/` (並走 [T-2865] の担当) は変えていない。計算は投入していない。
- 逐語 (`verbatim/`): 依頼 `request.md`、段 1 brief `brief.md` (同日の改訂節を含む)、段 6 のレビュー・裁定 (段 6 の後に置く)。

## 0. この文書が主張すること・しないこと

- **主張する:** D2258 の実行契約のうち、規則として継承できるものと、コードとしてそのまま使えないものを、local main `ad114fba0` の実コードで分けた (§2)。
  草稿の設計判断とその理由 (§3)、見積りの計算 (§4)、発効までに要る実装 (§5)、起草で読んだ既知結果 (§6) を記録した。
- **主張しない:** 見積りが政策の候補での実費であること (単価は B-5 の backoff 候補の実測からの換算、§4)。LLM の週上限で何週かかるか (測れていない)。
  草稿の規則が確定したこと (起草版の間は規模の択一で改めうる、草稿 §0)。

## 1. 依頼と前提の確認

- 依頼 (逐語 = `verbatim/request.md`): 関数単位の軸で LLM 対 非 LLM 生成器の対照を設計し、事前登録を起草する。同じ評価数の予算で LLM と random 等を比べる。
  まず D2258 の実行契約 (1 評価 1 job、429 の保留、LLM 親の起動器、report の v2 判定) を流用できるかを読んで確かめる。node 時間・LLM 直列時間の見積りを作る。
  計算の投入はしない。発効はユーザー確認の後。driver・job body は [T-2865] の担当で編集しない。規律 2 を緩めない。本題だけ。
- 前提の実測: 段階 E は D2256 で着地済み (driver 495 行・coder role 2 本・runbook)。段階 F (計算ノードでの実走と job body) は [T-2865] が稼働中 (ListAgents で確認)。
  本軸の対照の事前登録は既存に無い (`docs/*preregistration*` を確認)。
- **段 1 の途中で見つけた上位の被覆:** 比較基盤 D2220 (`output/insights/2026-09-22/t2849-comparison-harness-design/README.md`) と T-2850 の試走の事前登録
  (`docs/search-repetition-trial-preregistration.md`) が、4 契約・情報構成 R0・K0 の LLM・共通の初期点・S3 を足す条件 (比較基盤 §10) を既に定めていた。
  brief の provisional 裁定のうち 2 つをこれに合わせて改めた (`verbatim/brief.md` の改訂節): 比較族を族 A (同じ IR) と族 B (空間拡張) に分け、LLM×C++ を
  族 A に入れない (比較基盤 §10)。共通の初期点 k = 2 を job 1 で測り、LLM の baseline は系列開始 stock のまま (比較基盤 §4.3)。

## 2. D2258 の流用可否 (local main `ad114fba0` の実コード)

| D2258 の契約 | 流用元 | 判定 | 根拠 (file:line) |
|---|---|---|---|
| 1 評価 1 job の系列制御 (項 1) | `orchestrator/campaign/b5_generator_contrast.py` | **規則は継承、コードはそのままでは使えない** | 評価の起動は `p3_s4_loop` の argv に固定 (`slot_argv`、:516)。候補は backoff 値 (`_genome`、:609、`validate_backoff_value`、:816・:938)。LLM の提案は K2 の閉じた schema と planner を要求 (:810・:935)。`run_series_step` (:975)・`next_series_action` (:880) はこれらを通る。`SeriesLedger` (:217) は arm も値も検査しないので呼べる候補 (比較基盤 §7 の区分と同じ) |
| 利用上限 (429) の保留 (項 2) | `tools/pegasus/b5_llm_parent.py` | **判定規則はそのまま使える** | `classify_exit` (:41) は出力 JSON の `is_error` と `api_error_status` だけを見る汎用関数。再試行の間隔 900 s (:17)。ただし親の argv は同じ session を `--resume` し (:167)、許可 tool は `tools/b5_llm_round.py` だけ (:168)、config の必須 field は系列・block・台帳 path |
| LLM 親の起動器 (項 1) | `tools/pegasus/b5_contrast_launch.py` の v2 経路 | **形は継承、コードは使えない** | `p3_s4_loop` と B-5 core を import (:29・:30)、親は B-5 の `Parent` (:31)、schedule は `registered_v2_schedule` (:414) の 24 対 |
| critic への入力の要請 (項 3) | `tools/b5_llm_round.py` の v2 の要請文 | 文言は使える | round tool 自体は `p3_s4_loop`・K2 の知識 manifest・backoff 文法を import (:19〜:28) |
| 同時検査 (項 4) | campaign 設定の `verify_performance_concurrent` (`orchestrator/campaign/loop.py:894` が読む) | 本軸は write-heavy だけで、write-heavy の同時検査は D2251 で実測済み | 政策 driver の `default_cfg` (`p3_s4_loop_policy.py:121`) の search_config にこの key が無い |
| report の v2 判定 (項 5) | `orchestrator/campaign/b5_generator_contrast_report.py` | **統計の核は呼べる** | `exact_sign_flip_p` (:48、1〜12 対)、`_holm` (:68、任意の族。6 比較だけ特別扱い)、`stock_cv_floor(v2=True)` (:90、3 × 5 session の pooled)、`pair_differences` (:103、系列 1..12)、`decide_comparison(v2=True)` (:128、block 条件なし)。台帳の読込・検証・射影 (`_load`・`_validate`・`_reconcile`・`_project`) は B-5 の schema に結合 |

政策 driver (`orchestrator/campaign/p3_s4_loop_policy.py`、D2256) 側で、対照に要るが無いもの (いずれも [T-2865] の担当範囲の file):

- 系列ごとの campaign identity。`default_cfg` (:121) の search_config は形・軸・動作点・verify 構成だけで、形ごとに 1 campaign になる。coder 入力の自系列の履歴は
  campaign の履歴 file から読むので (`make_policy_coder_input`、:272)、系列ごとに campaign を分ける口が要る。
- 停止規則の切り離し。driver は `p3_s4_loop.check_stop` に委ね、`MAX_ITER = 10`・`MAX_WALLTIME_S = 3600` (`p3_s4_loop.py:187-188`) で止める。
  preview の拒否も `--record-reject` で反復を 1 消費する (D2256 項 6)。A ≤ 30・複数 job にまたがる系列と噛み合わない。
- 機械生成 IR 候補の口。`--run-iteration` は proposal に `auditor` を要求する (:117)。D2214 項 8 は非 LLM の IR 候補の auditor 段を省く。
- stock (軸 OFF) と静的 10 µs (元の適用方法) を同じ session 契約で測る口。
- session の分類 (B-5 の slot sidecar に当たる、品質欠測・機械故障の判別)。
- 計算ノードの job body (`tools/pegasus/p3_s4_loop_pegasus.sh` は `p3_s4_loop` 固定、段階 E の insight §6)。

## 3. 草稿の設計判断 (親の裁定と理由)

| 項 | 判断 | 理由 | 退けた案 |
|---|---|---|---|
| arm | 4: LLM×C++・LLM×IR・random×IR・進化×IR | D2214 の最小 3 arm に、フィードバックを使う非 LLM (進化) を足した。random との差だけでは LLM の事前知識とフィードバックの利用を分けられず、査読の「藁人形」批判に答えられない。差分分析 P2 は進化探索を比べる手法に挙げる | 3 arm (random だけ) — 草稿 §11.3 に費用の択一として残した |
| 比較族 | 族 A (LLM×IR 対 random・進化)、族 B (LLM×C++ 対 random・進化)、各 Holm α = 0.05。LLM×C++ 対 LLM×IR は記述 | 比較基盤 §10 と設計 §5 (比較 A と B を混ぜない) | 4 比較を 1 族 (brief の初版) |
| 進化の方式 | 型付き GP の subtree 変異の (1+1)、field 追加 1/5、親は初期点を含む自系列の最良 | 比較基盤 §6.4 の候補のうち最小。初期点の方策は状態を持たないので、field を足す変異が無いと状態を使う方策へ行けない | 交叉・TPE・SMAC (比較基盤 §6.4 の他案、B = 10 では効きにくく実装が大きい) |
| random の分布 | 型付き grow 法、深さ ≤ 4、葉 1/2、定数は 0 (1/8) と B-5 の log-uniform 1..1000 の混合 | IR の文法をそのまま引く。定数は骨格の上限 1000 µs と B-5 の分布に揃えた。支持集合が IR 全体より狭いことは草稿 §2 で開示 | 任意の C++ 文字列の乱択 (オンボーディング §3-D が禁じる) |
| 初期点 | k = 2 (新骨格内の静的 5・10 µs)、B の外、endpoint 候補に含める | 比較基盤 §4.5 と設計 §5 の seed | 即 abort も含める k = 3 — 即 abort は write-heavy で thrashing 点 (段階 D) で、費用に見合う情報が無い |
| job の切り方 | job 1 = stock + 初期点 2、評価は 1 job 1 回、score job、参照 job 3 本 | D2258 項 1 の「stock と評価 1 を同 job」は同 job の対照のためで、本書では初期点が同 job の対照を担う。評価 1 を外に出すと LLM の待ちを全部 node の外へ出せ、job 1 の中の 429 の保留で stock を測り直す規則も要らない。B-5 v2 の見積りでは原提案 1 の node 上の待ちが 24 系列で 3.0〜6.1 h だった | D2258 項 1 どおり (評価 1 を job 1 に置き、LLM の原提案 1 を node 上で待つ) |
| LLM 親 | 1 原提案ごとに新 session | 系列の状態は driver が coder 入力に載せる。B-5 v1 では resume で 1 機会ごとに cache read が約 0.45 M token 増えた (write-heavy 系列で 1 機会目 2.0 M → 13 機会目 7.5 M、`output/insights/2026-09-26/t2797-b5-cost-options/README.md` §5) | 1 系列 1 session の resume (比較基盤 §3.4・D2216 の運用) |
| workload | write-heavy だけ | driver の動作点が write-heavy 固定 (`default_perf`、:137)。段階 D・小比較・再測も write-heavy | balanced を足す — 系列数が倍、balanced の政策の地形は未偵察 |
| 規模 | n = 12、B = 10、A = 30、N_eval = 5 | B-5 と同じ。n = 8 は 2 比較の Holm でも 1 敗で初段 (0.025) を通らない (等しい大きさの差で p = 9/256 ≈ 0.035) | n = 8 |

- **規律 2:** 草稿は全 arm の全候補・初期点・再計測に legacy 1 本 + 性能構成 5 本の verify、anomaly の即 reject、bench 前の検査完了、anomaly でも B を消費、
  を書いた (草稿 §3・§5.1)。同時検査は検査の本数と判定を変えない (D2251)。
- **firewall:** coder 入力は driver の出力だけ (草稿 §4.1)。段階 D の二値と射程文が LLM にだけ届くことは、driver が載せる入力なので外さず、LLM 構成の一部として開示した。

## 4. 見積りの計算

### 4.1 node 時間

一次の単価 (実測): B-5 v1 block 1 stage 1 の write-heavy の完走系列 (sweep r04) = stock 251 s + 評価 10 回 4,069 s + score 5 session 2,548 s
(`output/insights/2026-09-26/t2797-b5-cost-options/README.md` §2)。系列開始 stock は 251〜265 s。job の準備 (job Elapse と計算の和の差) は 29〜35 s。
同時検査の縮小率 write-heavy ×0.51〜0.60 は同 insight §4.2 の模型の換算 (冷却 60 s を全 session に足した値)。

| 量 | 式 | 値 |
|---|---|---:|
| 1 系列の直列の計算 | 258 (stock の中央) + 2 × 407 (初期点を評価の平均で) + 10 × 407 + 5 × 510 | 7,692 s |
| 同時検査の後 | 7,692 × 0.51 / × 0.60 | 3,923〜4,615 s |
| job の準備 | 12 job × 29 / × 35 | 348〜420 s |
| 1 系列 | | 4,271〜5,035 s (1.19〜1.40 h) |
| 48 系列 | × 48 | 57.0〜67.1 h |
| 参照 job | 3 × (5 × 258 + 5 × 510) = 11,520 s → × 0.51〜0.60 + 3 × 29〜35 | 5,962〜7,017 s (1.66〜1.95 h) |
| **推奨規模の合計** | | **58.6〜69.1 h** |
| 36 系列 (3 arm) | 42.7〜50.4 + 1.66〜1.95 | 44.4〜52.3 h |
| 40 系列 (n = 10) | 47.5〜55.9 + 1.66〜1.95 | 49.1〜57.9 h |

- 政策の候補の単価は未測定。backoff の候補と trace の量 (commit 数) が違いうる。段階 D の偵察 job (2 方策 + 対照 1、verify は性能構成 1 本) は 428〜564 s、
  小比較の job (6 方策) は平均 772 s (`output/insights/2026-09-23/t2865-silo-policy-known-best-compare/README.md` §0) で、経路が違うので単価には使っていない。
- 契約上限 (例): walltime を job 1 = 1 h・評価 job = 0.5 h・score job = 1.5 h・参照 job = 1.5 h とすると 48 × 7.5 + 3 × 1.5 = 364.5 node 時間。

### 4.2 LLM の直列時間と暦

- 1 機会の待ち (実測): B-5 v1 の 22 機会 (採用と却下、429 の時間切れを除く) で 255〜1,021 s、平均 599 s、中央値 473 s (同 insight §2)。
- 直列: 240 機会 × 599 s = 39.9 h、720 × 599 = 119.8 h。両端 240 × 255 = 17.0 h、720 × 1,021 = 204.2 h。同時 4 親の理想の下限はその 1/4。
- 週上限 (試算): B-5 v1 は 22 機会で週上限に達し、429 までの使用量は出力 1.14 M token・cache read 114 M token (同 insight §5)。1 原提案ごとの新 session で
  1 機会の cache read を 1 機会目の 2.0 M と置き、114 M を週の枠と置くと 57 機会 / 週で、240〜720 機会は 4.2〜12.6 週。枠は他 session と共有で、token に
  比例する保証も無いので、上下限ではない。
- 本書の比較でも LLM の直列時間が律速になりうる。D2219 項 6 の再提示条件は T-2850 の本比較を名指すので、草稿は条件を広げず事実だけを発効の提示に添えるとした (草稿 §14)。

## 5. 発効までに要る実装 (後続の wave、本 wave では実装しない)

いずれも Codex author が書き、新しい gate・検査・台帳は足さない。1〜3 は [T-2865] の担当 file に当たる。

1. 政策 driver: 系列ごとの campaign identity、停止規則の切り離し、機械生成 IR 候補の口 (auditor なし)、stock と静的 10 µs の口、session の分類、
   同時検査の key (§2 の後段)。
2. 計算ノードの job body と投入許可 (`tools/pegasus/`)。
3. 段階 F の生死確認 (実 LLM の 1 iteration を C++ 形・IR 形で、機械生成 IR の 1 評価) と job Elapse の実測。草稿 §11 の換算を置き換える。
4. 生成器: G_rand と (1+1) 進化 (草稿 §4.4・§4.5)。固定入力での値の照合試験を持つ。
5. 系列制御と起動器: D2258 の形 (1 評価 1 job、step 照合、途中死で停止、単一 process lock) を政策 driver の上に。`SeriesLedger` と 429 の判定関数は呼べる。
6. LLM の round tool と親の指示文: driver の `--emit-coder-input` / `--preview-diff` / `--record-reject` と coder・auditor・critic の呼出しを 1 機会にまとめる。
7. report: §2 の統計の核を import し、族 A・B の Holm と草稿 §7.4 の判定順を当てる。

計算: 上の実装に伴う開発の検査 (受入・焦点走・変異) と生死確認を含め、1 タスクの job 合計が 2 node 時間以上になるなら、見積りを示してユーザー確認後に投入する (D2212 項 4)。

## 6. 起草で読んだ既知結果 (草稿 §8 の台帳の出所)

| 材料 | 読み方 |
|---|---|
| 段階 D の insight (§0〜§4、点 ID・因子・比を含む) | 一次成果物の記録を直接読んだ (`aggregate.json` の生値は読んでいない) |
| 小比較の insight (§0〜§4) | 同上 (`compare-aggregate.json` は読んでいない) |
| 再測の insight (§0〜§1) | 同上 |
| 段階 C の insight | 読んでいない。初期点の値 5・10 µs の出所は段階 D の insight §2.1 の記述を通して知った |
| B-5 v1 事前登録 (§3〜§15)、v2 事前登録 (全文)、v2 準備と費用見直しの insight | 直接読んだ |
| 比較基盤の insight (§0〜§8・§10〜§11)、T-2850 の試走の事前登録 (§0〜§3・§8.3・§9〜§12) | 直接読んだ |

- 親は段階 D・小比較・再測の点 ID と比を知った上で草稿を書いた。草稿の coder 入力は driver の出力だけで、この知識は LLM の入力へ流れない (runbook §2)。
  ただし、草稿の生成器の分布 (random・進化) と初期点の選択は、知った後の設計者の選択である (草稿 §8)。

## 7. 段 6 の経緯

(段 6 の後に追記する)
