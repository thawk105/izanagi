---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-t2867-contrast-run
seq: 1
---

## {{D:silo-policy-contrast-v1-effective}}. silo-function-policy 軸の生成器対照 (事前登録 `docs/silo-policy-generator-contrast-preregistration.md`) を 4 arm × n = 12 で発効させ、発効束の実値を固定する

**決定:**
1. **発効。** D2305 項 1 (ユーザー裁定、計算確認済み) に従い、事前登録 (以下「本書」) を推奨規模 4 arm (LLM×C++・LLM×IR・random×IR・進化×IR) × n = 12 (48 系列) で発効させる。
   本書の raw bytes の SHA-256 は `541331bd90764e0a621bc1de7a34ba0919d7f145981814a6eebc4afa7f38985f` (起草版の最終 bytes、発効に伴う本文の書き換えなし)。
   以後の訂正は本書 §0 のとおり末尾の Erratum への追記だけとする。規模は推奨どおりなので、本書 §12 の「推奨以外を選んだときの書き換え」は不要。
2. **計算確認:** D2305 項 1 (2026-09-30、換算 約 61〜70 node 時間、walltime の契約上限 183 node 時間)。本決定の前の前走 (下の 7) を足した見込みは約 64〜73 node 時間で、確認の範囲を大きく超えない。
3. **対象 commit:** 本走の全 submit checkout の HEAD は wave branch の `1da88472bc54d7d59c1c8b0430dd67bfb5776618`。
   これは local main `4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037` (本書 §10 の欠ける部品の実装 D2299 を含む) に、前走で見つかった driver の欠陥の最小修正 1 commit
   (静的 10 µs の参照 slot でも offline 供給の configure 引数を condition gate へ渡す、下の 7) を足したもの。main との差はこの 1 commit (`orchestrator/campaign/p3_s4_loop_policy.py` +10/−1 と試験) だけ。
   系列台帳は作成時の checkout の path と HEAD を束縛し、本走の途中で HEAD を変えない。
4. **発効束の実値 (本書 §12):**
   - CCBench の PIN: `axis_silo_function_policy.PIN` = `pin.CURRENT_PIN` = `6810666` (submodule `68106660686232781bca3be792a750d3e19d7a8a`、D2305 項 1 のとおり C に固定。Silo の取引内の値の修正は含まない)。
   - 動作点・引数: write-heavy の較正動作点 (`p3_s4_loop.calibrated_perf("write-heavy")`、本書 §5.2)。compiler は GNU 11.4.0 (計算ノードの job 記録)。
     correctness・bench の経路と引数は job body `tools/pegasus/p3_s4_loop_pegasus.sh` の `contrast` mode と driver の `--contrast-run-unit` (対象 commit の bytes) が決める。
     判定器の版は各候補 slot の結果の `campaign_verifier_epoch` として台帳に残り、本走の記録 insight に最初の値を写す。
   - 生成器: `orchestrator/campaign/silo_policy_contrast_generators.py` の SHA-256 `6060f13767700c5d57cc55c31ee3d0832d2c3e284fd352e4fdb79972d5d5b0a3` (本書 §4.4・§4.5 の確率・重みの実値はこの file の定数)。
     版文字列 `silo-policy-generator-contrast-v1` (cohort 名 `silo-policy-contrast-v1`)。v1 の preimage で引いた値は発効の前に誰も見ていない (前走と生死確認は試験版 `silo-policy-contrast-test-2026-09-29`)。
   - LLM: `claude -p --model claude-opus-5-5 --output-format json`、settings は空の JSON、1 原提案ごとに新しい session (resume しない)、サブスクのログインだけ (API キー・代替 provider なし)。
     親の指示文 `tools/pegasus/silo_policy_contrast_parent.md` の SHA-256 `3a9674088518b18e8e3497b53e8aabd609323068434e1b8d21f5186350f54015`。
     役割 `coder-v4-autonomous-policy` (C++ 形)・`coder-v4-autonomous-policy-ir` (IR 形)・`auditor`・`critic` はいずれも role 定義の model `opus`・effort `high`。
     駆動 loop は親を起こすとき `CLAUDE*`・`CLAUDECODE`・`AI_AGENT`・`ANTHROPIC_*` の環境変数を外す (起動した session の識別子・effort が親へ漏れないように)。
   - schedule: 組 r の 4 系列の開始順は基本順 (LLM×C++・LLM×IR・random×IR・進化×IR) を (r − 1) mod 4 だけ左へ巡回した順。組を r 順に開き、
     実行 batch b (r = 4b−3〜4b) の最初の組の前に参照 job b を開く。同時に進める系列は 16 (参照を含む)、同時に動く LLM 親は 4 (本書 §7.1 の推奨、D2216)。
   - walltime (本書 §11.0 の案): job 1 = 1,800 秒、評価 job = 900 秒、score job = 2,700 秒、参照 job = 3,600 秒。
   - 駆動 loop: repo の外の `contrast_runner.py` (SHA-256 `d12eb6cd32bdb14a22abafb47d9ac112a5e2f3f588ff3d7dafd16b44f31b12f2`、Codex author、本走 wave の段 5・6)。
     起動器 `tools/pegasus/silo_policy_contrast_launch.py` の `init`・`status`・`submit`・`generate` と親 `tools/pegasus/silo_policy_contrast_parent.py` を呼ぶだけで、台帳・driver に書かない。
     逐語は本走の記録 insight の `verbatim/` に置く。
5. **LLM の待ちと 429:** LLM の待ちは login に置き (D2258 項 1)、利用上限 (429) は親が構造化 field だけで判定して同じ原提案番号で 900 秒おきに再開する (本書 §5.5、D2258 項 2)。
6. **既知結果台帳の差分 (本書 §8):** 発効の前に親 (Claude) が見たものは、生死確認 (`output/insights/2026-09-29/t2867-silo-policy-contrast-impl/README.md` §4) の値と、
   本決定の前走 (試験版) の値 = 参照 job 2 本の stock 10 session (1.355〜1.373 M tps) と静的 10 µs 5 session (3.998〜4.028 M tps)、
   進化×IR 1 系列の job 1 (stock 1.349 M、初期点 3.860 M・3.877 M)、評価 10 回 (すべて certified・品質正常、0.864〜3.993 M)、endpoint (eval-4) の score 5 session (3.958〜3.974 M)。
   いずれも試験版の preimage・別 cohort であり、本書の標本・予測的再現に使わない。
7. **前走 (本書 §10 の未実走部品の確かめ):** D2305 項 1 が「本走の最初の単位で確かめる」とした score job・参照 job・進化×IR は、v1 の系列を始める前に試験版の cohort で確かめた。
   理由: 台帳が checkout の HEAD を束縛するので、v1 の走行中の系列で欠陥が出るとその系列に修正を当てられず欠測となり、比較が判定不能になる。
   参照 job の静的 10 µs で condition gate が config.h を見つけられない欠陥が見つかり (driver rc=1、slot は dead-job)、上の 3 の修正で直した後、2 本目の参照 job で
   10 slot すべてが certified・品質正常になった (Elapse 2,135 秒)。進化×IR は評価 10 回と score job (Elapse 1,207 秒) まで通り、系列は `b-complete` で閉じた。
   駆動 loop は前走の途中で停止・修正版での再起動を行い、走行中の job の引き継ぎと二重起動の拒否を実機で確かめた。

**理由:**
- D2305 項 1 がユーザー裁定として規模・計算・pin を決め、発効束の実値の記入と投入を AI に委ねた。本決定はその記入である。
- 前走を v1 の外に置いたのは、HEAD の束縛の下で欠陥を v1 の欠測に変えないため (D2305 項 1 の「本走の最初の単位で確かめる」の意図を、欠測を出さない側で満たした)。

**却下した選択肢:**
- v1 の最初の組の中で未実走部品を確かめる — 欠陥が出た系列は HEAD の束縛で直せず欠測になり、実際に参照 job の静的 10 µs が落ちた (前走で確認)。
- 修正を待たずに main の `4f412c67b` で本走する — 参照 job 3 本の静的 10 µs がすべて落ち、参照の系列が欠ける。
