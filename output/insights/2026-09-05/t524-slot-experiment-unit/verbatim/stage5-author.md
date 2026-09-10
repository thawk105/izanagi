## 実装した内容

- [attempt_registry_core.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-author/orchestrator/campaign/attempt_registry_core.py:730): v3 root の全 slot が単一の正整数 `prereg_generation` を持つことを検査。汎用化を避け、8c schema 専用条件として 29 行だけ追加しました。
- [trial_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-author/orchestrator/campaign/trial_registry.py:66): attempt registry を v3 化。v1/v2/v3 を明示 map で読取可能にし、series key は変更していません。
- [trial_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-author/orchestrator/campaign/trial_registry.py:2464): creator に必須引数を追加し、全 slot との exact 一致を要求。自動補完はありません。
- [trial_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-author/orchestrator/campaign/trial_registry.py:6192): v3 slot projection を生成し、attempt path・prefix bytes/hash・generation・全 unit・個数を v5 receipt へ格納。
- [s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-author/orchestrator/campaign/s8c_acceptance_receipt.py:30): outer receipt を v5 化。v1〜v4 の読取互換を維持。
- [s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-author/orchestrator/campaign/s8c_acceptance_receipt.py:1503): attempt prefix を独立 replay し、genesis 由来の非空期待集合と final terminal を照合。`observed` / `terminal-failure` のみ数え、`retryable-failure` と `not-consumed` は final に数えません。
- [test_trial_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-author/orchestrator/tests/test_trial_registry.py:6448) と [test_s8c_acceptance_receipt_v2.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-author/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:975): M1〜M3、P1〜P2、v2/v4 互換、capability digest 世代束縛を追加。
- 指定された残りの fixture/test も schema v3/v5 へ機械追随しました。docs、指示ファイル、g1〜g13 は無変更です。commit/push もしていません。

## 実走したテスト

pytest は実装済み・未実走です。次の nodeid を `tools/run_tests.py` へ渡しましたが、全て `child_started=false` でした。

- `test_trial_registry.py::test_m1_v3_reader_accepts_single_generation_and_rejects_mixed_generation`
- `test_trial_registry.py::test_m2_genesis_creator_requires_exact_slot_generation`
- `test_trial_registry.py::test_attempt_registry_v2_reader_remains_explicitly_mapped`
- `test_trial_registry.py::test_v3_capability_digest_binds_generation_without_receipt_duplication`
- `test_s8c_acceptance_receipt_v2.py::test_v5_attempt_binding_accepts_all_predeclared_observed_units`
- `test_s8c_acceptance_receipt_v2.py::test_m3_v5_rejects_predeclared_unit_without_final_terminal`
- `test_s8c_acceptance_receipt_v2.py::test_p1_v5_accepts_observed_and_terminal_failure_mix`
- `test_s8c_acceptance_receipt_v2.py::test_p2_v5_accepts_retryable_failure_followed_by_next_attempt`
- `test_s8c_acceptance_receipt_v2.py::test_v4_remains_readable_without_v5_attempt_binding`

制約 meta-test として `--collect-only -q orchestrator/tests` も投入しましたが、同じ理由で未実走です。

実走済みの検査:

- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- 変更 10 ファイルの AST parse: OK
- `git diff --check`: OK

## 赤の内訳

pytest assertion の赤は 0 件です。テストプロセス自体が起動していません。

全 runner 投入は Pegasus dispatch の `qstat -Q preflight rc=1`、`rc=16` で終了しました。直接確認した原因は `NQSconnect: Can't create socket (errno: 1)` です。login local 経路も予約台帳を安全に更新できず使用不可でした。

## 現行の受理・拒否挙動の変化

変更前は v2 genesis に generation がなく、v4 verifier は attempt registry を参照しない receipt を検証できました。

変更後は次のようになります。

- v3 genesis は generation 欠落・非正整数・root 内混在を拒否。
- creator 引数と全 slot の generation 不一致を拒否。
- v1/v2 は読取可能ですが、新しい formal v5 発行には使用不可。
- v5 は attempt registry の欠落、prefix 不一致、projection 不一致、空集合、unit の final 欠落・重複、report hash/status 不一致、`replicate_index > 0` を拒否。
- 単一 generation の全 unit 消費、`observed` / `terminal-failure` 混在、retryable failure 後の次 attempt 正常終端は受理対象です。
- v4 以前の verifier 受理条件は維持しています。静的監査上、意図しない受理集合の拡大はありません。

## 所有外への波及

- production の genesis caller は依然 0 件です。out-of-band caller は必須引数と slot field の追加が必要です。
- 既存 v2 root は読取専用となり、新しい v3 event の追記や v5 発行はできません。
- generation を含むため capability digest と、それを束縛する classification receipt hash は変化します。
- `p3_autonomous_workload_trial.py` は capability に追加された field を受け取りますが、新しい分岐はありません。
- `layer3_report.py` など未編集 consumer は optional な parsed receipt field の追加影響を受ける可能性があります。
- `test_attempt_registry_core_equivalence.py`、S8B profile、P3 workload、reflux 2 系統は fixture 追随済みですが pytest 未実走です。

## 総括

実装は完了していますが、pytest 未実走のため全体として未完了です。  
M1〜M3 はそれぞれ対象述語だけを外した際に通る入力形へ分離しました。  
P1・P2と旧 v2/v4 互換テストも実装済みです。  
repository checker と静的検査は通過しています。  
親でテスト実行可能な環境から、記載した nodeid と影響 7 ファイルの全走が必要です。