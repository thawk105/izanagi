実装完了です。編集は指定された3ファイルだけで、commit/add/stash は行っていません。

## 実装

- [p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/campaign/p3_b4_closed_critic.py:1)
  - config から arm を一度だけ導出する sealed pair factory
  - certified/test-only evidence 分離と共有 session tracker
  - admitted WAL・LoopState・iteration の snapshot 束縛
  - raw/escape decode/path normalization の3-view非開示検査
  - closure manifest hash、開始・success/failure/timeout receipt
  - exact 5-field response parserと薄いCLI
  - critic応答のstate/proposalへの反映なし
- [test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_b4_closed_critic.py:1)
  - 実 admitted fixtureによるon/off digest
  - A1〜A13、M1〜M15、P1〜P4の正負対
  - sorted-globals自走harness
- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_s4_loop.py:1835)
  - 指定されたdocstring 2箇所だけ更新

既存の受理・拒否挙動は維持しています。off digestは引き続き赤loaderを呼ばずgreen digestとbyte一致し、既存providerはdenial、複数turn、server tool useを拒否します。段4driverへの配線はなく、既存production受理集合は変えていません。

## 検証

実走済み:

- 新規自走harness全範囲: 25/25 passed
- 既存digest対照3関数: passed
  - `test_make_critic_digest_reflux_off_drops_red_section`
  - `test_make_critic_digest_reflux_off_skips_all_structured_anomaly_loaders`
  - `test_make_critic_digest_reflux_off_is_byte_identical_to_green_only`
- file/caller集合メタテスト7関数: passed
- `tools/check_codex_agents.py`: passed
- `tools/check_docs.py`: passed
- `git diff --check`、新規2ファイルのAST parse: passed

pytestは次の範囲を投入しましたが、Pegasusの`qstat -Q` preflight失敗で子が一度も起動せず、`rc=16`でした。

- `orchestrator/tests/test_p3_b4_closed_critic.py` 全体
- `::test_p1_real_on_off_digests_are_admitted_by_exact_payload_and_identity_gate`
- 同ファイルのcollect-only

したがってpytestとしては未実走であり、緑とは報告しません。

## 波及可能性

- 現時点のproduction callerはCLIだけです。段4driver、WAL、`make_critic_digest`、既存providerは未変更です。
- closure依存先のprovider、loop、digest renderer、critic roleが将来変わるとprojection hashが変化します。
- 新規テストは共有のcampaign admission APIと`campaign_lock_test_support`を利用します。
- 親所有のrunbookとB-4 prereg更新は未landですが、`check_docs.py`由来の赤はありませんでした。
- 実Claude CLI負の対照、全pytest、全受入走、commit後provenance監査は未実走です。

## 総括

A1〜A13を反映した閉じたcritic pair、証拠receipt、非開示gate、sanctioned CLIとM1〜M15対応テストを実装しました。自走25件、既存対照3件、メタテスト7件、両checkerは緑です。残したテスト赤はありません。pytestはdispatch infrastructure failureで未実走、実CLIと全走も未実走です。