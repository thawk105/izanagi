## 総括

- 許可された 4 file だけに A1〜A7 を実装した。
- A3 は祖先 directory だけの選択的正規化を採用した。
- AST parse、`git diff --check`、Codex agent checker、docs checker は成功した。
- pytest は dispatch infrastructure failure、rc=16 で child 未起動のため未実走。
- 必須の tracked-descendant 検査が、現行 HEAD の ignored prefix 配下にある tracked 418 files を検出する。
- この所有外状態を解消するまで snapshot consumer 群は fail-closed になる。
- `git add`、commit、stash、branch 操作は行っていない。

## 変更した file と行

- [output_snapshot_ignores.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/output_snapshot_ignores.py:11): A1/A2 の規則解析、Git 判定、祖先集合。
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/test_s8b_oracle_driver.py:560): A3〜A6 と A1/A2 contract。
- [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/test_real_repo_serialization.py:542): A3〜A7。
- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/test_s8b_floor_campaign.py:1573): A4/A5。

## A1 の実装

変更前は、実在する ignored path を `git ls-files` で列挙し、exact prefix またはその子孫だけを除外していた。したがって非実在の `runs` は返らなかったが、`runs-visible` は可視だった。

変更後は次を実装した。

- `.gitignore`、`git rev-parse --git-path info/exclude`、`git config --get core.excludesFile` の規則 bytes だけから候補を生成。
- negation、`**`、escape、対象外の静的 prefix を候補から除外。
- directory 規則の問い合わせには末尾 `/` を維持。
- `git check-ignore --no-index --stdin -z` を rc=0、rc=1、その他に分岐し、NUL 出力と入力部分集合を検証。
- 従来の `git ls-files` 結果と和集合化。wildcard は実在後だけ取得する従来契約を維持。
- 規則由来 prefix ごとに tracked descendant を検査して fail-closed。
- `output/` 全体 ignore の拒否を維持。
- `runs-visible` を隠さない component 境界も維持。

## A2 の実装

[祖先集合](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/output_snapshot_ignores.py:255)を `exact` と `subtree_roots` で公開した。

- root `.` は常に exact。
- literal `runs` は root だけを祖先化。
- nested literal は厳密な親だけを祖先化。
- `variants/*/bin` は `variants` を subtree root とし、配下の全 directory を祖先扱い。
- tree の列挙や存在確認は使わず、規則候補と末尾 `/` 付き Git 判定だけから導出。

## A3 の実装 (選択的正規化を採ったか、一律へ退避したか)

選択的正規化を採用した。一律正規化への退避はしていない。

2 個の `_t080_output_snapshot` で、`lstat()` の mode が directory かつ A2 の祖先集合に属する場合だけ、size、mtime、ctime を `None` にする。mode は保持し、regular file と symlink の全 metadata、祖先でない directory の timestamp は保持する。

docstring も「Git-visible entry と、非 ignore 祖先での一時作成後削除を捉える」契約へ更新した。

## A4 / A5 / A6 / A7 の実装

- A4: 3 negative control の baseline を `runs` 作成前へ移動。
- A5: 3 file に `runs-visible/nested/payload.bin` の positive control を追加。
- A6: 2 file に非祖先 directory 直下の Git-visible create-and-delete control を新設。
- A7: 実 xdist probe と同じ worker hook source を pluggy harness に接続。decorator 除去と記録の yield 後移動が、どちらも worker-first 検査を通らない control を追加。
- 既存の worker payer 合成負例は維持した。

## 実走したか (nodeid と範囲、または「実装済み・未実走」)

**実装済み・未実走。**

次の 4 node を `tools/run_tests.py` で名指ししたが、`qstat -Q preflight rc=1`、runner rc=16、`child_started=false` で 1 node も起動しなかった。

- `test_s8b_oracle_driver.py::test_git_ignored_output_prefixes_uses_rule_sources_before_paths_exist`
- `test_s8b_oracle_driver.py::test_git_ignored_output_prefixes_rejects_tracked_rule_descendant`
- `test_s8b_oracle_driver.py::test_git_ignored_output_prefixes_rejects_entire_output_ignore`
- `test_real_repo_serialization.py::test_receipt_memo_worker_hook_order_mechanism_rejects_both_mutants`

実走済みの非 pytest 検査:

- 4 file の AST parse
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- U+0300〜U+036F 不在検査

## 制約 meta-test の洗い出し結果

新設した node は 5 件。

- oracle driver: create-and-delete、rule sources、tracked descendant の 3 件
- real repo serialization: create-and-delete、pluggy mutation harness の 2 件

静的検索結果:

- acceptance duration ledger は collection の 90% coverage 契約で、全新規 node の即時登録を要求しない。
- `conftest.py` の real-repo inventory は output snapshot 系を明示的に対象外としている。
- flaky hold、growth hold、skip 分類に新規 node の登録要求はない。
- `check_docs` に test nodeid の exact inventory 要求はなく、実走も違反なし。
- 新 node 名を要求する他の exact inventory は見つからなかった。

## 所有外への波及可能性

- `git_ignored_output_prefixes()` の全 caller は今回の所有 3 test file 内だった。
- `_t080_output_snapshot` を使う T-080 boundary test と、`_real_output_snapshot` を使う floor integration guard 群も新しい fail-closed 判定を継承する。
- `conftest.py`、共有 fixture、acceptance ledger の変更は不要と判断し、編集していない。
- Git-visible な `output/task-runs/reports` は除外されず、既知の F136 型並行 writer risk は残る。
- `.gitignore:24` の `output/env/pegasus/silo_ladder_rung1/job-staging/` 配下には tracked 418 files がある。A1 の必須検査により全 snapshot caller が現在これを拒否する。解消には所有外の `.gitignore` または tracked `output/` inventory への対応が必要。

## 期待赤の finding 集合

実装子 B が未 land のため、次は親の統合前には未解消扱いとなる。

- flaky registry の 3 node は引き続き skip。
- `test_control_lock_serializes_latch_check_through_immediate_visibility`
- `test_control_lock_allows_peer_after_pending_hold_is_durably_released`

上記 2 dispatch test には `poll_interval_s` 注入がまだなく、固定 poll の床が残る。

- `test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary` は hold 登録中。
- `test_receipt_memo_real_xdist_order_has_no_worker_payer` も hold 登録中。

これ以外の赤は回帰として扱う。ただし tracked 418 files の fail-closed は今回静的に確定した所有外矛盾であり、B 未 land 由来ではない。

## 未完・未確認

- pytest は未実走で、追加・変更 node を closed と申告しない。
- tracked 418 files と ignore 規則の矛盾が未解消。このままでは snapshot consumer は決定的に赤になる。
- A7 の実 pluggy node、実 xdist node、受入全走は未確認。
- commit 禁止のため provenance の commit 後監査は対象外。