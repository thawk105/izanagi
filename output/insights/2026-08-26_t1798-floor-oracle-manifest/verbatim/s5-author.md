### 実装したもの (file:line 粒度)

- [sort_swo_dependency_material.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/sort_swo_dependency_material.py:32)
  - hardened Git probe、tracked path 検証、fd 起点の symlink-safe 読み込み。
  - tracked ∪ {`config.h`, `PIN`} から manifest を生成。
  - `PIN = verified HEAD + LF`。実 root の `PIN` は未参照。
  - [二根等価検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/sort_swo_dependency_material.py:327)。
  - [canonical materialize](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/sort_swo_dependency_material.py:397)。pin 判定は既存 `_prepare_verified_dependency` のみを使用。
  - [lease cleanup](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/sort_swo_dependency_material.py:487)。

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/s8b_floor_campaign.py:2122)
  - binding に actual root と canonical root、lease、manifest hash を分離保持。
  - [prebuild 後の canonical 生成](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/s8b_floor_campaign.py:3107)。
  - [oracle へ canonical root を配線](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/s8b_floor_campaign.py:4147)。
  - build と bench は従来の actual root を維持。
  - [build 後の二根 postflight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/s8b_floor_campaign.py:3555)。
  - [全 build/postflight 後の lease cleanup](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/s8b_floor_campaign.py:4401)。
  - manifest mismatch 診断へ生成 hash と期待 pin を追加。

- [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/buildcache.py:55)
  - post-oracle capability を 6-key 化し、旧 5-key を拒否。
  - [canonical exact + actual 等価 + archive 独立 hash](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/campaign/buildcache.py:966)。
  - cache lookup 前、cache hit 返却前、configure 前後、build 後に二根検査。
  - canonical path は cache preimage に追加していない。

- テスト
  - [新規 generator・変異テストと自走 harness](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_sort_swo_dependency_material.py:59)。
  - [canonical → oracle PASS → build miss → hit 系列](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_buildcache_v2.py:437)。
  - M01〜M08 に対応する manifest、二根、旧 capability、cache hit、floor 配線、空 tracked の検査を追加。
  - floor marker、receipt/binding 一致、lease cleanup を更新。

### 現行の受理・拒否挙動と、変更後の受理・拒否挙動

変更前:

- primitive oracle は pinned 101-path root のみ受理する。
- 196-file の実 source root は `dependency-file-set-mismatch`。
- buildcache も実 root に exact verifier を掛けるため、fresh floor の合成成功集合は空。

変更後:

- primitive oracle、pin、fixture、receipt consumer は不変。
- fresh floor は、実 root が期待 HEAD、正常な非空 tracked 集合、安定した regular bytes、`config.h` を持ち、規則生成 manifest が pin と一致するときだけ受理する。
- oracle は canonical root、build/bench は実 rootを使う。build 境界で両者の tracked 集合・bytes・HEAD・`config.h` を再照合する。
- post-oracle build は canonical root を欠く旧 capability を拒否し、cache hit でも二根検査を省略できない。
- generic build caller、pilot、ambient resolver、resume の受理挙動は変更していない。
- 合成された fresh floor の受理集合は、等価射影に限り空集合から非空へ意図的に拡大する。

### 実走した検査 (nodeid と範囲を併記)

pytest nodeid の緑は 0 件です。緑とは申告しません。

実走できた非 pytest 検査:

- 実 prebuilt root `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` に production generator を適用。
  - 宣言 101
  - manifest `8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875`
  - config `e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a`
- 変更 6 Python file の AST parse、production 3 module と test 3 module の import。
- 新規 test file の plain-runner harness/allowlist 契約を静的確認。
- `git diff --check`、新規 file の末尾空白、結合文字不在、index 未変更を確認。
- 禁止対象 8 件を個別確認し、すべて `UNCHANGED`。

runner 実行要求:

- `test_sort_swo_dependency_material.py::test_materialize_uses_rule_derived_inventory_and_generated_pin`
- 3 test file の `--collect-only`

いずれも Pegasus が dispatch を選択後、`qstat -Q` rc=1 で child 未起動、rc=16。テスト結果ではありません。

### 実装済み・未実走のもの

- 新規 generator test 全体と自走 harness。
- production 系列の oracle compile、buildcache miss/hit。
- `test_buildcache_v2.py` の二根、旧 capability、cache-hit drift、path 非 identity。
- `test_s8b_floor_campaign.py` の canonical 配線、診断、cleanup、postflight。
- `test_plain_runner_coverage.py` と `test_pytest_collection_config.py` の meta-test。
- 既存 oracle verifier/E2E 回帰。
- `IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT` を使う opt-in real-root node。
- 親が行う `<base>/masstree-src` での実 oracle PASS →実 build miss/hit 系列。

### 所有外への波及可能性 (静的列挙)

- `s1_direct_comparison`: floor caller の引数だけ canonical へ変化。他 caller は不変。
- `buildcache.build_v2`: post-oracle capability 利用者は新 6-key 必須。production caller は floor のみ確認。
- `s8b_oracle_n_pilot`: canonical 保証外のまま。
- ambient resolver consumer と resume: canonical gate を通らない現行境界のまま。
- private floor marker: actual root に加えて canonical root と manifest hash が増える。
- receipt/digest consumer: pin と schema は未変更。
- shared Masstree fixture: bytes 未変更。新規テストが期待値として読むだけ。
- archive tool identity、mimalloc、A→B→A、durable execution proof は既存隣接項目へ残る。

### 裁定からの逸脱 (あれば。無ければ「なし」)

なし。

## 総括

実装は作業ツリーに残し、commit・`git add`・docs 編集は行っていません。actual generator の正例値は裁定値と一致しましたが、pytest は infrastructure failure で未実走のため、完了・closed とは申告しません。