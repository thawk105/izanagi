## 変更

- [tools/t2273_replica_analyze.py:810](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:810): A/P の builder を key だけで対応付け、初回要求 test の nodeid は出力に保持しました。同じ key の複数 builder には各々 digest を要求し、key ごとに digest 値が一意かを検査します。
- [tools/t2273_replica_analyze.py:943](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:943): 資源欠測が `lustre: no readable llite/*/stats` だけの場合に限り、理由を付けて `excluded_structural_missing` に出すようにしました。

## 自己検査

- `python3 -m py_compile tools/t2273_replica_analyze.py`: 成功。
- job 1 の実データを `python3.10 ... --ab-dir ... --json /tmp/t2273-fix2-j1.json` で再解析: `validity.valid=true`、`failed=[]`。`checks` は `rc`, `outcomes_equal`, `record_error_zero`, `clean`, `same_HEAD`, `others_zero`, `builder_keys_equal`, `one_builder_per_key`, `stat_digest_equal`, `visible_digest_equal`, `ready`, `ready_visible_matches_A`, `precopy_source`, `copy_wait_spans`, `publish_phases`, `argv_env_equal`, `separate_sessions`, `intervention_env`, `memo_no_overrun`, `required_observations` の全項目が `true`。
- 一時 fixture: 同 key・別 nodeid は有効、file digest の差は `stat_digest_equal=false`、llite 以外の資源欠測は `required_observations=false`。`git diff --check` も成功。

## 総括

E1 の 2 点を `tools/t2273_replica_analyze.py` のみで修正しました。job 1 は再解析で有効となり、失敗項目はありません。runner・plugin は変更していません。