### 直したもの (F1〜F6 に対応づけて file:line 粒度で)

- F1: [sort_swo_dependency_material.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/sort_swo_dependency_material.py:222)
  - 各 source file の読取時 identity を保存。
  - 最終 Git probe 後、全 path の identity を再検査し、不一致を `canonical-source-drift` で拒否。
  - [test_sort_swo_dependency_material.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_sort_swo_dependency_material.py:195) に、前半 file 読取直後の一方向変更を検出する負例を追加。実 Git checkout を使用。

- F2: [test_buildcache_v2.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_buildcache_v2.py:437)
  - commit object と index を持つ実 Git checkout を作成。
  - 実 HEAD と非空 tracked 集合を確認。
  - 合成 HEAD による `canonical-manifest-mismatch`、生成 hash、期待 pin を assert。

- F3: [test_s8b_floor_campaign.py:2400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_s8b_floor_campaign.py:2400)
  - real-root opt-in 正例を追加。
  - production `_prepare_floor_oracle_dependency`、canonical adapter、material sink、実 `prepare_cell` の oracle 配線、post-oracle capability 生成、production postflight を一続きに通す。
  - canonical lease が sink 経由で cleanup されたことも assert。
  - 指定された 4 変異はいずれもこの node を赤にする構造。

- F4: [test_sort_swo_dependency_material.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_sort_swo_dependency_material.py:329)
  - 既存 real-root node を oracle PASS、production `build_v2` の cache miss、cache hit まで延長。

- F5: [sort_swo_dependency_material.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/sort_swo_dependency_material.py:394)、[test_sort_swo_dependency_material.py:278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_sort_swo_dependency_material.py:278)
  - fixture manifest の直接編集を廃止。
  - production generator の PIN 宣言、2 空白区切り、昇順を直接変異。
  - M01 は `canonical-manifest-mismatch`、M02/M03 は単一の `dependency-manifest-invalid` を確認する形。

- F6: [test_s8b_floor_campaign.py:4949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_s8b_floor_campaign.py:4949)
  - marker の `oracle_dependency_root` と `dependency_manifest_sha256` を assert。

### monkeypatch を外した箇所と、それによって新たに実行されるようになった production コード

[test_buildcache_v2.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_buildcache_v2.py:437) から `_probe_git_source` の置換と、`.git/HEAD` への hash 直書きを削除しました。

これにより production の以下が実行対象になりました。

- `_canonical_source_root`
- `_probe_git_source`
- `_run_git`
- 実 `git rev-parse --show-toplevel --verify HEAD`
- 実 `git ls-files --cached -z`
- tracked path の UTF-8、正規化、重複、予約名検査

F1 負例も固定 probe を使わず、実 Git probe を通します。

### 残した monkeypatch と、それによって一度も実行されない production コード (全列挙)

今回追加・変更した node 内では次のとおりです。

- F1 の read wrapperは production readerへ必ず委譲するため、未実行になる production コードはありません。
- F5 の generator 変異:
  - `_probe_git_source` を固定し、Git probe 系を実行しません。F1/F2/F3/F4 が実 Git probe を担当します。
  - reverse-order 変異では production `_manifest_paths` を意図的に実行しません。
  - PIN と区切りの変異も production generator 出力を意図的に壊す mutation seamです。
- F3:
  - `compilers_for_current_site`: site compiler 選択を実行しません。
  - `_bind_current_toolchain`: calibration receipt と live toolchain の照合を実行しません。
  - `prepare_masstree_fetchcontent`: 実 CMake prebuildを実行しません。
  - `buildcache.build_v2`: F3 node内では実行しません。production postflightは実行し、`build_v2` はF4 nodeが担当します。
  - 既存 autouse fixtureにより `source_digest.resolve_evidence` と perf probeを実行しません。
- F4 の既存 fake build environment:
  - 実 site 判定、CCBench commit検査、source evidence再取得、worktree allowlist、trace diff、trace symbol検査、実 CMake subprocessを実行しません。
  - production `build_v2`、post-oracle capability検証、二根検査、archive検査、cache miss/hit処理は置換せず実行します。

### 実走した検査 (nodeid と範囲を併記)

pytest の緑は 0 nodeid です。

許可された `python3 tools/run_tests.py` で焦点 nodeid を3回試行しましたが、すべて以下で test child は未起動でした。

- `qstat -Q preflight rc=1`
- `child_started=false`
- rc=16

実走できた静的検査:

- 変更4 Python fileの `py_compile`
- `git diff --check`
- 禁止対象9件の個別 diff 検査
- index変更なしの確認
- 結合文字 U+0300〜U+036F なし
- caller/consumer の静的列挙

### 実装済み・未実走のもの

- `test_two_root_verifier_rechecks_all_file_identities_after_final_probe`
- `test_manifest_mutations_have_one_exact_verifier_reason` の3 parameter
- `test_synthetic_production_dependency_series_uses_real_git_and_fails_closed`
- `test_real_floor_prepare_material_oracle_and_capability_series_when_configured`
- `test_real_prebuilt_masstree_material_is_pinned_when_explicitly_configured`
- `test_phase_marker_is_create_only_fsynced_private_and_carries_dependency_hash`
- 変更3 test fileの全体回帰
- M01〜M09 の mutation巡

`IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT` は現在未設定です。F3/F4のreal-root nodeは設定時のみ走ります。

### 所有外への波及可能性 (静的列挙)

- `buildcache.build_v2` の全 post-oracle caller。miss/hitを含む各二根検査で全 file identity再検査が増えます。
- `s8b_floor_campaign` の binary admission前 postflight。
- `_prepare_floor_oracle_dependency` を既定関数として参照する `s8b_oracle_n_pilot`。
- `s1_direct_comparison.prepare_cell` の oracle root consumer。
- source file数に比例した追加 `open/stat` による検査コスト。
- 既存 generator testの内部 helper名と、F4から利用する buildcache test helper。
- receipt、digest、共有 fixture、oracle primitiveの受理集合は不変です。
- 指定された非帰属赤と `output_snapshot_ignores.py` には触れていません。

### 裁定からの逸脱 (あれば。無ければ「なし」)

なし。F3の成功正例も pin一致には実 Masstree checkoutが必要なため、F4と同じ明示 opt-inを使用し、合成 rootでの迂回は行っていません。

## 総括

F1〜F6を未 commit、未 stageの作業ツリーへ実装しました。HEADは `3e81c730` のままで、禁止対象9件、docs、`external/ccbench` はすべて無変更です。

pytest childが一度も起動していないため、緑・closedとは申告しません。