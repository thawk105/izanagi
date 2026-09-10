# fix Unit B 報告

## 1. 所見ごとの対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F-B1 | partial | ticket marker と attempt ledger の durable 成功後にだけ token を発行。許可回数は canonical protocol の `reps` に固定。正式 pytest 未実走。 |
| F-B2 | partial | core の 4 gate 注入引数を削除。既存 campaign harness を一時 Git authority＋実 claim／ledger／ticket 経路へ変更し、meta-test を追加。 |
| F-B3 | partial | public pilot／official の全 caller callable seam を列挙して事前拒否。 |
| F-B4 | partial | cell claim を環境・予約・clean scan・perf・build・manifest preflight 後、`runner.run()` 直前へ移動。安全根拠を docstring に記載。 |
| F-B5 | partial | caller の journal bool／manifest hash を API から削除。admission が実 run directory、manifest bytes、journal、resume state、terminal、retry trigger を検証。 |
| F-B6 | partial | `--confirm-irreversible-pilot-holdout` を追加。既定拒否とし、承認を claim／ledger row に記録。 |
| F-B7 | partial | CLI の `--protocol` path 固定を削除。broken freeze の既存構造化エラー診断は direct 実行で維持を確認。 |
| F-B8 | partial | consumer test の呼び先を private core＋実 admission authority へ変更。clocks／NUMA の assert は維持。 |
| F-B9 | partial | repo の実 canonical protocol／freeze bytes を一時 Git repoへ複製し、claim→ledger→marker→`run_once` spy を通す E2E を追加。 |
| F-B10 | partial | 指定された constructor 1 箇所に `attempt_id` と `permitted_run_once_calls` を追加。拒否期待は不変。 |

すべて正式 pytest が collection 前 `rc=16` で停止したため、`closed` とはしていません。`regressed` はありません。

## 2. 変更した file と要点

- [s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_holdout_admission.py:583)
  - 実 manifest／journal 検証、terminal／retry trigger 拒否。
  - finalize 時の先行 observation token 発行を削除。
  - attempt durable 消費後の private receipt 結線。
  - pilot 不可逆承認の ledger 記録。
- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:4153)
  - public callable seam 全拒否。
  - 4 gate seam 削除と claim 遅延。
  - pilot 承認 flag、CLI protocol path 固定削除。
- [test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_holdout_admission.py:180)
  - M4／M5、実 resume bytes、terminal、retry trigger、承認記録、canonical E2E。
- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_floor_campaign.py:3073)
  - no-op admission harness を実 Git authority harness へ変更。
  - seam meta-test、pilot callable 全列挙、claim 順序検査。
  - Unit A の exact neutral API に合わせ、fixture identity を rr80／rr20 へ変更。TPS、件数、判定理由は維持。
- [test_s8b_freeze_io.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_freeze_io.py:212)
  - 対象 consumer を private core＋実 admission 経路へ変更。
- [test_holdout_observation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_holdout_observation.py:374)
  - F-B10 の指定箇所だけ修正。

docs と所有外コードは編集せず、commit も作成していません。

## 3. production entrypoint に残した seam の全列挙と、それが検査を無効化しない根拠

public `run_campaign` に残る callable 引数は次のとおりですが、pilot／official とも非 default 値を core 進入前に拒否します。

`measure_fn`、`probe_fn`、`sleep_fn`、`monotonic_fn`、`prepare_fn`、`now_fn`、`host_provenance_fn`、`process_identity_fn`、`execution_receipt_fn`、`build_fn`、`after_certificate_issued_fn`、`perf_preflight_fn`

private test core の解決 seam は次の 2 つです。

- `_holdout_repo_root`: 共有 durable root と canonical HEAD artifact の場所だけを変更。authority、claim、ledger、ticket、identity 検査はすべて実行。
- `_floor_preflight_fn`: official freeze allowlist の解決だけを変更。holdout admission 関数は置換しない。

`_holdout_reserve_fn`、`_holdout_finalize_fn`、`_holdout_assert_fn`、`_attempt_consume_fn` は core signature から削除済みです。

`confirm_irreversible_pilot_holdout` は gate 無効化 seam ではなく、pilot の不可逆消費を明示承認する exact bool です。承認後も全 claim／ledger／ticket 消費を行います。

## 4. 実走したテスト / 実走できなかったもの

`tools/run_tests.py` 経由で次を 1 file ずつ投入しました。

- `orchestrator/tests/test_s8b_holdout_admission.py -q`
- `orchestrator/tests/test_s8b_floor_campaign.py -q`
- `orchestrator/tests/test_s8b_freeze_io.py -q`
- `orchestrator/tests/test_holdout_observation.py -q`

全件とも次で collection 前停止しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
runner exit_code=16
```

実走 pytest nodeid は 0 件です。緑は主張しません。

非 pytest の限定 direct 診断では次を確認しました。

- M4 parallel fresh claim: `DIRECT_OK`
- M5 crashing callback 前消費: `DIRECT_OK`
- fresh／resume／terminal／retry trigger admission: `DIRECT_OK`
- canonical authority→claim→ledger→marker→`run_once`: `DIRECT_OK`
- 96 session campaign happy path、running resume、finalize-pending: `DIRECT_OK`
- default `measure_point` token 結線、freeze_io consumer、F-B10: `DIRECT_OK`
- public callable seam／approval／meta-test、broken-freeze CLI: `DIRECT_OK`
- 6 file AST、NFC、結合文字不在、`git diff --check`: 成功
- `tools/check_codex_agents.py`: 成功
- `tools/check_docs.py`: 違反なし

これらは pytest 結果には数えていません。

## 5. 事前登録変異 M4/M5 の位置・old 逐語・前後層確認

- M4: [s8b_holdout_admission.py:382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_holdout_admission.py:382)

  old: `flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL`

  cell claim 呼び出しは同ファイル 743 行の `_write_exclusive(path, claim)`。同 key の並行 fresh reserve は authority、artifact、cell、schedule 検査を双方通過し、ledger finalize 前なので、他層は先に拒否しません。実効拒否は claim の `O_EXCL` です。

- M5: [s8b_floor_campaign.py:3260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:3260)

  old:

  ```python
  observation = consume_ticket_fn(
      admission, attempt_id=attempt_id,
  )
  ```

  この block は external callback の直前です。前段の cell／座標 assert は ticket を消費せず、M5 テストの external 4 引数 callback は `run_once` gateway を通らないため、消費を callback 後へ移すと crash 前に marker が残らず同一 attempt を再実行できます。後段にも重複を先に拒否する層はありません。

正式 mutation harness は親担当のため未実走です。

## 6. 所有外への波及可能性

- `tools/pegasus/floor_campaign.sh` は現在、新しい承認 flag を渡していません。このままでは安全側に pilot が拒否されます。不可逆承認を wrapper が自動付与すべきではないため、所有外 caller 側で人間承認の伝播設計が必要です。
- 対応する consumer は `orchestrator/tests/test_pegasus_floor_tools.py` です。
- public `run_campaign` へ callable seam を渡す所有外 caller があれば、pilot でも拒否されます。静的検索では指定所有外に直接呼び出す production Python site は見つかりませんでした。
- admission API の旧 bool／manifest hash signature を直接使う所有外 caller は見つかりませんでした。
- module import consumer として `test_s8b_materialization.py`、`test_s8b_floor_contract.py`、`test_s8b_approved.py`、`test_s8b_protocol_builder.py`、`test_s8b_ratified_freeze.py` があり、親の統合受入対象です。

## 7. 未完・申し送り

- pytest と mutation harness は未実走です。親環境で 4 file を個別再投入してください。
- `test_pegasus_floor_tools.py` と PBS wrapper の新 approval flag 伝播は所有外です。
- campaign fixture の holdout identity は、実 admission が Unit A の exact neutral 集合を要求するため rr80／rr20へ変更しました。数値・件数・理由の期待は維持しています。
- official mode の既存拒否は変更していません。
- docs、commit、Unit A 所有ファイルは変更していません。

## 総括

F-B1〜F-B10 の実装とテスト結線を所有範囲内へ反映しました。  
claim／ledger／ticket／`run_once` の proof chain は限定 direct E2E で通過しました。  
production core から 4 gate seam を削除し、pilot callable seam と不可逆承認を fail-closed にしました。  
正式 pytest は Pegasus dispatch `rc=16` で未実走のため、全所見を partial としています。  
所有外では PBS floor wrapper への承認 flag 伝播が残ります。