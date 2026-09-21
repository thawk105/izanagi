単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-fix1-prompt.md — 前々 fix の prompt (制約と報告形式の正本。全文適用する)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-fix1b-prompt.md — 前 fix の prompt (差し替えの範囲の正本)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s6-fix1b.md — 前 fix の報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/focus-f2.log — **親が計算ノードで走らせた焦点走 f2 の出力 (10 failed / 4,756 passed / 20 skipped)。本 fix の対象はこのうち `test_b5_tier0.py` の legacy 側 8 ケース**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py — 所有 file (編集対象、`insertion_case` fixture)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py — 所有 file (参照)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/ident.py — 参照 (`verify_recorded_activation_tuple`、`ensure_resumable_attempts`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_p3_s4_loop.py — **参照のみ (編集禁止)**。既存 B-5 seam fixture が site / env contract をどう選んでいるか。読めなければ即停止

この checkout は branch `dev-wave-t2797-unit-a1-fix1c`、HEAD は `5386b9015` (前 fix までを統合済み)。

## 事実 (親の実測、焦点走 f2)

`test_b5_tier0.py` の `insertion_case` の **v2 側 8 ケースは緑、legacy 側 8 ケースは全部赤**。legacy 側はすべて Tier0 に届く前、
`_run_one_iteration_resolved` → `ident.ensure_resumable_attempts` → `verify_against_lock` → `verify_recorded_activation_tuple` で
`IdentityMismatch: campaign-lock activation tuple is not authentic: 記録 activation state が対象 environment contract H を active にしていない` になる
(preparation-io の 1 ケースは `source_digest: git status 失敗 (rc=128)`)。fixture は legacy で `site_policy.OTHER` の env contract を使っており、
その contract は記録済み activation state で active でない。残り 2 件の赤 (`test_p3_s4_loop.py` の seam 2 件) は本 fix の対象外。

## 作業

legacy 側 8 ケースが **Tier0 の legacy build 分岐 (`buildcache.build`) まで届いて検査項目を検査する**よう、`insertion_case` fixture を直す。
- Tier0 より手前の準備層 (site 判定・env contract の選択・campaign identity / activation の準備) の調整は前 fix の「差し替えの範囲」に含まれる。最小の変更を選ぶ
  (例: legacy 側でも記録 activation state で active な contract を使い、campaign_options に `env_contract` が入らない条件だけを作る。あるいは同じ準備層を差し替える)。
- 実物を通す検査対象 (Tier0 の配線・smoke・gateway・パーサ・lock・sidecar writer・`drive_iteration` の早期 return・CLI rc 3) は差し替えない。
- **legacy ケースを削除・skip・xfail しない。** legacy 分岐が現行の本番 CLI から到達不能だと実コードで示せる場合は、編集を止めてその根拠 (file:line) を報告する。
- preparation-io の legacy ケースが `source_digest` で落ちている点も、上の修正で準備差し替え (`_b5_tier0_build_inputs`) に届くようになるか確かめる。
- 編集は `orchestrator/tests/test_b5_tier0.py` だけ。本番コードの差分 0。

制約・報告形式は `s6-fix1-prompt.md` の「制約」「報告形式」を全文適用する (git commit しない / docs を編集しない / テストを走らせない /
既存テストの期待値を変更しない / 機構を stub しない / 揮発値を焼き込まない / 受理集合を変えない / 本番コードに test 専用の迂回を入れない)。
報告の 1 の対応表は「legacy 8 ケース」の 1 行でよい。最後に `## 総括` を置く。
