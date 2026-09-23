# [T-2854] 残り (1) 単位 5 — v3 の構造化出力を CLI・pipeline・受領証 digest へ配線し、pipeline の trace allowlist を tpcc + v3 + 57:43 へ広げる — 段 1 brief (親)

wave: dev-wave-t2854-unit5-v3-wiring / branch worktree-t2854-unit5-v3-wiring / 起点 local main 65fd1422f (開始 gate fresh rc=0、2026-09-23 19:59 JST)
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring
job dir: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring

## 研究前進
D2212 項 2 (TPC-C 段 1 は論文の必須経路) と D2228 (TPC-C 転移の事前登録) が前提にする「合成候補の TPC-C run を pipeline の正しさゲートで認定する」経路。
現状、verifier の公開 API は実 TPC-C v3 trace を certified にできる (D2232) が、pipeline の `_run_trace` は `ycsb_` 以外の binary を trace 前に拒否し
(pipeline.py:435-437)、CLI・pipeline の診断・受領証 digest は旧 `result_to_dict` (report.py、凍結) を使うので v3 の表・取引種別・存在詳細が落ちる
(cli.py:90、pipeline.py:656、core.py:284)。完了判定: (a) pipeline が tpcc + v3 + 57:43 の run を通し、実 trace (単位 1・2 の B0、silo 36,156 取引) と
その stdout の commit 計数で certified に届く (親の repo 外 probe)、(b) v2 の tpcc trace・57:43 でない flag・witness 不一致は reject、(c) CLI JSON・
pipeline 診断・受領証 digest の射影に v3 の表・取引種別・存在詳細が載り、v2 では bytes 不変、(d) §6.1 の段 1 例が試験で揃う、(e) 事前登録の変異が全部 kill。

## scope (本題だけ)
- 変更面 (予定): orchestrator/verifier/core.py、orchestrator/verifier/cli.py、orchestrator/campaign/pipeline.py、既存 test file
  (orchestrator/tests/test_verifier.py、test_campaign.py、必要なら test_t1286_commit_receipt.py)。
- scope 外: 単位 11 (pin 前進)、CCBench の編集、buildcache / campaign lock / workload 登録など tpcc を production で build・選択する経路
  (buildcache は常に `ycsb_<protocol>.exe` を作る: buildcache.py:1960 ほか。設計 §7.1 の単位 5 に含まれない)、段 2 (S/Q・Delivery)、
  si、report.py の編集、reflux_result_evidence.py / silo_ladder_rung1.py / critic digest の旧 result_to_dict 利用 (YCSB 専用経路)、
  新しい gate・検査・台帳・一般化。[T-156] の再評価は段 7 の記録だけ (実装しない)。

## 確定済みユーザー裁定・前提 (実測)
- D2224 項 3: v3 の構造化出力は `core.result_to_dict_v3` に置き report.py は不変。項 4: TPC-C を認定に使う単位 (allowlist 拡張) は存在履歴の検査が前提 → D2232 で充足。
- D2232: 存在違反は `read-unborn-genesis` ほか 5 種、`Integrity.existence_violation_details` は v3 のとき list、v2 では None。
- 設計 §3.5: allowlist は v3・表識別・計数修正が揃った tpcc binary に限る。57:43 = OrderStatus / Delivery / StockLevel を 0%。
- 実測 (単位 1・2 の B0、compute-2/B0-tpcc-run.json): argv = `tpcc_silo.exe -thread_num=2 -extime=1 -tpcc_num_wh=1 -tpcc_perc_payment=43
  -tpcc_perc_order_status=0 -tpcc_perc_delivery=0 -tpcc_perc_stock_level=0 -clocks_per_us=2100`。stdout に `commit_counts_:\t36156` と
  `batch_commit_counts_:\t0` (YCSB と同じ書式)、trace の C 行 36,156 = 計数。C 行は 10 token、tx_type は 1 (19,751) と 2 (16,405) だけ。
- CCBench の既定値 (tpcc_common.hh:6-12): payment 43、order_status 4、delivery 4、stock_level 4。3 つを明示的に 0 にしないと 57:43 にならない。
- 現 pin e9e477ca には v3 emitter が無い。単位 1・2 の branch `izanagi-tpcc-v3-trace` (C2 `a6f2c741`) は人間が push 済みだが pin 候補ではない
  (/rulings 第 33 回 項 1、inbox 2026-09-23 19:53)。現 pin の tpcc binary は v2 を出し、計数修正も無い。

## 不変条件
1. v2 (YCSB) の CLI JSON・pipeline 診断・受領証 digest (`_result_sha256`) の bytes、`ycsb_` の受理、他 binary の拒否は不変。既存試験の期待値を変えない。
2. report.py と orchestrator/verifier/__init__.py は編集しない (前者は D295 の凍結、後者は fixture campaign.lock が現行 sha256 を持つ)。verifier に新 module を足さない。
3. 新しい test file・fixture dir を足さない。受領証 digest の domain 文字列の改訂は段 3 の攻撃結果で裁定する。
4. 規律 2: tpcc の run が certified になるのは v3・57:43・witness 一致・存在違反 0・X/P 充足がそろうときだけ。どれかが欠ければ reject。
5. T-2797 / T-2850 の発効束が束縛する commit は動かさない (束は効力 commit の固定 checkout で走る。本 wave は main に commit を足すだけ)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 配線: cli.py の `--json`、pipeline.py:656 の診断、core.py:284 の受領証射影を `result_to_dict_v3` へ切り替える。v2 では同じ dict を返す。
  受領証射影は framing / permutation の詳細を pop している。存在詳細は依頼どおり digest に入れる (pop しない)。domain は v1 のまま。
- (P2) allowlist: `_run_trace` は basename が `tpcc_` で、flags に payment=43・order_status=0・delivery=0・stock_level=0 が文字列で正確にあるときだけ
  受理する。他の flag は制限しない。それ以外の tpcc は既存の unsupported-workload で拒否。
- (P3) v3 の要求: tpcc の run は verifier の結果が v3 であることを要求し、v2 なら reject。判定の信号は verifier が既に持つ値から取り、trace を再 parse しない。
- (P4) witness: 既存の「stdout の計数 = C 行数」の照合をそのまま tpcc に適用。§6.1 の witness (b) 末尾 C frame の欠落・(c) 最大 txid の欠落・
  (d) thread file 丸ごとの欠落を tpcc 名の試験で示す。(a) (commit 直後の quit) は CCBench 側 (単位 1・2 で確認済み) で repo 試験にしない。
- (P5) §6.1 段 1 の例は既存試験 (test_verifier.py:3475〜4009) に対応づけ、不足分だけ合成 fixture で足す。「genesis の誤用」は存在検査の
  `read-unborn-genesis` に帰属させる。si の行は対象外。実 CC での lost update (broken-silo-norw-validation.patch を TPC-C で) は、
  v3 branch の bundle と patch で計算ノード 1 走 (0.3 node 時間以内の見込み) の証拠として取るか、合成 fixture に留めるかを段 3 で攻撃させる。

## 成果物
production 差分 + 試験、親の実 trace probe、変異 matrix、insight README、fragment (worklog / decisions)、[T-156] の再評価記録。

## 並列分割
author 2 本の予定: A = verifier 側 (core.py・cli.py・test_verifier.py、受領証試験)、B = pipeline 側 (pipeline.py・test_campaign.py)。
所有 path は素集合。段 2 plan で依存が出れば 1 本に寄せる。
