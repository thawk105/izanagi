## 所見 1 — queue 行の全体一意性が裁定より弱い

(a) 主張: execution queue 行の候補抽出と、その行の書式検証が同じ正規表現に結合されています。このため、正常な行が1本ある状態で、別 server や不正な queue 名を持つ2本目の `(Execution Queue)` 行を追加しても受理されます。

(b) 根拠: [`paper_story_a1_paired.py:313`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:313) の正規表現は、最初から `@nqsv` と限定文字の queue 名を満たす行だけを候補にします。[`同:2905`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:2905) はその候補数だけを数えます。例えば正常な行に続けて `Queue = other@other (Execution Queue)` を置くと、後者は数えられず、state、件数、位置、queue 名の全条件が成立します。裁定は候補数検査と唯一の行の書式検査を別条件にしています（[`s4-ruling.md:126`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2349-a1-qstat-format/s4-ruling.md:126)）。既存負例は wrong-server 行への置換だけで、正常行との併存を試していません（[`test_paper_story_a1_job_contract.py:353`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/test_paper_story_a1_job_contract.py:353)）。

(c) 成果物への影響: 複数の execution queue 表示を含む曖昧な scheduler 出力が可視性 gate を通り、submission receipt が発行されます。stdout 全体で1本という fail-closed 境界を満たしません。

(d) 判定: **real**

(e) 重要度: **must-fix**

## 所見 2 — 裁定 §7 の残りの条件

(a) 主張: 所見1を除き、§7 条件1から6に未実装または弱められた条件がある、という疑いは退けられます。

(b) 根拠:

- 条件1: 共有 regex と parser を alias import し（[`paper_story_a1_paired.py:41`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:41)）、terminal parser も共有 regex を参照しています（[`同:572`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:572)）。
- 条件2: rc、空 stderr、canonical `{QUE, RUN}`、Request ID、queue 位置、`gen_S` は実装されています（[`同:2895`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:2895)）。不足は所見1の候補集合だけです。
- 条件3: disappearance の fullmatch、正規化 ID 束縛、prior visibility が producer と consumer の双方にあります（[`同:557`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:557)、[`同:3755`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:3755)、[`同:3773`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:3773)）。
- 条件4: 12語 reader、terminal 集合、state／exit-status 述語に変更はありません（[`同:306`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:306)）。
- 条件5: production 関数を通ることは所見5のとおりです。
- 条件6: worktree の4個の非空 fixture は指定された raw bytes と `cmp` 一致しました。不存在 stderr は裁定どおり0 bytesです。

(c) 成果物への影響: 所見1を修正すれば、§7 の実装面に他の欠落は見当たりません。

(d) 判定: **refuted**

(e) 重要度: **nit（追加修正なし）**

## 所見 3 — 実機 RUN、PRR、Queued の過剰拒否

(a) 主張: 実機3形式が正常運用で fail-closed する、という疑いは退けられます。

(b) 根拠:

| 実機入力 | 共有 leaf の結果 | queue 条件 |
|---|---:|---|
| RUN: `Current State = Running`（[`qstat-f-980043.nqsv.txt:7`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2349-a1-qstat-format/qstat-f-980043.nqsv.txt:7)） | `RUN` | line 11 が一致 |
| PRR: `Current State = Pre-running`（[`qstat-f-980062.nqsv.txt:7`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2349-a1-qstat-format/qstat-f-980062.nqsv.txt:7)） | `RUN` | line 11 が一致 |
| Queued（[`qstat-f-queued-978193.excerpt.txt:3`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2349-a1-qstat-format/qstat-f-queued-978193.excerpt.txt:3)） | `QUE` | line 7 が一致 |

共有写像は Running／Pre-running を `RUN`、Queued を `QUE` にします（[`scheduler_nqsv.py:55`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/scheduler_nqsv.py:55)）。3 parameter とも observer から acquisition validator まで通すテストです（[`test_paper_story_a1_job_contract.py:248`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/test_paper_story_a1_job_contract.py:248)）。

(c) 成果物への影響: D805 が却下した `Current State` の一部実測値だけへの過学習は再導入されていません。

(d) 判定: **refuted**

(e) 重要度: **nit（追加修正なし）**

## 所見 4 — 独立境界として数えられない検査

(a) 主張: `_observe_qstat_visibility` の `len(request_matches) == 1` は現行実装では恒真です。また producer 出力を直ちに validator へ渡す正例は wiring 試験であり、canonical 制限の独立した再検査ではありません。

(b) 根拠: 共有 leaf は同じ `QSTAT_REQUEST_ID_RE` の match 数が1でなければ state を返しません（[`scheduler_nqsv.py:80`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/scheduler_nqsv.py:80)）。observer は返された state が `{QUE, RUN}` に入ることを確認した後、同じ regex の件数を再確認しています（[`paper_story_a1_paired.py:2904`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:2904)）。正例も生成値をそのまま receipt に差し込みます（[`test_paper_story_a1_job_contract.py:273`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/test_paper_story_a1_job_contract.py:273)）。

(c) 成果物への影響: 現在の受理集合は広がりません。Request ID 一意性の実効境界は共有 leaf、canonical 制限の実効境界は producer の state 集合検査です。これらを二重の独立証明として数えると監査上の境界数を過大評価します。

(d) 判定: **real**

(e) 重要度: **nit**

## 所見 5 — production wiring と stub の境界

(a) 主張: 新規テストが helper だけを直接呼び、production 関数を迂回している、または parser と observer の両層を stub している、という疑いは退けられます。

(b) 根拠: visibility テストは `subprocess.run` だけを差し替えて `_observe_qstat_visibility` を呼び、その結果を `validate_acquisition_receipt` に通します（[`test_paper_story_a1_job_contract.py:265`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/test_paper_story_a1_job_contract.py:265)）。terminal 正例も `_observe_scheduler_terminal` から `validate_completion_receipt` まで通ります（[`同:1208`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/test_paper_story_a1_job_contract.py:1208)）。consumer 負例は producer で作った receipt を変異させて validator を再実行します（[`同:1301`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/test_paper_story_a1_job_contract.py:1301)）。新規テストから private parser helper の直接呼出しはありません。

(c) 成果物への影響: parser、observer、receipt validator の実配線が試験対象です。pytest は未実走なので、ここで述べるのは静的な到達性だけです。

(d) 判定: **refuted**

(e) 重要度: **nit（追加修正なし）**

## 所見 6 — 既存テストの緩和と揮発値

(a) 主張: assertion の削除、反転、skip、または揮発 payload を期待値へ焼き込む緩和は見当たりません。

(b) 根拠: 既存テストの変更は、qsub ID を raw fixture の ID に合わせ、合成 qstat 文字列を実機 fixture に置き換えた部分だけです（[`impl.patch:673`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2349-a1-qstat-format/s6/impl.patch:673)）。同 hunk に assertion の変更はありません。実機 fixture 内の時刻や path は raw bytes の一部ですが、期待値は canonical state、queue、固定 stub 時刻 `2` だけです（[`test_paper_story_a1_job_contract.py:295`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/test_paper_story_a1_job_contract.py:295)）。

(c) 成果物への影響: 既存の repository-root 経路試験は維持され、scheduler 入力の代表性は改善されています。

(d) 判定: **refuted**

(e) 重要度: **nit（追加修正なし）**

## 所見 7 — 絶対規律2と変更禁止 path

(a) 主張: 無断で verifier、anomaly、promotion correctness 面または変更禁止 path に差分を広げた、という疑いは退けられます。ただし「validator に差分が無い」という文字どおりの説明は正確ではありません。

(b) 根拠: patch header は driver、既存テスト、5 fixture だけです（[`impl.patch:1`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2349-a1-qstat-format/s6/impl.patch:1)、[`同:124`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2349-a1-qstat-format/s6/impl.patch:124)、[`同:347`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2349-a1-qstat-format/s6/impl.patch:347)）。`scheduler_nqsv.py`、job shell、A-2、dispatcher、docs の header はありません。`validate_completion_receipt` 自体には差分があります（[`paper_story_a1_paired.py:3760`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:3760)）が、これは裁定 §7.3 が明示的に要求した consumer 側の受理集合縮小です（[`s4-ruling.md:135`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2349-a1-qstat-format/s4-ruling.md:135)）。

(c) 成果物への影響: 関連しない correctness 判定の意味は変更されていません。completion receipt の変更は別 ID・非 signature 出力を新たに拒否する強化です。

(d) 判定: **refuted**

(e) 重要度: **nit（報告表現のみ注意）**

## 所見 8 — M1 から M10 の静的 kill 対応

(a) 主張: 親が事前登録した M1 から M10 に、kill test が無い変異は見当たりません。

(b) 根拠: 以下の nodeid は、各変異を意味どおり注入すると期待した例外が消えるか、正例が失敗するため赤になります。これは未実走の静的判定です。

| 変異 | 赤になる test nodeid |
|---|---|
| M1 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_visibility_rejects_each_noncanonical_observation[M1-held]` |
| M2 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_visibility_rejects_each_noncanonical_observation[M2-queue-before-id]` |
| M3 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_visibility_rejects_each_noncanonical_observation[M3-wrong-queue]` |
| M4 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_visibility_rejects_each_noncanonical_observation[M4-missing-marker]` |
| M5 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_terminal_observer_rejects_nonterminal_nqsv_observations[M5-other-request]` |
| M6 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_terminal_observer_rejects_nonterminal_nqsv_observations[M6-nonsignature]` |
| M7 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_visibility_rejects_each_noncanonical_observation[M7-nonempty-stderr]`。terminal 側も `test_terminal_observer_rejects_nonterminal_nqsv_observations[M7-nonempty-stderr]` |
| M8 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_real_nqsv_visibility_flows_through_acquisition_validator[M8-running]`、`[M8-pre-running]`、`[M8-queued]` |
| M9 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_visibility_rejects_each_noncanonical_observation[M9-unknown-state]` |
| M10 | `orchestrator/tests/test_paper_story_a1_job_contract.py::test_completion_validator_reparses_disappearance_stdout[M10-other-request]`。`[M10-nonsignature]` も同じ変異を殺します。 |

(c) 成果物への影響: M1からM10について事前登録上の欠落はありません。ただし所見1の「正常行と、書式不正な別 execution queue 行の併存」は変異表外で、現実装もテストも受理してしまいます。

(d) 判定: **refuted**

(e) 重要度: **nit（M1からM10自体の追加対応なし）**

## 総括

**受理不可です。must-fix は1件**です。`_NQSV_EXECUTION_QUEUE_RE` が候補識別と書式検証を兼ねているため、stdout 全体の execution queue 行一意性が裁定より弱くなっています。正常行と malformed execution queue 行を併存させる回帰テストを追加し、候補行を全体で数えた後に唯一の行の server、marker、queue 名を検証する必要があります。

それ以外の §7 条件、実機 RUN／PRR／Queued の受理、disappearance の ID 束縛、production wiring、変更禁止 path、M1からM10の kill 対応は静的には成立しています。pytest は制約どおり実行していません。