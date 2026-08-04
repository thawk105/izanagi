## 変更した file と行

- [tools/ruleops.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:25)
  - schema v2 化。
  - 663 行付近に skip counter、691 行付近に root key を追加。
- [orchestrator/tests/test_ruleops.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:52)
  - root key 集合、bytes fixture、408 行以降にテスト 6 本を追加。
  - item key 集合は変更していない。

`git add`、commit、docs 編集、ファイル削除は行っていない。

## 実装の要点 (gate 署名をどう守ったか)

変更前は selected regular blob の一つでも strict UTF-8 decode に失敗すると inventory 全体が rc=2 だった。変更後は次の契約になった。

- kind filter 適用後の `selected` 内だけを走査。
- `raw.decode("utf-8", "strict")` が `UnicodeDecodeError` を送出した path だけを除外。
- path/item 単位で `skipped_non_utf8` を加算し、0 の場合も整数で出力。
- suffix、path 名、JSON/Python 妥当性、NUL、size による除外を追加していない。
- `_batch_blobs` → `_last_changes` の呼び出し順は維持。
- retained item の key・値・順序生成は維持。
- `inspect`、`_strict_json`、receipt、ledger/check、insight candidate の strict decode は未変更。

裁定の採用項目 #1〜#7 はテストへ反映した。#8・#9・#11 は親所有の docs／decision／brief、#10 は段9 land 時の採番事項なので、編集禁止境界に従って触れていない。

## 追加したテストと固定した内容

- `test_inventory_non_utf8_skip_matrix_and_utf8_formats`
  - direct test `.py` と insight `.py/.md/.json/.raw/.sh` の content matrix。
  - 不正 bytes は6セルすべて異なる。
  - path は中立名。
  - Latin-1 coding cookie 付き direct test が Python として compile 可能なことを確認。
  - UTF-8 control の5形式、BOM JSON、NUL入り raw、UTF-8だが不正なPython、空のshellを保持。
  - schema、root/item exact keys、skip件数、membershipを固定。
- `test_inventory_non_utf8_counter_respects_selected_kind`
  - `all/test/insight == 6/1/5` を固定。
- `test_inventory_non_utf8_counter_tracks_same_path_content_transition`
  - 同一 path を非UTF-8→UTF-8+NUL→非UTF-8へcommitし、selected総数を保ったまま counter とmembershipが反転することを固定。
- `test_inventory_non_utf8_counter_excludes_out_of_scope_and_nonregular`
  - zero case、scope外 blob、scope内symlink/gitlinkの非計上を固定。
- `test_inventory_all_selected_non_utf8_succeeds_and_counts_paths`
  - rc=0、`items == []`、件数Nを固定。
  - 同一blob OIDを持つ複数pathも個別に数えることを固定。
- `test_inspect_non_utf8_target_fails_closed_without_traceback`
  - rc=2、`non-utf8`、stdout空、Tracebackなしを固定。

## 走らせた nodeid と結果 (走らせていないものは走らせていないと書く)

- `python3 -m py_compile tools/ruleops.py orchestrator/tests/test_ruleops.py`
  - rc=0。
- `git diff --check`
  - rc=0。
- `python3 tools/run_tests.py orchestrator/tests/test_ruleops.py -x -q`
  - 2回試行したが、いずれも collection 前に rc=16。
  - `qstat -Q preflight rc=1`。直接確認では `EACCTAUTH Unknown user-id (uid: 31609)`。
  - したがって同ファイル内のnodeidはすべて未実走で、緑は主張しない。
- `python3 tools/run_tests.py orchestrator/tests/test_plain_runner_coverage.py -q`
  - 同じdispatch基盤障害でcollection前 rc=16。全nodeid未実走。

Pegasusログインノード上での直接pytestは禁止されているため迂回していない。受入全走も親担当であり未実施。

## 波及可能性 (所有外 caller、共有 fixture、consumer test)

- 所有外のPython callerは静的検索では見つからなかった。直接callerは同じ `tools/ruleops.py` のCLI `main`。
- `docs/ruleops.md` は現在v1記述で、親によるv2更新が必要。
- 共有 `_base_repo` は変更していない。新matrix fixtureは独立追加。
- `_INVENTORY_ROOT_KEYS` を共有する既存のliteral-scope testとreal-checkout consumerは、新しい5-key形を要求する。
- `test_plain_runner_coverage.py` はテストファイル単位のconsumer。
- `tools/run_tests.py` のRuleOps preflightは `check` 経路のみで、今回変更していない。
- 凍結insightと歴史資料には接触していない。

## 残る赤とその理由

テスト由来の赤は観測していないが、pytest自体が未実走である。残件はPegasus dispatchの認証障害による未検証状態であり、親環境から上記2コマンドを再実行する必要がある。

## 総括

指定2ファイルだけを変更し、inventory v2、selected path単位の非UTF-8 skip counter、裁定されたmatrix・因果・境界・inspect負例を実装した。静的構文検査とdiff検査は成功したが、pytestは計算ノードdispatch障害のため未実走である。