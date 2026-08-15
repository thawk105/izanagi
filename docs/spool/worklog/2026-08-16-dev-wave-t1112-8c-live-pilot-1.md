---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1112-8c-live-pilot
seq: 1
title: 8c live pilot を実機で 2 走し、transport 層の突破と numactl 契約矛盾を実測した (実走のみ、branch worktree-dev-wave-t1112-8c-live-pilot)
---

## 本文

- **本 wave はコードを一切変更していない。** [T-1097] の job script を 1 バイトも変えずに
  `qsub -v` で再投入しただけである。実装面は並行 wave (branch
  `worktree-dev-wave-t1109-admission-grammar`) が担った。起動時の重複検査で当該 wave を検出し、
  SendMessage で scope を照会して「前段 3 件は向こう、live pilot は本 wave」と分担を確定した。
- **8.5 時間 land を待ったが受入フレークで進まなかったため、ユーザー裁定で land 前の branch tip
  での先行投入へ切り替えた** (2026-08-16 07:26 JST)。判断材料は、当該 wave の受入 3 走目と 5 走目の
  red-check がいずれも `test_dev_wave_wait.py` の別ノードで `rerun_rc=0` (単独再走では緑) であり、
  変更面 2 module と無関係だったこと。投入後に前段は land 済み (D430 / D431 / F332)。
  `git diff 84e7a157 main -- orchestrator/ tools/ external/` が空であることを確認しており、
  **pilot が走った木は現 main と実装面で完全に同一**である。land 前の投入は結果の解釈を損なわない。
- **前段の positive control を第三者として独立に回した。** `is_valid_pbs_jobid` へ実測値を直接通し、
  positive 5/5 通過 (`0:911106.nqsv` `0:911104.nqsv` `0:911096.nqsv` `0:911191.nqsv` および prefix
  なしの `911106.nqsv`)、negative 15/15 拒否 (空、`0:` のみ、`:` 始まり、二重 prefix、別 prefix、
  path traversal、command injection、改行埋め込み、前後空白、非文字列など)。受理集合の拡大は
  `0:` prefix ちょうど 1 形で、規律 2 は緩んでいない。D431 の unmet member を閉じる材料になる。
- **1 走目 (Request 912783.nqsv、bnode003、`PBS_JOBID=0:912783.nqsv`) で 2 つの初到達があった。**
  (1) journal seq=1 が `transport-admission-error` ではなく `transport-admission` であり、
  前回 23 秒で死んだ壁が消えた。(2) planner が `status=valid` を返し、**計算ノードから claude CLI が
  サブスク経路で実際に動いた**。transport_receipt の `admitted_env_keys` は
  `['http_proxy','https_proxy']` のみで、従量経路の env は不在である (鉄則を満たしたままの初実証)。
- 同走の coder は `Expecting ',' delimiter: line 1 column 695 (char 694)` で invalid。生出力 694 文字
  ちょうどでエラー位置が終端だが、envelope は `stop_reason=end_turn` / `subtype=success` /
  `is_error=False` / output_tokens=692 (thinking 449) であり、**truncation ではなくモデルが閉じ括弧を
  落とした生成ミス**である。`retry=False` で 1 回で諦めている。
- **2 走目 (Request 912786.nqsv) は coder が通り、LLM 合成 → campaign 起動 → build → verify まで
  到達した** (campaign `p3-t178-ycsb-a-workload-conditioned-autonomous-29944d36`)。止めたのは
  `extra_correctness に numactl 必須の構成があるが numactl 未指定 (D36 決定4-4)` で
  `0 committed / 1 aborted`、結果として Layer-3 validation が `build_start がない` で失敗した。
  env での上書き経路は無く決定論的に再現するため、3 走目は投入せず打ち切った。
- **事前に列挙した関門の読みは実機で 1 件外れた。** 並行 wave と独立に「成功経路で初めて発火するのは
  `_assert_build_transport_admitted` / `assert_autonomous_trial_completeness` /
  `assert_campaign_layer3_chain` の 3 つ」と読んでいたが、実際に 1 走目が落ちたのは
  `_finalize_build_cell_admission` (`build cell campaign has no reports directory`) で、
  3 つのいずれでもない 4 つ目だった。`_assert_build_transport_admitted` は通過している。
  **関門の静的列挙は呼び出し元の分岐を跨ぐと漏れる**という実例である。
- 両走とも `report.json` は生成されなかった (完全性検査ではなくその手前の cell admission で落ちたため)。
  成否判定に `report.json` の実在を使う運用は正しかった。

## 次の一手差分

### 更新

- [T-1112] **P1・ユーザー裁定待ち**: 8c A/B/C live pilot の再投入。
  **2026-08-16 に実機で 2 走し、閂が 1 点に絞られた。** [T-1109]/[T-1110] の修正により
  transport admission は実機で通過し、計算ノードからの claude CLI 実行 (planner `status=valid`)、
  coder 合成、campaign 起動、build、verify 到達まで確認した。
  したがって旧本文の懸念 (b) 「計算ノード実機での D122 (2)(i)(iii)〜(viii) が未測定」は
  **実測で解消した** — proxy 2 key の実在と exact 一致、TLS override 不在、従量 env 不在は
  transport_receipt に記録されている。
  **残る閂は環境契約の矛盾 1 点である**: `env_contract.py` の pegasus 契約は `numactl=()` だが、
  S2 verify (extra_correctness) は D36 決定 4-4 で numactl を必須と要求するため、
  Pegasus では S2 verify が構造的に abort する。旧本文の懸念 (a) F97 runtime attestation
  (D143 未裁定) は今回そこまで到達していないため未測定のままである。
  **この閂の解き方は {{T:s8c-pegasus-numactl-contract-conflict}} でユーザー裁定へ返す。**
  base: e8f00ce9a08b4d346dba394521008d76ae1dcce031c09716375a6b20e90a27d3

### 新規

- {{T:s8c-pegasus-numactl-contract-conflict}} **P1・新規・ユーザー裁定待ち**:
  Pegasus で S2 verify が構造的に通らない環境契約の矛盾を解く。
  `orchestrator/campaign/env_contract.py` の pegasus 契約は `numactl=()` (launch prefix なし)、
  linux-baremetal は `("numactl","--interleave=all")`。一方 extra_correctness は
  D36 決定 4-4 により numactl を必須と要求するため、実機 campaign が
  `numactl 必須の構成があるが numactl 未指定` で abort する (2026-08-16 実測、[T-1112] 2 走目)。
  択 (a) pegasus 契約に numactl を足す — `contract_sha256` が reviewed golden と照合される
  ため golden 更新と calibration_ref 整合に人間レビューが要る。
  択 (b) pilot では extra_correctness を外す — **正しさゲートを緩める方向であり規律 2 に抵触するため
  親は推奨しない**。択 (c) launch prefix を別経路で渡す配線を新設する。
  **親の推奨は (a)** — 計測の正しさを保ったまま矛盾を解く唯一の択であり、
  D36 決定 4-4 が要求するメモリ配置は bench と verify で揃っている必要があるため。
  受理集合ではなく実行環境契約の変更なので、golden 更新の可否をユーザー裁定へ返す。
- {{T:s8c-partial-report-lost-at-cell-admission}} **P1・新規**:
  role 出力が invalid で build cell が生まれなかったとき、`_finalize_build_cell_admission` が
  `build cell campaign has no reports directory` で `AutonomousTrialError` を投げ、
  **`report.json` が 1 バイトも書かれない**。[T-1110] が `assert_autonomous_trial_completeness` で
  閉じたのと**完全に同型の型**が、その手前の cell admission に残っている
  (2026-08-16 実測、[T-1112] 1 走目)。coder が 1 回 JSON を壊しただけで診断可能な成果物が
  attempts.jsonl しか残らず、`run-finish` が指す report path は存在しないままになる。
  D431 が定めた positive control 義務づけの族の member 候補でもある。
  実装面のため Codex author が要る。
- {{T:s8c-role-json-parse-no-retry}} **P2・新規**:
  role 応答の JSON parse 失敗に retry が無い (`retry=False`)。2026-08-16 の [T-1112] 1 走目では
  coder が `stop_reason=end_turn` / `is_error=False` で正常終了しながら閉じ括弧を落とした
  JSON を返し、その 1 回で 1 世代が失われた (thinking 449 tokens を消費済み)。
  確率的な生成ミスに対する再試行方針は未定義であり、無人ループの歩留まりを直接下げる。
  ただし retry は「正しさゲートを緩める」方向へ誤用されうるため、
  **parse 失敗に限定し内容の作り直しを許さない**設計が要る。実装面のため Codex author が要る。
