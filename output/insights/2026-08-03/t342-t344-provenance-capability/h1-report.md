実装を working tree に残しました。docs・Git index・commit・branch は操作していません。

### 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| variant 再導出の過剰拒否 | closed | BUILD_START 自身だけ canonical identity を再導出。BUILD_START のない variant は拒否しない |
| Layer 3 の残赤 7件 | closed（実装） | post-policy fixture を維持し、receipt 伝播を実 WAL 契約へ限定。framing 診断と report view を調整 |
| bench-first 実 WAL の残赤 4件 | closed（実装） | admission-aware node 専用に policy-bound lock＋canonical receipt 付きコピーを生成 |
| plain-runner coverage | closed（静的確認） | `test_artifact_admission.py` と `test_build_admission.py` に `_run()`/`__main__` を追加 |
| pytest 実測 | partial | `hostname=pegasus02` のためリポジトリ規律に従い未実行 |
| regressed | 未判定 | pytest 未実走のため、実行時回帰の有無は確定していない |

### variant 再導出の narrow

[artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h1/orchestrator/campaign/artifact_admission.py:543) では、BUILD_START が存在する場合だけ genome・source evidence から variant を再導出して一致を要求します。全 WAL record に BUILD_START の存在を要求していた後段ループは削除しました。

BUILD_START のない variant が通る正例は [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h1/orchestrator/tests/test_artifact_admission.py:232) に固定しました。

narrow 後も次は拒否されます。

- receiptless campaign の未証明 historicity
- policy-bound lock の policy 不一致
- attempt topology、receipt canonicality・伝播 SHA の不一致
- BUILD_START の genome/source/lock identity 不一致
- BUILD_START 自身の canonical variant 不一致
- 検証中の lock/WAL byte 変更

### fixture 修正

Layer 3 は [test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h1/orchestrator/tests/test_layer3_report.py:37) で `derive_build_admission()` から canonical receipt を生成し、[policy-bound lock](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h1/orchestrator/tests/test_layer3_report.py:117) を書きます。receipt SHA は BUILD_DONE・COMMIT・attempt-bound ABORT にのみ伝播します。

Layer 3 report 側では admission transport field を材料 view から除外し、post-policy truncated WAL も従来の framing 診断を保ちます。[layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h1/orchestrator/campaign/layer3_report.py:221)

bench-first の4 nodeは [専用 post-policy fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h1/orchestrator/tests/test_bench_first_real_wal.py:62) を使用します。元の9-record raw fixtureは、実出力形そのものを検査する非-admission test用に保持しました。

validator の monkeypatchや allowlist追加はありません。各 admission-aware consumer は実際の `require_admitted_campaign()` を通ります。

plain-runner harness は以下に追加しました。

- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h1/orchestrator/tests/test_artifact_admission.py:300)
- [test_build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h1/orchestrator/tests/test_build_admission.py:292)

### 検査

走らせた pytest nodeid: なし（0件）。

`pegasus02` ログインノードでは単一 nodeidを含めpytest禁止のため、緑は主張しません。

実施済み:

- 所有7 Pythonファイルの `python3 -m py_compile`: 成功
- 所有差分の `git diff --check`: 成功

未実施:

- 指定された Layer 3 7件、bench-first 4件、plain-runner meta-test
- `test_artifact_admission.py`、`test_build_admission.py` 全体
- acceptance/full suite、mutation、build、campaign実走

### 直さず報告した項目

- accept3 のうち `critic/`、`p3_*`、`guided.py`、autonomous、S6/S8a、qualification、`test_campaign.py` 等の所有外残赤
- 既存の所有外 working-tree 差分。編集禁止の `silo_ladder_rung1.py` にも先行差分がありますが、本作業では触れていません
- `test_plain_runner_coverage.py` 本体とREADME allowlistは変更不要だったため未編集です

## 総括

BUILD_START のある variant の canonicality gate は維持しつつ、BUILD_START のない正当な variantへの過剰拒否を除去しました。対象11 fixture nodeは実 receiptとpolicy-bound lockを使う形へ揃え、2つの新規test fileには自走harnessを追加済みです。実行検証のみ、Pegasusログインノード規律により未完です。