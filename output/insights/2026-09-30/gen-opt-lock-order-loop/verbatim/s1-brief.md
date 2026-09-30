# 段 1 brief — md_20: 段 A の軸を探索ループへつなぐ ([T-2888]・[T-2946])

wave: dev-wave-md20-lock-order-loop / branch worktree-dev-wave-md20-lock-order-loop / 着手 main 908741c6f (開始 gate rc=0、startup-gate.log)
依頼逐語: 同 dir の md_20.txt・common-5.txt。(P1)〜(P8) は親の provisional 裁定で、攻撃対象。

## 研究前進
段 A の試し [T-2896] (文献の最適化「競合度順の施錠」を LLM が正しく合成できるかの最初の実例 = 論文の中心主張の土台) は、候補が certified を名乗れる経路が無いと始められない (D2321 項 4)。完了判定: 名前つき対照 (version_desc) が driver の関数経路で order_gate → 小モデル関門 → patched trace build → 要求つき判定器を 1 周し、certified か構造化理由が history 行に載る。

## 確定済み裁定・不変条件
- D2321: gen-opt 候補の certified = 版 2 以上・要求あり・D5 成立・D1/D2a/D2b 違反 0。要求しない既存呼び出しは版 1 と同一の結果・投影 (1 byte も変えない)。capability 経路と source snapshot への D5 束縛は driver 接続と同時に行う (= 本 wave の義務)。
- 規律 2・3・6: 照合を緩めない。検査を外した対照を作らない。反例・失敗理由は閉じた field だけで返し自由文を載せない (関門設計 §4.4)。
- 編集禁止: orchestrator/campaign/p3_s4_loop_policy.py (生成器対照 md_11 の部品、行番号 446 固定 test、DriverContract 固定)、silo_policy_contrast*・b5_*contrast*・silo_policy_{grammar,compile,ir}.py (md_17)、tools/cc_model_checker/ (md_19)、.claude/agents/auditor.md (md_22)、external/ccbench の gitlink・CCBENCH_FULL_SHA・CURRENT_PIN (md_15)。共有登録簿・inventory test は追記のみ。
- D442: verifier の core.py/dsg.py/model.py/parse.py を変えると、変更前に作った lock は land 後 E1 drift になる (想定内、md_14 と同じ)。md_11 本走は submit checkout なので無影響。

## scope (実装単位、変更面は下の実アンカー表)
- U-A 判定器の capability 経路: `verify_trace_dir_with_capability(..., require_gate_witness=False)` を keyword 既定 False で足し、True のとき D5 を build 時に捕えた source snapshot の text で評価する (disk を読まない)。snapshot に gate emitter の file (include/ycsb.hh・cc/silo/ycsb_silo.cc。transaction.cc は既に SOURCES) を要求時だけ足し、fan-out 用の serialize/deserialize も通す。pipeline `_execute_verification_repetition` まで要求を通す。
- U-B 小モデル関門 (新 module、orchestrator/campaign/ 配下): 仕様 digest ごとの結果を build 前に要求。欠落・schema 不正・digest 不一致・未完了 (complete 偽)・登録場面の欠落は拒否。反例ありは「小モデルの反例で失格」。反例は tools/cc_model_checker/schema.py の `validate_counterexample` (cc-model-counterexample/1) を通したものだけ返す。
- U-C driver (新 sibling module、例 `p3_s4_loop_lock_order.py`): `from . import p3_s4_loop_policy as P` で部品を再利用。proposal の閉じた intake (axis `silo-lock-order-policy`)、order_gate、U-B、run_campaign (要求 True)、専用 history (`lock_order_history.jsonl`) の閉じた行 (反例の閉じた field を含む)、coder 入力の出力 (`--emit-coder-input`)。inventory test (namespace discovery・certified-writer inventory・build authority sites・plain runner allowlist・duration ledger) は追記。
- U-D 生死確認 (repo 外の起動器、Codex author): U1 bundle dcb9a41f3 + Silo 修正 patch + 骨格 patch (親の実測: git apply で fuzz なし・offset のみ、U1+修正の上に当たる) の trace build、名前つき対照を driver の関数で通す。2 node 時間未満 (1 条件 ~2 分の実測単価)。

## provisional 裁定 (攻撃対象)
- (P1) 要求の出所: driver が明示で True を渡し、さらに pipeline は genome の SILO_ORDER_VARIANT≠0 なら要求を強制する (渡し忘れを fail-closed にする)。stock 対照 (flag 0) は要求しない (pin C の stock trace は gate file を持たない)。
- (P2) 小モデル結果の schema は消費側のこの wave が定義する (md_19 未着手、branch・作業跡 0 件を親が実測)。名前は `cc-model-result/1`、反例は既存 schema を入れ子にする。md_19 がこれに合わせる。
- (P3) 期待する仕様 digest は結果 file 自身から取らない (自己申告は恒真)。軸の定数 (axis module かその隣の登録) に置き、md_19 着地前は未登録 = 全候補拒否 (fail-closed)。test は fixture digest を注入。
- (P4) 軸の仕様は全順列を覆う 1 つ (段 A 候補 §5.1) なので、digest は軸単位で 1 つ。候補ごとのモデルは作らない。
- (P5) LLM coder の新 role (agents md・manifest・adapter・codex_roles/policy.py の axis 固定・projection_guard の contract) と coder 接続仕様 md は scope 外、後続 item。driver の intake は将来の role が出す閉じた proposal schema を受ける形にする。
- (P6) 「並べ替えを使った取引の数」の計数 build は scope 外 ([T-2896] の前提として残す)。
- (P7) D5 の束縛先を disk から snapshot に替えることは判定の意味を変えない (MEANING_VERSION は 2 のまま)。
- (P8) pin C のままでは pipeline 経由の 1 周は通らない (source_digest.ALLOWLIST に ycsb.hh が無い、PIN=C)。生死確認は起動器方式で、pipeline 経路は test で担保し、certified の主張は pin 前進 (md_15) と md_19 の後に取り直す。生死確認では小モデル結果に fixture を使い、fixture であることを結果に刻む (production の digest 登録は未登録のまま)。

## 実アンカー (調査子の地図、親が一部を実測)
- oc/silo_lock_order_gate.py:26 order_gate / axis_silo_lock_order.py:4-16 / patches/silo-lock-order-variant.patch / silo_lock_order_hand/version_desc.cpp
- oc/p3_s4_loop_policy.py: load_proposal_file:128, policy_gate:233, _append_history:272, _result_history:287, make_policy_coder_input:340, run_one_iteration:478 (applied:477, run_campaign:493), drive_iteration:543, main:905。606-900 は生成器対照 (不可侵)
- orchestrator/verifier/core.py:43-73 _gate_d5, :259 verify_trace_dir(require_gate_witness, _proof_source_snapshot), :462 _bound_proof_source_snapshot, :616/:654 capability 版 / model.py:121 compiled_protocol_source_texts, :186 CompiledProtocolSourceSnapshot / source_digest.py:97 ALLOWLIST, :129/:153 serialize
- oc/pipeline.py:626-686 _execute_verification_repetition, 2264・2341 呼出, 887-890 fan-out serialize, 3068 evaluate
- tools/cc_model_checker/schema.py:12-47 (Counterexample)
- inventory: ot/test_p3_exploration_namespace.py (discovery 名 tuple・DriverContract), ot/test_campaign.py:4937/5509 (certified writer inventory), ot/test_p3_build_authority_cli.py:76, ot/test_official_perf_closure.py, ot/test_plain_runner_coverage.py

## 受入・実測環境
焦点走・受入は計算ノード (tools/run_tests.py --force-dispatch、dev_wave_wait acceptance)。生死確認は tools/pegasus/dispatch_compute.py --task generic で 1 job (所在 = worklog、機体固有 = runbook)。

## 分割方針
段 5 は所有素集合 2 単位: 単位 1 = U-A (orchestrator/verifier/・source_digest.py・pipeline.py の verify 経路と各 test)、単位 2 = U-B+U-C (新 module 2 本と新 test、inventory test 追記)。U-C は U-A の新 keyword に依存 → 単位 2 は keyword を仕様として先に固定して並列。U-D の起動器は段 6 の後に別 author 子 (job dir)。
