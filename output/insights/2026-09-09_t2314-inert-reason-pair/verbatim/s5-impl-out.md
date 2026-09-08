## 実装した内容

- [t316_sandbox_backend_probe.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:124)
  - 変更前: identity の reason/comparison を述語内で固定。
  - 変更後: `_INERT_CONDITION_GATE_PAIRS` に D1625 の2組だけを定義。
- [t316_sandbox_backend_probe.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:320)
  - supply receipt に `"comparison": supply.evidence.get("comparison")` を追加。
  - `evidence` mapping 自体は出力していない。
- [t316_sandbox_backend_probe.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:357)
  - 変更前の単一組 exact 判定を、2要素 tuple の集合 membership に変更。
  - admission、receipt equality、driver、macro、status、meaning 条件はすべて維持。
- [test_t316_sandbox_probe.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:185)
  - `__FILE__` を両 header に追加し、production evaluator から root-location-only family を発行。
- [test_t316_sandbox_probe.py:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:233)
  - `stock_comparison=False` の genuine requested/default family を追加。
- [test_t316_sandbox_probe.py:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:267)
  - fixture receipt の supply entry に `comparison` を純増。
- [test_t316_sandbox_probe.py:964](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:964)
  - 正例2、交叉負例2、第3 reason 負例1を追加。
  - 交叉負例は局所 seam と交叉後 family 由来 receipt を使用。

## 変更前の受理・拒否挙動

変更前は genuine な `(stock-inert-preprocess-identical, stock-inert-identity)` だけを受理し、root-location-only 組は gate が admit しても `S6_CONDITION_GATE_UNPROVEN` でした。

交叉2方向は gate 層で拒否され、第3 reason は gate が admitしても probe が拒否していました。receipt は comparison を保持せず、旧形との exact summary equality を要求していました。

変更後の受理集合は D1625 の2組だけです。交叉、第3 reason、その他の既存拒否条件は引き続き拒否します。

## 実走した検査

- 新規5 nodeid、rc=0、`5 passed, 122 deselected`
  - `test_s6_accepts_each_exact_inert_condition_gate_pair[identity]`
  - `test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]`
  - `test_s6_rejects_crossed_inert_condition_gate_pair[identical_reason__root_location_comparison]`
  - `test_s6_rejects_crossed_inert_condition_gate_pair[root_location_reason__identity_comparison]`
  - `test_s6_rejects_requested_default_preprocess_difference`
- `test_t316_sandbox_probe.py` 全範囲、rc=0、`127 passed`
- collection 確認、rc=0、全127 nodeと上記5 nodeidを確認。
- `test_acceptance_schedule_order.py` 制約 meta-test 全範囲、rc=0、`79 passed`。
- `test_official_perf_closure.py` 全範囲、rc=0、`7 passed, 0 failed`。

なお、coverage nodeだけを `PYTEST_ADDOPTS=-k` で選択した初回は selector が内部 collect-only に継承され rc=1 となりました。selector を除いた正規の全範囲実行で rc=0 を確認済みです。

## 波及の静的列挙

- 所有外 caller:
  - `_execute_ccbench_build` が新 receipt summary を生成。
  - `observe_s6` が family と summary を伝播。
  - `verdict_s6` が新しい2組述語を適用。
- 共有依存:
  - `condition_meaning_gate.evaluate_define_supply_effectuation`
  - `orchestrator/tests/fixtures/condition_meaning_gate/supplied`
  - いずれも未変更。
- consumer test:
  - S6 injected/unissued/receipt mismatch/legacy vocabulary tests
  - `test_injected_observer_flows_through_judge_and_overall`
  - `_good_stages` 経由の containment/performance discharge tests
  - `test_r3_1_coverage_does_not_overclaim`
  - acceptance coverage、official-perf closure、hooks path classification
- PBS の `HEAD:<path>` 実行時 pin と admission registry は新 blobへ追随するため co-edit 不要。

## 残した赤・未了

実装側の赤はなし。受入所要台帳への5 nodeid追加は、指示どおり親が行う段5として未変更です。

## 総括

D1625 の2組だけを exact に受理する述語へ変更しました。  
root-location-only と第3 reason は production evaluator 発行 record で検査しています。  
交叉負例は receipt mismatch に逃げず、probe の pair membership を直接検査します。  
対象全127 nodeと関連する制約 meta-test はすべて緑です。