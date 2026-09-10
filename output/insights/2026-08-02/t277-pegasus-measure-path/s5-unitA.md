実装単位 A を所有6ファイルだけで実装しました。docs 編集・commit は行っていません。

## 変更要旨

- [buildcache.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py)
  - v2 pre-image に実 site と実効 dependency prefix を常時追加。
  - 非空 prefix の argv 追加と subprocess 環境からの ambient 除去。
  - compute 専用 `gcc/g++` resolver を追加。
  - legacy `cache_key` は無変更。

- [pipeline.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/pipeline.py)
  - `dependency_prefix` を追加。
  - compute では `source_digest.resolve(..., "g++")` と v2 build の `gcc/g++` を使用。
  - 公開 `site` 引数は追加せず、既定時は build_v2 の呼出し形を維持。

- [loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/loop.py)
  - `env_contract` と `dependency_prefix` だけを追加。
  - compute の source digest に `g++` を配線。
  - 非既定値だけを `evaluate` へ渡し、既存 caller の呼出し形と campaign_id を維持。

- 所有テスト3ファイル
  - M7/M8/M9/M10/M12/M13、compiler resolver、OTHER legacy 正例を追加。
  - exact manifest 期待へ `site` と `dependency_prefix` を追加。

## 受理・拒否挙動

現行は v2 cache equivalence が site/prefix を無視し、ambient prefix は subprocess に継承される一方で identity 外でした。注入 `site` は gate/jobs に効き、LOGIN/SUSPECT の subprocess は拒否、OTHER/COMPUTE は受理されます。

変更後は次のとおりです。

- gate の受理集合は不変。
- caller 注入 `site` は引き続き gate/jobs に効くが、digest は変えない。
- 実 `current_site()` が変われば v2 digest が変わる。
- 非空 prefix は exact 文字列を1 argv tokenとして受理し、NULまたは非文字列は拒否。
- 空 prefix は ambient を継承したまま identity に束縛。
- v2 cache equivalence は実 site/prefix ごとに分割され、既存 entry はcold miss。
- OTHER legacy の cache key、configure argv、compiler、campaign_id は不変。

既存期待値の変更は exact v2 manifest の1件です。受理集合が「toolchain等だけ」から「実 site＋実効 prefix も完全一致」へ狭まったため、2 key を追加しました。caller 注入 site による既存 cache hit 期待は、A-1/M13に従い変更していません。

## canonical 化規則

ambient `CMAKE_PREFIX_PATH` は以下の規則で identity 用に正準化します。

- unset/空は `""`。
- OS path separator（Pegasus/Linuxでは `:`）で分割。
- 非空要素を呼出し時 cwd 基準の絶対 path にし、`realpath` で `.`、`..`、symlinkを解決。
- 空要素は空のまま保存。
- 要素を `;` で再結合。

明示した非空 prefix は argv と identity に同じ文字列をそのまま使い、canonical 化しません。

## 静的な波及可能性

- `run_campaign` consumer: `p3_s4_loop*`、`s6_sort_sweep`、`backoff_*`、`demo`、`p3_kickoff`、`s8a_trigger_sweep`、`sanity_silo`、trigger-gating。
- v2 consumer: floor、oracle、T126。全て一度cold missする可能性があります。
- trigger-gating は実装単位 B がlandするまで新しい contract/prefix 引数を供給しません。
- 共有 fixture: `test_t126_qualification_driver.py` が `test_campaign.py` をimportします。
- `test_s1_direct_comparison.py` の最小 buildcache mockを壊さないよう、compiler resolverはmodule-level seamに固定しました。
- full build digestをpinする所有外 goldenは静的検索で見つかりませんでした。凍結成果物bytesは変更していません。

## 検査結果

通過した静的検査:

- 所有6ファイルの `python3 -m py_compile`
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

pytest実走 nodeidは0件です。以下の範囲を `tools/run_tests.py` で計算ノードへdispatchしましたが、いずれもテスト開始前に `qstat -Q` preflightが失敗し、rc=16でした。

- `test_buildcache_v2.py`
- `test_build_site_gate.py`
- `test_campaign.py`
- `test_pytest_collection_config.py`
- F42 meta-test: `test_plain_runner_coverage.py`、`test_real_repo_serialization.py`

内訳は `NQSconnect: Can't create socket (errno: 1)` です。テスト赤や回帰ではなくdispatch infrastructure failureですが、緑は主張しません。親docs未landにより期待する赤集合は空です。

## 総括

- 実 siteと実効 dependency prefixをv2 identityへ束縛しました。
- 明示prefixはargv/envを一意化し、ambient経路は従来の実build条件を保持します。
- computeのsource digestとv2 buildを`gcc/g++`へ揃えました。
- legacy key、OTHER caller、注入siteのgate挙動は維持しています。
- 静的検査は通過、pytestはscheduler接続失敗により未実走です。