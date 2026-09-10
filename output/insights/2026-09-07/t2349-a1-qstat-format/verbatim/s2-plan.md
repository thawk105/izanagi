## 推奨方針

| 論点 | 推奨 |
|---|---|
| P1 | 新規 receipt には共有 parser の正規化後 `QUE` / `RUN` を書く。既存 schema の reader は現行の有限集合を維持し、過去の `STG` などだけ後方互換として読む。 |
| P2 | 実書式 `Queue = <name>@nqsv (Execution Queue)` を対象 request の後方からちょうど 1 行だけ抽出し、`<name> == "gen_S"` を要求する。 |
| P3 | `_parse_qstat_terminal` と `NQSV_QSTAT_TERMINAL_STATES` は変更しない。実測の無い終端状態形式を共有 parser 経由で増やさない。 |
| P4 | `rc == 0` は必要条件に留める。不在扱いには対象 ID と一致する `Batch Request: ... does not exist on nqsv.` の完全一致も要求する。 |

根拠は、共有 leaf が実機 RUN と PRR の `Current State` をともに `RUN` へ写し、未知語を `state-vocabulary-unknown` として拒否することです。[scheduler_nqsv.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/scheduler_nqsv.py:40) と射影された逐語コピーはバイト一致していました。

## P1: state の書込み語彙と reader 互換

新規書込みは正規化後の `QUE` / `RUN` にします。

- [paper_story_a1_paired.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:40) 付近で `QSTAT_REQUEST_ID_RE` と `target_bound_qstat_state_result` を共有 leaf から import します。
- [paper_story_a1_paired.py:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:312) 付近に、producer 専用の `_NQSV_SUBMISSION_VISIBLE_STATES = frozenset({"QUE", "RUN"})` を置きます。
- [paper_story_a1_paired.py:2870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:2870) は共有 parser の結果が `QUE` または `RUN` の場合だけ受理し、その正規化値を receipt の `state` に書きます。したがって実機 `Pre-running` も receipt では `RUN` です。

一方、既存 receipt の schema version は変えず、stdout も receipt に残っていません。このため過去 receipt と新規 receipt を安全に識別して再正規化できません。reader は次の既存有限集合を維持します。

```text
ARR WAI QUE PRR RUN POR EXT HLD HOL SUS MIG STG
```

対象は次の三箇所です。

- V3 group submission validator: [paper_story_a1_paired.py:2983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:2983)
- direct submission の同族再検査: [paper_story_a1_paired.py:3540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3540)
- disappearance 前の prior visibility: [paper_story_a1_paired.py:3590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3590)

ここは `NQSV_QSTAT_STATES` membership を変えません。結果として:

- 新規 writer の語彙は厳密に `{QUE, RUN}`。
- reader の語彙は schema-v1 後方互換の現行 12 語。
- `STG` は過去 receipt の読取りに限り受理され、新規には書かれない。
- `XXX`、`Launching` など集合外の語は引き続き拒否される。
- reader の受理集合は現状から広がらず、正しさゲートも緩まない。

## P2: queue の述語

[paper_story_a1_paired.py:2879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:2879) の PBS-Pro 型検索を、実機行だけに合わせます。

変更後の述語は次です。

1. 共有 parser が検証した唯一の `Request ID` 行を境界にする。
2. その行より後だけから、次の形式を検索する。

```text
Queue = <queue-name>@nqsv (Execution Queue)
```

3. 一致数がちょうど 1。
4. `<queue-name>` が `_PBS_QUEUE == "gen_S"`。
5. `Queue: gen_S`、別 server、別 queue、重複 queue 行は拒否する。

正規表現は、大文字小文字を無条件に緩めず、行頭・行末を固定して `@` 前だけを capture する形にします。実機根拠は RUN、PRR とも各ファイル 11 行目です。

## P3: 終端 parser

[paper_story_a1_paired.py:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:547) の `_parse_qstat_terminal`、[paper_story_a1_paired.py:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:326) の `NQSV_QSTAT_TERMINAL_STATES` は触らないことを推奨します。

理由は次の通りです。

- 射影された二つの実機出力は RUN と PRR であり、終了状態の逐語ではありません。
- この機体の実測済み終了形は request 消失です。
- 共有 leaf の `END` 語彙を `_parse_qstat_terminal` に接続すると、`completed`、`finished`、`post-running` など未実測の受理枝を新たに有効化します。
- 現行 parser は過去の visible-terminal receipt を再検査する consumer でも使われています。[paper_story_a1_paired.py:3705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3705)
- 削除や `END` への schema 変更は、今回の実機 submission 書式修正より大きい migration です。

したがって、この wave では terminal branch を増やさず、実測された disappearance branch だけを P4 で狭めます。

## P4: rc=0 の扱い

締めるべきです。実機では不存在も rc=0 なので、現在の「rc=0、非空 stdout、対象 `Request ID` 行なし」という条件では任意の診断文字列を disappearance と誤認できます。

[paper_story_a1_paired.py:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:535) 付近に、A-2 の先例 [paper_story_a2_certification.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a2_certification.py:85) と同じ範囲の disappearance parser を追加します。

変更後の disappearance 述語は以下の論理積です。

```text
returncode == 0
and stderr == ""
and stdout が NQSV disappearance 行の全体一致
and 行中の request ID の正規化値 == 問合せ対象 request ID
and prior visibility receipt が現在の検査を通る
```

適用箇所は二つです。

- producer: [paper_story_a1_paired.py:3746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3746)
- completion receipt の再検査: [paper_story_a1_paired.py:3728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3728)

`rc != 0`、非空 stderr、別 ID の不存在行、単なる空振り診断はすべて失敗にします。receipt schema は変えません。

## file:line 単位の変更計画

| file:line | 変更 |
|---|---|
| [paper_story_a1_paired.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:40) | 共有 leaf から `QSTAT_REQUEST_ID_RE`、`target_bound_qstat_state_result` を import。 |
| [paper_story_a1_paired.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:302) | 重複するローカル request-ID regex を削除し、共有定義へ一本化。 |
| [paper_story_a1_paired.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:311) | 実機 execution queue regex、disappearance regex、producer 用 `{QUE, RUN}` 集合を追加。既存 receipt 用 `NQSV_QSTAT_STATES` と terminal 集合は維持。 |
| [paper_story_a1_paired.py:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:535) | `_qstat_mentions_request` を共有 request-ID regex 使用へ変更し、対象 ID に完全束縛された disappearance helper を追加。 |
| [paper_story_a1_paired.py:2870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:2870) | state を共有 parser で正規化。rc=0、空 stderr、state が QUE/RUN、唯一の実機 queue 行、queue 名 gen_S をすべて要求。返す `state` は正規化値。 |
| [paper_story_a1_paired.py:3728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3728) | disappeared completion receipt の stdout を完全一致 helper で再検査。 |
| [paper_story_a1_paired.py:3746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3746) | rc=0 だけでは disappearance に入れず、空 stderr と完全一致シグネチャを要求。 |
| [test_paper_story_a1_job_contract.py:2394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:2394) | cwd を検査する既存テストの非代表 PBS fixture を実機 RUN fixture に交換。assertion は変更しない。 |
| [test_paper_story_a1_job_contract.py:1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:1023) 付近 | disappearance receipt の別 ID、非シグネチャ stdout を拒否する consumer 再検査テストを追加。 |
| `orchestrator/tests/test_paper_story_a1_qstat.py:1-` | 実機逐語を使う submission visibility と terminal observation の集中テストを追加。 |
| `orchestrator/tests/fixtures/qstat-f-980043.nqsv.txt:1-94` | 提示された RUN 出力を逐語コピー。 |
| `orchestrator/tests/fixtures/qstat-f-980062.nqsv.txt:1-94` | 提示された PRR 出力を逐語コピー。 |
| `orchestrator/tests/fixtures/qstat-f-does-not-exist.nqsv.txt:1` | brief に記録された `900001.nqsv` 不存在出力を逐語化。 |

## 追加テスト

| テスト | 極性 | 殺す実装 | fixture の由来 |
|---|---|---|---|
| `test_visibility_accepts_real_running_and_records_run` | 正例 | PBS-Pro state/queue regexを残す実装、生語 `Running` を receipt に書く実装 | 実機 RUN `qstat-f-980043.nqsv.txt` 全文 |
| `test_visibility_accepts_real_prerunning_and_records_run` | 正例 | `Pre-running` を拒否または `PRR` と記録する実装 | 実機 PRR `qstat-f-980062.nqsv.txt` 全文 |
| `test_visibility_rejects_unknown_current_state` | 負例 | 任意の英字状態、未知語、既定値フォールバックを受理する実装 | RUN 逐語の `Running` だけを `Launching` にした一箇所変異 |
| `test_visibility_rejects_wrong_execution_queue` | 負例 | queue を無視する実装、`@` 以降だけを見て受理する実装 | RUN 逐語の `gen_S` だけを `other` にした一箇所変異 |
| `test_visibility_rejects_duplicate_execution_queue` | 負例 | 最初の queue 一致だけを採用する実装 | RUN 逐語へ同じ queue 行を一行複製した変異 |
| `test_visibility_rejects_rc0_disappeared_request` | 負例 | rc=0 だけで submission visibility とする実装 | brief の実測 `Batch Request: 900001.nqsv does not exist on nqsv.` |
| `test_terminal_accepts_exact_rc0_disappearance_after_visibility` | 正例 | 不存在なら非零 rc のはずだと仮定する実装 | 同じ実測不存在出力 |
| `test_terminal_rejects_rc0_non_signature_absence` | 負例 | 任意の非空 stdout かつ request-ID 行なしを disappearance とする現行実装 | 実測不存在行を非 NQSV 診断文へ置換した負例 |
| `test_terminal_rejects_disappearance_for_other_request` | 負例 | 不存在行の request ID を問合せ対象へ束縛しない実装 | 実測不存在行の ID だけを別 ID にした変異 |
| `test_completion_validator_rechecks_exact_disappearance` | 負例 | producer だけ締め、保存 receipt の再検査を従来の「ID 行なし」に留める実装 | 既存 disappearance fixture を別 ID、非シグネチャへ変異 |
| `test_prior_visibility_retains_legacy_stg_and_rejects_unknown` | 正例と負例を分離 | P1 の reader 後方互換を誤って producer の `{QUE,RUN}` まで狭める実装、および未知語を広げる実装 | `STG` は brief が明記する過去 receipt 語、未知語は一箇所変異 |

既存の [test_acquisition_receipt_accepts_exact_nqsv_qstat_state_vocabulary:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:216) と [test_acquisition_receipt_rejects_non_nqsv_qstat_state_M23:417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:417) は、legacy reader 集合と未知語拒否を引き続き固定します。

## 既存テストの赤予測

そのままでは次の一件が赤になります。

- [test_submit_runs_real_qsub_call_from_repository_root:2385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:2385): 入力 fixture が [2402-2403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:2402) の `State: QUE` / `Queue: gen_S` であり、実機限定の queue 述語を満たしません。

このテストの期待値は誤りではありません。検査対象は qsub の cwd です。F852 で非代表と確定した入力 fixture だけを実機 RUN 逐語へ置換し、cwd、receipt shape、成功結果の assertion は一切変えません。

次は赤にしない設計です。

- [state allowlist の exact test:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:238): legacy reader 集合を維持するため不変。
- [visible terminal producer/validator test:964](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:964): P3 で terminal parser を触らないため不変。
- [disappearance acceptance test:1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:1023): 既存 fixture は正確な NQSV シグネチャなので通る。
- [terminal stdout 再解析 test:3406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_paired.py:3406): P3 の非変更により不変。

pytest は実行しておらず、緑とは報告しません。

## 静的な波及範囲

- `_observe_qstat_visibility` の caller は V3 fan-out submit [3138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3138) と direct submit [3285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3285) です。両方の新規 receipt が canonical state になります。
- V3 receipt は作成直後 [3202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3202)、acquisition [3397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:3397)、completion [4033](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:4033)、consumer/materializer [6493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:6493) と [8384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:8384) で再検査されます。
- `_observe_scheduler_terminal` の production caller は V3 group completion [4080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:4080) と direct completion [4275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:4275) です。
- `validate_completion_receipt` は V3 job projection [8342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:8342) と direct consumer/materializer [6560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:6560)、[8517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:8517) に波及します。
- `orchestrator/scheduler_nqsv.py` は変更しません。A-2 の import [36-39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a2_certification.py:36) と state 検査 [1150-1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a2_certification.py:1150)、D805 が述べる dispatcher consumer の挙動は変わりません。
- A-2 の disappearance 判定 [1235-1240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a2_certification.py:1235) と [1760-1765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a2_certification.py:1760) も変更しません。
- A-1 の source closure [161-180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/campaign/paper_story_a1_paired.py:161) は現状 `scheduler_nqsv.py` を列挙していません。また [source closure test:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2349-a1-qstat-format/orchestrator/tests/test_paper_story_a1_job_contract.py:243) は所有外 shell の同じ一覧との一致を要求します。この wave では一覧や shell を変更しません。

## 総括

- 推奨: 新規 receipt state は共有 leaf の正規化後 `QUE` / `RUN` に限定する。
- 推奨: 過去 receipt は現行の有限集合でだけ読み、`STG` を後方互換として残す。未知語は拒否する。
- 推奨: queue は実機の `gen_S@nqsv (Execution Queue)` 形式を対象 request の後方で一意に束縛する。
- 推奨: `_parse_qstat_terminal` と terminal state 集合はこの wave では変更しない。
- 推奨: rc=0 の disappearance は対象 ID を含む NQSV 不存在行の完全一致で締め、producer と consumer の双方で検査する。
- 未解決: 新たな共有 leaf import を A-1 source closure に含めるかは、所有外 shell の同期変更が必要になるため本 scope では扱えない。親が leaf を infrastructure として closure 外に置くか、別 wave で変更面を広げるか裁定が必要。
- 未解決: 「到達不能枝を温存しない」を historical visible-terminal receipt の reader にも適用するなら、P3 は schema migration と既存 terminal contract の再裁定が必要。本推奨は historical reader 互換を優先し、未実測の新規受理枝だけを増やさない解釈です。