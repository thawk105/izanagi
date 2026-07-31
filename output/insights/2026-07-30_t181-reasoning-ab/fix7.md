## 総括

指定された2件のみ修正しました。

- `MAX_INTER_BLOCK_GAP_MS = 900_000` を導入しました。親の実測350,980 msに対して約2.56倍の余裕を持たせています。同一 block・同一 attempt の `block_order 1 → 2` は従来どおり60,000 ms、block/pair 境界は900,000 msです。逆順・overlap拒否と `previous_exit_to_start_gap_ms` の記録は維持しています。[実装](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1519)
- manifest は `max_schedule_gap_ms` と `max_inter_block_gap_ms` の両方を検証し、片方の欠落・driftでも fail-closedになります。[replay検証](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4217)
- timing node は `test_intra_block_timing_large_gap_is_rejected`、`test_inter_block_timing_350980_ms_is_accepted`、`test_inter_block_timing_above_bound_is_rejected` を整備し、既存の逆順拒否 node も維持しました。[テスト](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1309)
- M6/M6p 用に `test_m6_verdict_packet_swap_restore_digest_layers_are_redundant` を追加しました。packet本文を交換して二読者の verdict を記録・freezeし、その後本文を復元する系列を作り、現行二層では拒否、読取時層だけ無効でも拒否、両層無効では逆帰属が受理されることを固定しています。指定されたDW-M04 docstringも付与しました。[M6/M6p node](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2408)
- 旧M6名目 node は実態に合わせて `test_reader_disagreement_is_conservative` へ改名し、冒頭のmutation node表は新しいswap→restore nodeへ張り替えました。[改名node](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2494)

`python3 -m py_compile` と `git diff --check` のみ実行し、いずれもrc=0でした。ユーザー指示に従いpytest、実snapshot build、`supervise-pair`実走、外部cloneは未実行であり、テストの緑は主張しません。波及可能性として、親が作るmanifestには新しいinter-block pinが必須となり、旧形式manifestは意図的に拒否されます。編集は指定されたコード・テストの2ファイルだけで、docs編集・commitは行っていません。