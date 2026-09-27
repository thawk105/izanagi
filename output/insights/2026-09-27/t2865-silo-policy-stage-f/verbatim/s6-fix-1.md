## 変更 file と要点 (file:line、F1〜F6 との対応)

- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/campaign/p3_s4_loop_policy.py:343): F2。同じ attempt の WAL に stock genome の variant と `BUILD_START.src_token=STOCK` がある場合だけ `certified-stock` と判定。
- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/campaign/p3_s4_loop_policy.py:609): F1・F3・F5・F6。環境の prefix を明示引数へ写さず、計測ログを stderr に出力。stock 不成立と候補未実走の pair は JSON 出力後 rc=1。
- [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/tests/test_p3_s4_loop_policy.py:489): F4。実 source テストの compiler 選択を `find_compiler()` に変更。既存の assert は維持。

## test の実走 (または未実走)

**実装済み・未実走。** `python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop_policy.py` は `qstat -Q` 事前確認で rc=16 となり、子テストは開始されませんでした。構文解析、`git diff --check`、`check_codex_agents.py`、`check_docs.py` は rc=0。pytest の緑は主張しません。

## 変異 M-F9〜M-F12 の fixture と単一理由性の見立て

- M-F9: 同じ variant の別 attempt に STOCK、選択 attempt に非 STOCK を置く WAL fixture。token 照合を外すと outcome の assert だけが落ちる。
- M-F10: stock 不成立の JSON と rc=1 を検査。rc を常時 0 にすると rc の assert が落ちる。
- M-F11: 候補 `ran=False` で stock 呼出しを失敗扱いにする fixture。stock を起動する変異でその検査が落ちる。
- M-F12: `CMAKE_PREFIX_PATH=/a:/b` で実際の `_run_measurement` を通し、`run_campaign` の kwargs を検査。明示 prefix を復活させると kwargs の assert が落ちる。

単一理由性は静的な見立てであり、変異の実走確認はできていません。

## 所有外への波及

呼出し元の job body [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/tools/pegasus/p3_s4_loop_pegasus.sh) と consumer 検査 `test_p3_s4_loop_job_contract.py`、`test_p3_build_authority_cli.py`、`test_p3_exploration_namespace.py`、`test_campaign.py`、`test_official_perf_closure.py` に静的な波及があります。所有外ファイルは編集していません。preview・record-reject・emit と、候補の gate 拒否時の rc は変更していません。

## 総括

F1〜F6 を所有する 2 ファイルに実装しました。commit は作成していません。テストランナーの dispatch 障害により、pytest と変異の実走確認が残っています。