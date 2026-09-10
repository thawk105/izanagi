## 総括

- 実装:
  - [`tools/spool_fold.py:445`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:445): `完了` item 末尾の可視な機械 field 群で exact-one `remaining: none` を検査し、canonical 出力から除去。
  - [`tools/spool_fold.py:354`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:354): fence／HTML comment を不可視化する tokenizer を追加。
  - [`tools/spool_fold.py:516`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:516): `見送り追記` の一行 item parser と `_DeferredAppend` を追加。
  - [`tools/spool_fold.py:1391`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1391): 可視な見送り台帳項目を索引。
  - [`tools/spool_fold.py:1444`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1444): 先頭行末への byte-exact 追記と重複 suffix 拒否を追加。
  - [`tools/spool_fold.py:1754`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1754): fragment 順の逐次適用を実装。先行 fragment／同一 fragmentで新規見送りにした項目にも追記可能。
  - `_strip_base` と `_insert_deferred` の既存契約・実装は変更していない。

- 新設 error ID:
  - `completion-remaining-field`
  - `deferred-append-empty`
  - `deferred-append-shape`
  - `deferred-append-missing`
  - `deferred-append-duplicate`
  - `deferred-append-duplicate-suffix`

- 受理・拒否差分:
  - 従来は、正しい `base:` と禁制語不在だけで未完了を示す散文も `完了` として受理した。変更後は可視な末尾 field 群の `remaining: none` が必須。
  - fence／comment 内や本文途中の decoy は field・見送り対象として数えない。
  - `更新`／`見送り` の `remaining` 要件、既存禁制語 `completion-remaining`、active 保存則は不変。
  - 従来未知 action だった `見送り追記` を、末尾 action として限定受理する。
  - 未 fold の既存 fragment 5 件は再確認し、`更新`／`新規` のみで `完了` はなかった。

- 検査:
  - `python3 -m py_compile tools/spool_fold.py`: rc=0
  - `git diff --check -- tools/spool_fold.py`: rc=0
  - pytest、`check_docs.py`、land、動的 error probe は走らせていない。`pegasus02` ログインノードのため dispatch 迂回も試みておらず、テスト緑は主張しない。
  - 各新 error ID が第一失敗になる最小入力への到達性は制御フロー上で静的確認した。

- 静的波及:
  - `tools/check_docs.py`: `validate_spool_tree` の動的 import を通じて新 finding が伝播する。tokenizer は仕様どおり spool 側へ同型実装。
  - `tools/dev_wave_land.py`: `plan_fold`／`apply_fold` の既存動的 importと `docs/phase3.md` transaction targetをそのまま利用可能。
  - `hooks/`: spool grammar consumer はなく変更不要。Codex hook は未配線なので、編集境界は手動で遵守。
  - worker B 所有の `orchestrator/tests/test_spool_fold.py` に共有 worktree 上の変更を確認したが、自分は編集していない。

- 仕様と実装の既知のずれはない。動的検証と byte-exact oracle、decoy、逐次意味論、cross-ledger placeholder、決定順の確認は worker B／親の計算ノード実走待ち。
- docs、tests、`output/` は編集せず、stage／commit も行っていない。dev-wave 契約に従い、自分の編集は `tools/spool_fold.py` のみに限定した。