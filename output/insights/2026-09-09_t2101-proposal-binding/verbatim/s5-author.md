## 実装したもの

- B-4 bootstrap 提案を一度だけ読み、同じ parse 結果から canonical SHA-256 を再導出。
- 封印済み publication を実 loader で検証し、`attempt_id` の一意性、driver、登録 hash、提案 hash を照合。
- base / sort / trigger の全 loader と launcher/driver CLI を配線。
- continuation と非 B-4 では新しい束縛引数を拒否。
- 裁定 §7 の非保証 7 項を逐語定数として収録。
- 実 publication を使う新規テスト 23 node 相当を実装。単一読取り、既存 gate 順序、実行前拒否を含む。

## 変更した file と行

Production:

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:171): 非保証、canonical hash、registry lookup、base loader/CLI。
- [p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_sort.py:439): sort loader/CLI。
- [p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:919): trigger loader/CLI。
- [p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_b4_launcher.py:177): bootstrap 引数 forwarding と mode gate。

Tests:

- [test_p3_b4_proposal_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:47): 新規。
- [p3_b4_proposal_binding_support.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/p3_b4_proposal_binding_support.py:14): 実 publication fixture。
- [test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_closed_critic.py:113): 共有 production context fixture。
- [test_p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_launcher.py:331): forwarding 検査。
- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_s4_loop.py:4395): 既存 bootstrap 正例へ正当な binding を追加。

## 現行の受理・拒否挙動の変化

変更前は、B-4 bootstrap が receipt key 不在と closed schema を満たせば、registry と無関係な schema-valid 提案も受理されました。

変更後:

- 一致する bootstrap 提案だけを受理。key 順、空白、Unicode escape の表記差は許容。
- 不一致、束縛欠落、相対/不在 publication、load 失敗、attempt 不在/複数、hash 不正、driver 不一致を拒否。
- receipt gate、closed schema、既存 fixture/no-build gate の順序は維持。
- continuation と非 B-4 は、束縛引数がない既存入力では挙動不変。束縛引数が混入した新規入力だけ拒否。
- 拒否前に `pgrep`、Git pin 検査、launcher sidecar/campaign directory 作成が起こり得る点は非保証のままです。

## 走らせたテストと結果

pytest の緑はありません。次はすべて `tools/run_tests.py` 経由で試みましたが、pytest child は開始されませんでした。

- `orchestrator/tests/test_p3_b4_proposal_binding.py -q`
- 同 file の `--collect-only`
- `test_canonical_identity_distinguishes_int_float_and_excludes_receipt`
- `test_plain_runner_coverage.py` の file 列挙メタテスト 2 node

いずれも実装済み・未実走です。

補助確認:

- 変更 9 file の AST parse/import: 成功。
- `git diff --check`: 成功。
- 実 publication smoke: base/sort/trigger の一致受理、base の同一 root/id 不一致拒否を確認。
- production context fixture smoke: 成功。
- docs、凍結 closure 5 file の差分なし。
- commit なし。

## 赤の内訳

テスト assertion の赤はありません。全 runner 試行が `rc=16` で、原因は `qstat -Q preflight rc=1`、`Unknown user-id` による dispatch infrastructure failureです。queue 状態も観測不能で、pytest child は一度も開始されていません。

最初の手動負例 smoke は、期待した不一致例外を捕捉しない形だったため `rc=1` になりました。例外内容は意図した canonical hash mismatch で、実装異常ではありません。

## 波及の静的列挙

- formal bootstrap launcher の全 caller は新しい publication root と attempt id が必要。
- 3 driver の直接 bootstrap loader caller も同様。既存 history helper は更新済み。
- `_production_launch_context` の既存利用者 15 件は実 publication fixture を共有経路で取得。
- `p3_s4_loop.py` と launcher の変更により、closed-critic の base/sort/trigger projection digest はすべて変化。
- 旧 launcher blob を固定した外部 v2 campaign lock は再開時に contract-loader drift で停止し得る。
- `p3_b4_raw_record_producer`、material report、issuer receipt の古い非保証文言は今回変更していません。
- 新規 test file を列挙するメタテストは `test_plain_runner_coverage.py`。静的 harness 判定は成功、pytest は未実走です。

## 実装しなかったもの

- continuation の初期提案束縛。
- publication root の権威固定。
- manifest membership 検査。
- 束縛成功の耐久証拠。
- issuer 側 canonical hash producer。
- 新しい台帳、receipt、署名、capability、汎用 framework。
- docs、凍結 receipt schema、凍結 closure、commit。

## 総括

要求された bootstrap proposal binding は 3 driver へ実装済みで、実 API smoke と静的検査は成功しています。ただし Pegasus の queue 認証障害により、pytest は全範囲が未実走です。