---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t1484-floor-restart-registry
seq: 5
---

## 新規

### {{F:terminal-reason-override-after-value}}. 8c attempt registry は値を見た後の失敗理由の付け替えで再走を得られる [恒真ゲート]

- 事象: `record_attempt_terminal` に渡す明示 `failure_reason` が、事前に封印した分類受領証の
  `pre_observation_failure_reason` を上書きする。terminal 行は受領証の値を
  `pre_observation_failure_reason_echo` として持ち、echo が受領証と一致することは検査されるが、
  **`failure_reason` が echo と一致することは検査されない**。null matrix も
  `failure_reason` が retryable 集合に属することしか見ない。したがって受領証の理由を
  `None` で封印し、性能値を読んでから `terminal_status="retryable-failure"` +
  `failure_reason="preempted"` を付ければ次の slot が受理される。観測開始を記録しなければ
  「観測後の再走禁止」検査も通る。
- 根本原因: 出力前に封印する分類と、再走を認可する terminal 理由が**別の field** になっており、
  両者の一致を要求する検査が無かった。「出力を読む前に分類する」という要件が、
  受領証の存在だけで満たされたことにされていた (恒真ゲート)。
- 恒久対応: {{D:attempt-registry-core-profile-policy}} 決定 3 —
  共通 core の遷移 policy に `require_terminal_reason_equals_classification` を置き、
  一致検査の有無を profile の項目にした。**8b profile は `True`** で塞いである
  (`orchestrator/campaign/s8b_attempt_profile.py`)。
  **8c profile は `False` のままであり、8c 側の穴は開いたままである** —
  締めると 8c の受理集合が狭まり D672 の実装条件に反するため、締める時期は別途のユーザー裁定に委ねる。
- 再発検知: `orchestrator/tests/test_attempt_registry_core_s8b_profile.py` の
  「8b は理由不一致を拒否し、同じ入力を 8c profile は従来どおり受理する」対の検査。
  段 4 事前登録の変異 M2 (8b profile の policy を `False` へ倒す) が実測で kill されることを確認済み。
