---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1669-floor-ledger-recovery
seq: 1
---

## 新規

### {{F:same-gate-both-sides-broke-valid-history}}. 「両側を同じ厳しさに」の指示が、履歴再検査側で正当な履歴を全部落とした [恒真ゲート] [テスト代表性]

- 事象: 段 6 の親裁定が「消費側と最終検査側に同じ gate を持たせよ」と指示した結果、
  実装が「その cell で最新の retry start であること」を最終検査にも課した。最終検査は履歴上の
  すべての retry start を再検査するため、recovery が連鎖した正当な履歴
  (planned が retry1 を開き、retry1 の recovery が retry2 を開く) では retry1 を再検査する時点で
  最新が retry2 になり、**正当な履歴が必ず拒否される**。測定はできても成果物が
  `artifact-invalid` で終わる行き止まりになる。
- 根本原因: 「同じ厳しさ」という指示語が、**評価時点に依存する述語**を含む gate に対して
  未定義だった。認可を出す時点と履歴を再検査する時点では、同じ規則でも真偽が変わる述語がある。
  親はその区別を裁定文に書かず、実装子は素直に両側へ同じ条件を置いた。
- 恒久対応: {{D:same-gate-different-time-is-not-asymmetry}} —
  評価時点に依存する述語は明示的な引数で分岐させ、暗黙の分岐・呼び出し側の事前フィルタ・
  片側だけの緩和で代替しない。裁定文で「同じ gate を共有せよ」と書くときは、
  時点依存の述語があるかを先に問う。
- 再発検知: 連鎖 recovery の履歴が最終検査まで通る正例
  (`test_registry_recovery_of_retry_attempt_selects_that_attempt_as_trigger`) と、
  consume 側で飛び ordinal・過去 ordinal を拒否する負例の対。
  変異 `MUT-T1669-RETRY-LATEST` が consume 側の力を固定する。
- 検出経路: **静的レビュー 3 本 (敵対 2 + 焦点再レビュー 1) は検出できなかった。**
  親のテスト実走が初めて赤にし、単独走の連鎖例外まで読んで根本原因を特定した。

### {{F:green-focus-run-hid-unreachable-implementation}}. 焦点走が全緑なのに、実装が production 経路から一度も呼ばれていなかった [テスト代表性]

- 事象: 段 5 の実装は焦点走 (変更 file 単独 153 passed、consumer 13 file 1812 passed) が
  すべて緑だったが、段 6 の敵対 2 レンズが独立に「production から到達不能」と指摘した。
  crash 後の再開処理は `session-start` のある seq を forward-only で飛ばすため復旧の入口へ
  到達せず、再試行を作る producer も新しい根拠を読まなかった。
  新設テストは低層 API を直接 2 回呼ぶ形だったため、この到達不能を隠していた。
- 根本原因: テストが「機構が正しく動くか」だけを撃ち、「**production の実経路がその機構へ
  到達するか**」を撃っていなかった。到達不能は緑では見えない。
- 恒久対応: 新しい復帰・再開機構を足す wave では、低層 API の直接呼出しテストに加えて
  **production の resume 経路を実際に通る正例**を必須にする。
  段 6 のレビュー lens に「実効性 — 実装したのに効かない形になっていないか」を明示的に入れ、
  「この機構が発火するには production のどの経路が呼ぶ必要があるか」を file:line で答えさせる。
- 再発検知: `_Runner.run()` の resume を通る正例
  (`test_resume_runner_replays_only_admission_proved_cut6_m_plus_a_minus`、
  `test_resume_runner_produces_one_retry_from_admission_selected_recovery`) と、
  変異 `MUT-T1669-CUT6-ADMISSION` / `MUT-T1669-TRIGGER-FORWARD`。

### {{F:verified-artifact-chose-its-own-trust-root}}. 検証対象の受領証が自分の trust root を名乗れた [恒真ゲート]

- 事象: 「検証済み recovery」の検証で、候補 receipt の `authority_id` と
  `authority_policy_sha256` を読み、その値で検証 profile を組んでいた。共通 core は
  「caller が渡した policy と receipt が一致するか」しか検査しないため、
  **任意の authority で自己整合させた registry が受理される**状態だった。
  テスト正例も自分で選んだ authority 文字列で通っていた。
- 根本原因: 信頼の根を、検証対象の artifact から採った。
  「全 replay と hash chain に束縛されている」ことは、chain 全体を攻撃者が作れる場合に
  何も保証しない。
- 恒久対応: {{D:floor-next-ordinal-needs-registry-recovery}} —
  authority は admission に pin した許可集合でのみ受理する。今日は空集合とし、
  fail-closed であることをコードで強制する。
- 再発検知: `test_registry_recovery_authority_is_empty_and_fail_closed` と
  変異 `MUT-T1669-AUTHORITY-PIN`。
- 検出経路: 段 6 の敵対レビュー (正しさ境界レンズ) が現物の file:line で示した。

### {{F:narrowing-candidates-before-counting-widened-acceptance}}. 候補を絞ってから数えたため、曖昧な履歴が消費側だけ通った [恒真ゲート]

- 事象: 「排他的二択」を実装する過程で、旧経路の候補を「正しい cell・planned・`valid=False`」に
  **絞ってから**件数を数える形にした。その結果、正しい失敗行 1 件と同じ trigger attempt の
  **不正な余分の完了行 1 件**が併存しても、消費側は前者だけを数えて受理した。
  最終検査は重複を拒否するため、測定後に `artifact-invalid` で終わる非対称になった。
  修正前は同じ attempt の全 `session` を数えて 1 でなければ拒否していたので、**受理集合の退行**である。
- 根本原因: 件数による排他検査は「母集合を絞る前に数える」ことで初めて曖昧さを検出できる。
  絞り込みは正しさの検査ではなく、曖昧さを隠す操作になりうる。
- 恒久対応: 候補件数は絞る前の母集合で数え、canonical 述語はその後に適用する。
  同じ考え方を registry 側の候補計数にも適用した。
- 再発検知: `test_legacy_retry_rejects_extra_completion_for_same_trigger` と
  `test_registry_recovery_counts_corrupt_extra_candidate_before_replay`、
  変異 `MUT-T1669-RETRY-XOR` / `MUT-T1669-RECOVERY-CANDIDATE-COUNT`。
- 検出経路: 統合後の焦点再レビューが `regressed` として判定した。
  焦点走は緑のままだったので、実測では見えなかった。
