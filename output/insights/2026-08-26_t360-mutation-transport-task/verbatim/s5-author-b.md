## 実装した内容

変更前は、両ツールとも site に関係なく `--runner-mode local` を受理し、既存の引数・spec・runner 検査へ進んでいました。

- [tools/mutation_harness.py:2938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_harness.py:2938): `site_policy.current_site(require_evidence=True)` を直接再利用。repo 解決直後、lock・collection 前に `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` の local を rc=2 で拒否します。
- [tools/mutation_worktree.py:398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_worktree.py:398): source repo と commit の解決を preflight から分離しました。
- [tools/mutation_worktree.py:1136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_worktree.py:1136): repo/commit 解決後、preflight・共有木 snapshot・lock・disposable worktree 作成前に同じ site gate を適用します。
- hostname 判定は複製していません。`OTHER` と `PEGASUS_COMPUTE` は引き続き local を受理します。
- harness 直接起動、fanout、attempt sidecar、spec schema、baseline 契約は変更していません。

## 受理集合の変化

- `--runner-mode local`
  - 変更前: 全 site で site gate なし。
  - 変更後: `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` は repo 解決後に rc=2。`OTHER` / `PEGASUS_COMPUTE` は不変。
- `--runner-mode dispatch`
  - 変更前 / 変更後: 不変。site 判定自体を呼びません。
- `--attempt-out` / `--wrapper-attempt`
  - 不変。dispatch 専用の同時指定必須ペアで、local 指定は従来どおり先に拒否します。
- harness 直接起動
  - 不変。禁止していません。
- `izanagi-dev-wave-mutation-spec/v1` と baseline 緑必須
  - 不変。
- exact full-suite argv、fanout
  - 不変。変更していません。

## テスト

追加箇所は [test_mutation_harness.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_mutation_harness.py:337) と [test_mutation_worktree.py:388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_mutation_worktree.py:388) です。改名した nodeid はありません。

- `test_local_site_gate_rejects_before_lock_and_collection[PEGASUS_LOGIN]`: 無いと login で lock と collection へ静かに進みます。
- `test_local_site_gate_rejects_before_lock_and_collection[PEGASUS_SUSPECT]`: 無いと site 不確定時に local runner が起動します。
- `test_local_site_gate_requires_evidence_for_nqsv_unreadable_login_hostname`: 無いと NQSV 証拠欠落 login が `OTHER` へ落ちて通ります。
- `test_local_site_gate_preserves_other_and_compute[OTHER]`: 無いと非 Pegasus の既存 local 利用を過剰拒否できます。
- `test_local_site_gate_preserves_other_and_compute[PEGASUS_COMPUTE]`: 無いと正規 inner-local を計算ノードでも拒否できます。
- `test_dispatch_mode_does_not_consult_local_site_gate`: 無いと dispatch を local 用 site gateへ誤接続できます。
- `test_local_site_gate_rejects_before_preflight_lock_and_worktree_between_observation_points[PEGASUS_LOGIN]`: 無いと wrapper が login で snapshot、lock、worktree 作成へ進みます。
- 同 nodeid の `[PEGASUS_SUSPECT]`: 無いと wrapper が不確定 site で worktree 作成へ進みます。
- `test_local_site_gate_requires_evidence_for_nqsv_unreadable_login_hostname_between_observation_points`: 無いと wrapper の既定 site 判定への退行を見逃します。
- `test_local_site_gate_preserves_other_and_compute_between_observation_points[OTHER]`: 無いと wrapper の非 Pegasus local が過剰拒否されます。
- 同 nodeid の `[PEGASUS_COMPUTE]`: 無いと mutation task 内側の local が計算ノードで拒否されます。
- `test_dispatch_mode_does_not_consult_local_site_gate_between_observation_points`: 無いと既存 wrapper dispatch 経路が site 判定に依存します。

制約 meta-test は次を静的に確認しました。

- worktree test の `_limited` と `_between_observation_points` 規約を全追加 nodeへ適用。
- flaky hold registry、skip census、`conftest.py` の real-repo/receipt consumer inventoryに追加登録は不要。
- acceptance duration ledger は新 nodeid の完全列挙を要求せず、欠落を許容。
- `check_docs` に当該 test nodeid の inventory 制約なし。
- test 関数名の重複なし。

## 未実走

- pytest は一切実走していません。実装済み・未実走です。
- 実施した検査は4ファイルの AST parse、test 名重複検査、call order の静的確認、`git diff --check`、所有範囲確認です。
- 軽量 probe では `pegasus02`、NQSV 証拠なしが、既定呼び出しで `OTHER`、`require_evidence=True` で `PEGASUS_SUSPECT` になることを実関数で確認しました。
- commit、add、push、branch 操作は行っていません。

## 波及可能性

- `tools/pegasus/dispatch_compute.py` の mutation task は wrapper を inner-local で起動します。compute では受理されるため、正規 task 経路との整合は維持されます。
- `tools/mutation_fanout.py` は wrapper argv を常に `--runner-mode dispatch` に固定しているため、site gate を通りません。
- `orchestrator/tests/test_mutation_fanout.py` は fake wrapper を使い、dispatch argv を検査するため、静的には新 gate による赤化要因はありません。
- `orchestrator/tests/test_mutation_fanout_contract.py` は tool identity と ledger を構築しますが、schemaや identity field は変更していないため直接影響はありません。ただし旧 HEAD に束縛された未統合 evidence は、通常の HEAD 更新と同様に再利用できない可能性があります。
- harness の既存 local fixture は `OTHER` を明示し、worktree の実 harness fixtureには最小の `site_policy` packageを追加しました。これが無いと実行機の hostname により既存 local test が環境依存になります。
- 所有外では実装子 A の2ファイルが既に変更済みでした。読み取りのみで、一切編集していません。

## 裏取りできなかったこと

必須の site 判定挙動について裏取り不能事項はありません。

pytest、dispatcherとの統合実走、実 queue 上の mutation task、fanout consumer suiteは親の実走に残しています。

## 総括

裁定 §7 だけを所有4ファイルへ実装しました。login / suspect の local は repo 解決後かつ副作用前に rc=2、OTHER / compute と dispatch は維持されています。DW-M07、直接 harness、schema、baseline、fanoutの受理集合は変更していません。