# 段 1 brief — [T-2279] 変異 harness 経由の D612 queue-wait 上書きの食い違い

## 研究前進

変異 matrix は、全 dev-wave の実装面に対して絶対規律 2 / 3 (正しさゲートを緩めない・正しさシグナルを
後付けにしない) を機械的に効かせる唯一の道具である。gen_S 混雑時にこの道具が「走らせられない」
(F762、4 回連続の起動失敗) か「mutant の性質でない TIMEOUT を mutant の観測状態として記録する」
状態にあると、Phase 3 合成の実装を land するたびに検査が空振りするか、変異台帳の値が誤る。
本 wave は上書きの伝播経路を特定して塞ぎ、混雑下でも変異検査を成立させる。完了判定は
「上書きが届かない経路がコード上で 0 になり、届いていることを正例テストが実測する」こと。

## scope

- 対象: `tools/mutation_harness.py` / `tools/mutation_fanout.py` / `tools/mutation_worktree.py` と
  既存 `orchestrator/tests/test_t2337_dispatch_timeout_overrides.py`。
- 原因の特定と、特定できた分の修正だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外
  (ユーザー明示)。修正した機構の正例テストは scope 内 (規律 3、DW-S04 の「通る正例を 1 つ」)。
- `tools/pegasus/dispatch_compute.py` の受理集合変更は scope 外 (F762 が別裁定と明記)。

## 確定済みユーザー裁定・既存被覆 (純増を出すための棚卸し)

- D612: 上書きは opt-in 環境変数だけ。既定 900/300 は変えない。自動選択も `_is_acceptance_run`
  分岐も採らない。→ 本 wave は既定値も自動選択も触らない。
- F762 (docs/failures.md:20562) が 2026-09-03 時点の根本原因を記録: harness は dispatch 時に
  `run_tests.py` を介さず `dispatch_compute.py` を直接呼ぶので上書きが届かない。当時「恒久対応: 未実装」。
- **依頼の前提を覆す新事実:** commit 1e22c4cbd (2026-09-07) が `_collection_command`
  (mutation_harness.py:1421-1490) に `--queue-wait-timeout` / `--overall-grace` の転送と
  「外側 timeout < queue+grace なら起動前に拒否」の gate を入れ、04954fbd2 が解釈器を harness 内へ
  自己完結させた。よって **collection 経路は既に閉じている**。904 秒 (2026-09-03 実測) は当時の
  collection 経路の 900 秒既定で説明がつく。純増は「本走 (baseline / mutation) 経路に何が残るか」。
- 既存 gate は collection の argv 形と provenance の kwargs しか見ていない (test_t2337 全文)。
  本走経路は無検査。

## 不変条件

- 既定 900/300 を変えない。上書きは opt-in のまま。受理集合を広げない。
- 規律 2 を緩めない: TIMEOUT / infra 失敗を KILLED や PASSED へ読み替える方向の変更を採らない。
- `_FIXED_HEAD_PATHS` (tools/mutation_fanout_contract.py:35) が harness / worktree の HEAD blob を
  束縛するので、実装後は焦点走の前に commit する。

## (P1) 親の provisional 裁定 — 攻撃対象

- (P1) 本走 (`_baseline` 2125-2131 / mutation 2248 付近) は runner command = `tools/run_tests.py` を
  そのまま起動し、`runner_env` (1933-1943) は `IZANAGI_DISPATCH_*` を落とさないので上書きは届く。
  残る欠陥は「harness の外側 watchdog `spec.timeout_seconds` が queue+grace より短いと、
  上書きを効かせた本走だけが watchdog に先に殺され、結果が TIMEOUT として mutant に帰属する」
  ことであり、collection にある事前拒否 gate が本走に無いこと。
- (P2) `mutation_fanout.py` / `mutation_worktree.py` に上書きを落とす経路は無い
  (`_child_env` 746-749 は GIT_* しか触らない)。

## 成果物の形

- 特定結果: どの経路にどの欠陥が残るかを file:line で示した裁定と insight。
- 修正: 特定できた経路のコード修正 + 通る正例テスト (既存 test file へ追加)。
- 変異 matrix (実装面があるため免除なし)、受入全走、worklog / insight / 必要なら decisions fragment。

## 分割方針

軽量版 + 段 2 / 3 は実施する (正しさ防壁の道具に触り、原因の候補が割れているため)。実装は D95 の
Codex author 1 単位で足りる見込み。親は docs だけを書く。

## 実測環境

login node 上の焦点走と変異 matrix。実 dispatch を要する probe は混雑次第で高くつくため、
必要性が段 4 で認められた場合だけ行う。
