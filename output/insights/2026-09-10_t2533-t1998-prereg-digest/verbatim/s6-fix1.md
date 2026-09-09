## 前提と読んだ資料

指定された一次資料 6 件はすべて全文読了した。

- `s4-adjudication.md`
- `AUTHORITATIVE-VALUES.md`
- `s6-lensA.md`
- `s6-lensB.md`
- `s5-author.md`
- `verbatim/D1790.md`

指定 worktree だけを読み書きし、親 checkout・他 worktree・`docs/**`・所要時間台帳には触れていない。

## F1〜F4 の対応

- F1: [t1998_stock_inline_pair.py:1296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-fix1/orchestrator/campaign/t1998_stock_inline_pair.py:1296)
  - artifact 比較後、ratio 計算直前のまま、gate を current SHA → measurement blob SHA → measurement blob 由来 identity の順へ変更。
  - identity は現行文書ではなく `repository_commit` の blob から導出する。
  - 既存 code・field と launcher 拒否 provenance は維持。

- F2: [t1998_stock_inline_pair.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-fix1/orchestrator/campaign/t1998_stock_inline_pair.py:347)
  - `patchharness.py` の先例と同型の Git 環境正規化を追加。
  - 既存 2 呼出しで repository/object/worktree/index 関連の `GIT_*` を除去し、`GIT_OPTIONAL_LOCKS=0` と `--no-replace-objects` を指定。

- F3: [test_ccbench_spawn_sites.py:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-fix1/orchestrator/tests/test_ccbench_spawn_sites.py:267)
  - `_preregistration_blob` と `load_preregistration` の 2 site を exact inventory に追加。
  - 走査除外・件数緩和などは行っていない。

- F4: [test_t1998_stock_inline_pair.py:510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-fix1/orchestrator/tests/test_t1998_stock_inline_pair.py:510)
  - 実文書 bytes と contract-loader 閉包をコピーする一時 Git repo fixture を追加。
  - consumer に任意のテスト repo を渡せる keyword-only `repo_root` を追加。既存呼出しは未変更。[t1998_stock_inline_pair.py:941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-fix1/orchestrator/campaign/t1998_stock_inline_pair.py:941)

## 追加・変更したテスト

- `test_current_preregistration_sha_mismatch_is_rejected`
  - [test:715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-fix1/orchestrator/tests/test_t1998_stock_inline_pair.py:715)
  - measurement blob は正本のまま、作業木 bytes だけを変え、current SHA 比較を単独で殺す。

- `test_measurement_preregistration_sha_mismatch_is_rejected`
  - [test:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-fix1/orchestrator/tests/test_t1998_stock_inline_pair.py:748)
  - 文書が存在し bytes だけが異なる commit を使用し、measurement SHA 比較を単独で殺す。

- `test_parse_preregistration_rejects_duplicate_key`
  - [test:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-fix1/orchestrator/tests/test_t1998_stock_inline_pair.py:801)
  - 実文書から重複行を生成して private parser を直接呼び、重複 key 拒否を単独で殺す。

二定数の不等性を要求するテストは追加していない。

## 実走した検査

- `python3 tools/run_tests.py -q -rf orchestrator/tests/test_t1998_stock_inline_pair.py orchestrator/tests/test_ccbench_spawn_sites.py`
  - `rc=16`、`child_started=false`、`qstat -Q` preflight 失敗。
  - 両ファイルの全 nodeid は pytest 未実走。生成された dispatch receipt 一式は除去済み。

- pytest ではない test 関数直接呼出し: 成功
  - 追加 3 nodeid
  - process inventory 2 nodeid
  - 既存正例、launcher provenance、document identity、missing blob、loader 正負例の 6 nodeid

- pytest ではない自走確認: 成功
  - current と measurement の identity が異なる二版分離ケース
  - 7 種の Git 環境汚染下での `load_preregistration`
  - `git diff --check`
  - 3 所有ファイルの `compile(...)` 構文確認

- `python3 -m ruff check ...`
  - `ruff` 未導入のため未実走。

## 受理・拒否挙動の変化

- 二版分離後は、measurement blob が登録していない current identity を渡す入力を `preregistration-identity-mismatch` で拒否する。
- 反対に、正しい measurement identity は current 文書の identity が改訂済みでも受理できる。
- 作業木 drift と存在する measurement blob の byte drift は、それぞれ既存 SHA code/field で拒否する。
- ambient `GIT_*` や replace ref による別 repository 参照はできなくなった。
- 現行 v1 の二定数は同値なので、正本入力の受理挙動は変わらない。
- 既存 launcher 負例は従来どおり `launcher-script-identity-mismatch` / `reservation.binding.script_sha256`。

## 所有外への波及

- 最終変更は指定された 3 ファイルのみ。
- `docs/**`、`orchestrator/tests/acceptance_duration_ledger.json`、`tools/**`、`patches/**`、`external/**` は未変更。
- consumer の既存 caller は変更不要。新引数の既定値は従来の repo root。
- commit、push、branch 操作、`git add` は行っていない。

## 総括

F1〜F4 の実装と単独負例を作業木へ反映した。  
identity は測定時点 blob に正しく束縛され、Git 参照環境も固定された。  
process 起動 exact inventory の既知 2 赤要因は直接確認で解消した。  
pytest は dispatch infrastructure の `rc=16` により未実走であり、closed とは申告しない。