## 実装 plan (file:line)

**P1 に賛成。監査位置は P2 を修正し、`commit-rev-parse` 直後・`commit-message-postcheck` 前を推奨する。** 行番号は読解時点の現物に対応する。

資料上の不一致がある。指定の [D2044-item5.md](/home/SFC/tanab/.claude/jobs/844e52e7/tmp/t2670/verbatim/D2044-item5.md:1) は「A-1 の本番測定の認可は据え置く」で、本件の位置移動を記した逐語ではない。以下は今回の依頼本文を根拠にした plan であり、D2044 の逐語確認済みとは扱わない。

[tools/dev_wave_wait.py:3838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-merge-provenance-position/tools/dev_wave_wait.py:3838) の `merge-history-provenance` 呼び出しを、現行 3873 行の `committed_sha = _head_sha(...)` 直後へ移す。argv、stage 名、`diagnostic_reason`、`capture_failure_output=True` は保存する。

変更後の順序は次のとおり。

```text
merge_pending = True
merge
merge-message-provenance
commit-dry-run
commit
merge_pending = False
commit-rev-parse                 # committed_sha を保存
merge-history-provenance        # 移設先
commit-message-postcheck
postcheck
commit-head-postcheck            # committed_sha と比較
prerun-clean
```

位置の比較：

| 候補 | HEAD の pin と赤時の状態 | 判断 |
|---|---|---|
| P2：commit 直後、rev-parse 前 | main と merge commit は監査対象になる。checker 内部の HEAD pin はあるが、waiter の pin は監査後なので、checker 終了から pin までの HEAD 変更を既存の比較で捉えにくい。赤なら commit を残す。 | 次点 |
| **rev-parse 後、message-postcheck 前** | waiter の pin と最終 HEAD 比較が監査呼び出しも挟む。監査赤でも commit を残す。 | **採用推奨** |
| message-postcheck 後、head-postcheck 前 | 同じく比較で挟めるが、message 検査の赤が全史監査より先になる。 | pin 取得後すぐに置く方が明瞭 |
| head-postcheck 後 | 既存の HEAD 比較が監査を挟まなくなる。 | 不採用 |

checker は `tools/check_ai_provenance.py:3558` で HEAD を解決し、`:1775` の `_commit_range` で **policy commit 自身と `policy..HEAD`** を列挙し、`:3573` で HEAD 不変を確認する。commit 後なら main 側 commit と merge commit が対象に入る。waiter の pin を渡す CLI は追加しない。この配置も、HEAD の一時的な往復変更まで検出する新保証ではない。

`merge-message-provenance` は現行 `tools/dev_wave_wait.py:3849` の commit 前に残す。checker の `:1721` が MERGE_HEAD から prospective parents を作り、`:1749` が index と各親との差分を使うためである。

## 中止・後始末の契約 (P1 への賛否と根拠)

**P1 を採用する。cleanup の実処理変更は不要。** 位置移動と契約コメント、テスト更新を同じ変更単位にする。

| file:line | 変更要否・根拠 |
|---|---|
| `tools/dev_wave_wait.py:607` `_AcceptanceLifecycle` | フィールド変更不要。`merge_pending` は未完了 merge の abort 権限を表し、commit 後の巻き戻し権限ではない。必要ならコメントで明記。 |
| `:3831` `merge_pending = True` | 移動不要。merge が部分的に失敗しても abort できるよう、merge 実行前に設定する。 |
| `:3872` `merge_pending = False` | 移動不要。commit 成功直後、rev-parse と移設する監査より前に解除する。監査成功後まで延期しない。 |
| `:3330` `_cleanup_lifecycle` | 不要。所有権と pending を先に消費して再入を無害化し、既存の解放権限を維持する。 |
| `:3286` `_cleanup_after_claim` | 不要。pending が false なら abort せず、解放権限がある lease のみ release する。 |
| `:3118` `_abort_pending_merge` | 不要。commit 前の失敗に対する abort、MERGE_HEAD 不在、tracked clean の確認を維持する。 |
| `:4162`、`:4198`、`:4272` | 不要。監査の `_StageFailure` を保存し、一時 message を削除して既存 cleanup に進む。 |

取得した lease の場合、監査赤では **受入 command 0 回、merge commit を保持、lease を解放**する。`HELD_SELF` は従来どおり解放権限がないため、この呼び出しからは解放しない。release 自体が失敗した場合の cleanup failure 優先も維持する。

`reset --merge <premerge sha>` は採らない。作成した merge commit を reflog にだけ残すと、`tools/dev_wave_cleanup.py:575–583` は main から到達不能な commit として撤去を拒否する。これは D1233 の「削除対象 ref の reflog commit は喪失側へ加える」と整合する防壁であり、reflog を消して回避すべきではない。commit を残す判断は、直ちに撤去可能になるという保証でもない。

## 既存 test の更新表

以下の行番号はすべて `orchestrator/tests/test_dev_wave_wait.py`。表中の「移設」は、**merge 直後の全史監査を commit-rev-parse 直後へ動かす**ことを指す。rev-parse を抽出していない期待列では commit 直後に見える。

まず共通部を直す。

| 対象 | 更新 |
|---|---|
| `:757` `_provenance` | history と message を連続登録する helper を解消する。利用箇所 6644、7091、8112 は `_message_provenance(fake)` と、pin 後の `expect_run(_history_provenance_argv())` に分離する。 |
| `:6683` `_STAGES` | `merge-history-provenance` を `commit-rev-parse` と `commit-message-postcheck` の間へ移す。 |
| `:6702` `test_nonzero_stage_blocks_submission_and_releases` | queue と `expected` の両方を新順序へ変更。message、dry-run、commit、rev-parse を通過する stage 集合に history を含め、history を実行する集合は history とその後段だけにする。abort 集合から history を除く。rc=70、失敗 stage、command 不在、release、全イベント一致、queue 消費を維持。 |
| `:704` `_preflight`、`:774` `_PRECLAIM_GUARD_EVENTS` | claim 前の history 期待は不変。 |
| `:1234` `_RoutingAcceptanceEffects`、`:1397` `_RetryAcceptanceEffects` | 既存の引数なし監査の応答分岐は変更不要。前者は claim 前後、後者は claim 前の時計進行を区別しており、commit 前配置には依存しない。 |

`_history_provenance_argv` を直接使う全 test と、連続 helper 経由で影響する test：

| test（開始行） | 期待列の変更／維持する assert |
|---|---|
| `test_acceptance_shards_are_not_injected_into_other_subprocess_paths`（3574） | 変更なし。checker 起動に shard 環境変数を注入しない性質を維持。 |
| `test_preclaim_behind_without_message_claims_and_submits_without_release`（6173） | 変更なし。preclaim behind → history → claim、成功・投入 1 回・解放なしを維持。 |
| `test_preclaim_behind_without_message_reaches_claim`（6209） | 変更なし。preclaim history < claim を維持。 |
| `test_preclaim_behind_with_merge_message_reaches_claim`（6232） | 直接 assert は preclaim 順序なので変更なし。成功と claim 回数を維持。 |
| `test_postclaim_merge_without_implementation_conflict_accepts_self_report`（6289） | 抽出列の history を commit 後へ。self-report → merge → message → dry-run → commit → history → command とし、成功を維持。 |
| `test_owned_path_prefix_is_not_overlap_and_reaches_submission`（6531） | 2 本目の history のみ移設。prefix を overlap と誤認しないこと、投入 1 回・解放なしを維持。 |
| `test_missing_owned_path_skips_diff_warns_and_reaches_submission`（6573） | 2 本目のみ移設。diff 不在、警告 1 回、成功を維持。 |
| `test_merge_sequence_and_postcheck_are_exact`（6632） | helper を分離し queue の history を pin 後へ。git mutation 列、禁止 option 不在、lease 保持の表示、一時 message 削除、queue 消費を維持。 |
| `test_nonzero_stage_blocks_submission_and_releases`（6702） | 上述の queue・期待列・stage 集合を更新。 |
| `test_postmerge_tracked_dirty_blocks_submission_and_releases`（7073） | queue と完全イベント列の history を pin 後へ。`prerun-clean` 赤、投入なし、release を維持。 |
| `test_malformed_ai_agent_message_fails_provenance_before_commit`（7240） | message 赤までの列から **merge 側 history を除く**。preclaim history は保持。commit 不在、abort、release、stage/source_rc を維持。 |
| `test_committed_message_without_ai_agent_never_runs_acceptance`（8103） | queue と完全イベント列の history を pin 後・log 前へ。message-postcheck 赤、投入なし、release、abort なしを維持。 |

abort を期待する箇所、および監査赤の関連 test：

| 対象 | 更新／維持 |
|---|---|
| `_abort_clean`（1147、呼び出し 1149）、`_ABORT_CLEAN_EVENTS`（1162）、routing fake の abort 応答（1382） | 共通部は変更なし。未完了 merge の cleanup に引き続き必要。 |
| `test_postclaim_merge_provenance_failure_rejects_self_report`（6335、abort assert 6353） | **message** 検査赤なので abort を維持。commit/dry-run/command 不在、release 1 回を維持。 |
| `test_nonzero_stage_blocks_submission_and_releases[merge-history-provenance]`（6702） | **abort 期待を削除する対象。** commit と pin の通過、history 赤、release を期待する。 |
| `test_malformed_ai_agent_message_fails_provenance_before_commit`（7240、abort assert 7260） | abort 維持。前表のとおり history の期待だけ除く。 |
| `test_merge_history_provenance_failure_blocks_submission_releases_and_returns_reason`（7308、abort assert 7331） | **abort 期待を不在 assert に反転する対象。** 現在の「message/dry-run/commit がない」を、それらと pin が history より前に実行済み、へ変更。command 不在、rc=70、source_rc=1、理由全文、`(claims, submissions, releases) == (1,0,1)` を維持。 |
| `test_merge_history_provenance_unexpected_rc_fails_closed`（7348） | 既存 assert を維持し、commit 済み・abort 不在も固定。source_rc=29 の握り潰しを許さない。 |
| `test_merge_failure_aborts_before_release`（7394） | 変更なし。merge 自体が失敗するため abort → release を維持。 |
| `test_held_self_merge_failure_aborts_without_releasing_lease`（7428、abort assert 7444） | 変更なし。abort は行い、release は行わない。 |
| `test_merge_abort_nonzero_is_cleanup_failure`（7692） | 変更なし。merge 失敗後の abort rc=8 を cleanup rc=74 とする性質を維持。 |
| `test_merge_abort_requires_clean_repository_postcondition`（7730） | 変更なし。MERGE_HEAD 残存／tracked dirty を cleanup failure とする。 |

さらに既存の `test_positive_postmerge_behind_count_blocks_only_submission`（8063）、`test_created_commit_identity_change_blocks_submission`（8076）は期待変更不要。後段の main 追随確認と HEAD 比較が残ることを確認する。

## 新規負例 test の設計

**実 git 版：`test_real_git_main_only_history_violation_blocks_acceptance_after_commit` を追加する。**

`_real_waiter_repo`（1081）を使い、実 git test 群の 8551 行付近へ置く。8551 の dirty test と 8639 の production checker test は、いずれも **subprocess で waiter の `acceptance` CLI を起動**している。新規もこの形式を採る。直接 `_run_acceptance_attempt` を呼ぶ形式より、実 HEAD、実 lease helper、エラー表示、command 未投入をまとめて確認できる。

構築手順：

1. fixture 作成後、偽 checker と計数用 runner を commit し、main をその共通基点へ fast-forward する。checker は `_write_path_aware_provenance_checker`（982）と同じく、temp repo の `tools/check_ai_provenance.py` に生成する。
2. runner は起動時に **repo 外の計数ファイルへ 1 行追記**する。`_write_exact_runner`（1040 付近）を使い、通常の `tools/run_tests.py` 経路として起動可能にする。
3. main にだけ非競合の変更を commit し、その SHA を保存する。wave へ戻り、この SHA が開始時 HEAD の祖先でないこと、main の祖先であることを fixture の前提として確認する。
4. SHA の自己参照を避けるため、checker は repo 外の SHA ファイルを読む。そのパスは共通基点の checker に埋め込み、SHA ファイルは main commit 作成後に書く。
5. 有効な merge message、repo 外の receipt/log を指定し、fixture 内の waiter を `acceptance ... -- <python> <repo>/tools/run_tests.py` で起動する。

偽 checker の分岐：

```text
--message-file あり:
    0 を返す
引数なし:
    git merge-base --is-ancestor <保存した違反 SHA> HEAD
    rc=0 → 違反理由を stderr に出し、1 を返す
    rc=1 → 0 を返す
    その他 → 検査不能として非 0 を返す
```

必要なら repo 外の trace に、呼び出し種別・観測 HEAD・lease ファイルの有無を記録する。これにより preclaim は緑、message は緑、commit 後 history は赤で、途中に lease が存在したことまで確認できる。

主張する結果：

- waiter rc=70、stage=`merge-history-provenance`、source_rc=1、違反理由が出力される。
- runner 計数が **0**。receipt 不在だけで未投入を代用しない。
- `acceptance.lease` が消えている。
- HEAD は開始時 wave tip と異なる **2 親 merge commit**。親は開始時 wave tip と取り込んだ main tip。
- 違反 SHA が終了時 HEAD の祖先である。
- MERGE_HEAD 不在、tracked clean、receipt/log 不在。

**模擬版：`test_merge_history_violation_after_commit_blocks_submission_and_releases` を追加する。**

`_FakeEffects`（313）の test-local 派生で、dry-run ではなく `git commit -F ...` の成功後だけ `committed=True` にする。引数なし checker は未commitなら 0、commit 後なら違反理由付き rc=1、message checker は 0 とする。queue は新順序を固定する。

`_run_acceptance`（1179）経由で実行し、history stage、rc/source_rc/理由、command と launcher の不在、commit 1 回、abort/reset 不在、release 1 回、queue 消費、渡した lifecycle の `merge_pending=False` と ownership 消費を主張する。

**模擬差：実 git 版は実際の祖先到達性を検証し、fake 版は commit 実行フラグだけを模す。どちらも production checker の全規則を再実装するものではない。**

## 変異被覆表

| 変異 | KILL／対照となる test |
|---|---|
| **M1：history を commit 前へ戻す** | 新規実 git test は違反を監査時に観測できず、期待する history 赤にならないため KILL。新規 fake 版も KILL。加えて更新済み `test_merge_sequence_and_postcheck_are_exact`、`test_nonzero_stage_blocks_submission_and_releases`、`test_postclaim_merge_without_implementation_conflict_accepts_self_report` の順序期待も KILL。**新規負例だけではないが、到達性による意味的な証拠は実 git 版が担う。** |
| **M2：history 呼び出し削除** | 新規実 git／fake 版、`test_merge_sequence_and_postcheck_are_exact`、`test_nonzero_stage_blocks_submission_and_releases`、既存 history 赤の 2 test が KILL。 |
| **M3：history 赤を握り潰す** | 新規実 git／fake 版、`test_merge_history_provenance_failure_blocks_submission_releases_and_returns_reason`、`test_merge_history_provenance_unexpected_rc_fails_closed`、stage parameter の history ケースが KILL。 |
| **M0：comment のみ変更** | SURVIVED 対照。コメント内容に依存する test は追加しない。実 git fixture は変異後 waiter をコピーするため、ソース束縛による無関係な失敗を避ける。 |

以上は事前登録する予測であり、変異実測済みの結果ではない。

## 不変条件の確認

- `tools/dev_wave_wait.py:3776` 付近の `preclaim-history-provenance` は移動・削除しない。既存 `test_preclaim_history_provenance_failure_never_claims_and_returns_reason`（6368）の claim 0、command 0、lease dir 空、理由表示を維持する。
- 全史監査は claim 前と merge commit 後の 2 箇所を維持し、D908 の監査削減禁止に従う。
- `merge-message-provenance` は commit 前に維持する。
- `tools/check_ai_provenance.py`、`tools/dev_wave_land.py`、`tools/dev_wave_cleanup.py`、`tools/known_violations/` は変更しない。
- `--range` 化、新しい gate・検査・台帳は追加しない。新規 checker は test の temp repo に生成する fixture だけとする。
- 実装変更は指定された waiter と test の 2 ファイルに限定する。brief の docs 成果物はこの plan の変更対象外。

## 総括

P1 は既存 lifecycle を維持して実現する。P2 は **HEAD pin 取得直後への移設**を推奨し、監査も既存の HEAD 比較で挟む。正例の順序期待と commit 前 abort を保ち、commit 後監査赤だけを「commit 保持・所有 lease 解放」へ更新する。

指定資料を静的に照合した。書き込み・pytest・変異実測は行っていない。親への引継ぎ事項は、P2 の配置判断と、内容が本件に一致しない D2044 逐語資料の差し替えである。