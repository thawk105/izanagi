実装は完了しました。ただし Pegasus の PBS user mapping エラーにより pytest は開始できず、テストの緑は未確認です。commit は作成していません。

変更内容:

- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:384)
  - lock を1回だけ読み、同じ `lock_raw` から hash・parse・分類・snapshot照合・receiptを生成。
  - `_is_legacy_trigger_lock()` を追加。形状を限定せず trigger axis のみを判定。
  - 歴史 trigger の `classification` を維持し、status のみ `legacy-unclassified` に変更。
- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:56)
  - 7ケースの真理値表。
  - path・lock/WAL SHAを固定した旧 trigger 6件。
  - 現在 admitted な非trigger歴史 campaign 21件の明示 literal。
- [test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_layer3_report.py:262)
  - 代表 sweep から Layer3 report を発行できず、出力も残らない検査。

受理挙動は以下です。

| 対象 | 変更前 | 変更後 |
|---|---|---|
| 旧 trigger sweep 6件 | 歴史分類、admitted | 歴史分類のまま `legacy-unclassified`、raw view／新規Layer3拒否 |
| overlay 3件 | `overlay-denied` | 不変 |
| 非trigger歴史 campaign 21件 | admitted | 不変 |
| post-policy campaign | 既存検証に従う | 不変 |
| snapshot不一致・未知receiptless | 拒否 | 不変 |

overlay 枝は引き続き lock/WAL hash の exact membership のみで判定し、新 helper を参照しません。lock hash の入力が1回取得した bytesになっただけで、membership集合・分類・statusは変わりません。

静的に確認した波及先は、`critic/digest.py`、`replay.py`、`layer3_report.py`、`p3_s4_{loop,loop_sort,red}.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`autonomous_trial_completeness.py` です。共有fixture／consumer testでは `test_critic.py`、`test_bench_first_real_wal.py`、`test_p3_s4_loop*.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`、`test_autonomous_trial_completeness.py` が影響候補です。実際に挙動が変わるのは旧 trigger 6件を渡す経路だけです。

検査結果:

- `python3 -m py_compile`（変更3ファイル）: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- 追加4 nodeid の dispatch: rc=16、テスト未開始
- 関連2ファイル全体＋`test_plain_runner_coverage.py`＋`test_pytest_collection_config.py`: rc=16、テスト未開始
- 原因: `qstat -Q` が `Unknown user-id (uid: 31609)` で失敗

新D不在を参照する依存は対象テスト上では静的に見つからず、`check_docs` も通りました。ただし pytest 未実行のため、実測上の保証ではありません。

変更中に所有外の `docs/spool/decisions/2026-08-05-dev-wave-t474-legacy-trigger-admission-1.md` が untracked として出現しました。これは編集・削除していません。HEAD は `55c2e84` のままで、指定された保護対象・`output/`・その他docsには触れていません。

## 総括

- 実装: lock read-once化と、旧trigger歴史artifact 6件の admission拒否を実装。overlay・post-policy・非trigger歴史集合は維持。
- 検査: 構文・diff・Codex agent・docs検査は成功。pytestとmeta-testはPBS preflight rc=16で未実行。
- 残るrisk: 対象／consumerテストの実測が必要。事前登録M8のABA検出力不足、WAL側ABA、post-policy機械sweep membership穴は裁定どおりscope外です。