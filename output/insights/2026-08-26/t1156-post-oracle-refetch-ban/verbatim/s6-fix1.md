## 所見対応表 (closed / partial / regressed)

`closed` は実装と静的検査による判定です。pytest は未実走です。

| 所見 | 状態 | 対応 |
|---|---|---|
| F1: builder identity の fail-open | closed | capability を無条件に構築し、非 exact builder と capability 欠落を build 呼び出し前の `FloorCampaignError` で拒否 |
| F2: oracle と異なる inventory 実装 | closed | 独自 parser/inventory と archive 特例を削除し、oracle の `_verify_dependency_root()` を直接使用 |
| F3: campaign production 配線の未検査 | closed | 非 exact builder の呼び出し 0 件と、default exact builder への literal capability 配線を追加 |
| F4: M4 identity 配線の偽陰性 | closed | 同一 base・receipt・archive の generic entry を seedし、capability build の cache missを要求 |
| F4: manifest 本体 hash 削除の偽陰性 | closed | tracked file と manifest を同時更新した自己整合入力を configure 前に拒否 |
| F5: positive fixture の自己観測 | closed | fixture bytes、manifest、各 digest、HEADを test literalへ固定 |
| H2: production manifest generator 不在 | partial | 親裁定どおり本 fix では未実装。F2により oracle/buildの検証規則だけは統一 |
| X1〜X5 | partial | 親裁定どおり scope 外 |
| 既存事後検知 | closed | archive事前照合、cache-hit照合、build後root/content検査、floor postflightを維持 |
| 新規回帰 | regressed なし | 静的確認。pytest未実走のため動的保証は未確定 |

## 実装した変更 (file:line)

- [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:939)
  - oracle自身の dependency verifierを使用。
  - manifest hash、config、HEAD、archiveをreceipt由来の値と照合。
  - 独自inventory、`.git`除外、未宣言archive特例を削除。
  - configure前後の材料検査は [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:2305)、実効値検査は同ファイル2319行付近で維持。

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:4010)
  - dependency-bound `sort_best` の capabilityをbuilder identityに関係なく構築。
  - exact `buildcache.build_v2` 以外を呼び出し前に拒否。
  - build直前にexact builderとcapability keyを明示的例外で再確認。

- [test_buildcache_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:359)
  - `.git`、config、archiveを含むoracle-shaped fixtureをliteral化。
  - [M4統合テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:764) と [manifest authority負例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:792) を追加。

- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_s8b_floor_campaign.py:2317)
  - 非 exact builder呼び出し0件のテストを追加。
  - [literal capability配線テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_s8b_floor_campaign.py:2372) を追加。
  - 既存production consumerの期待値は変えず、test fakeをexact symbolへ据えるsetupのみ更新。

## 実走した検査 (nodeid と結果)

実装済み・未実走です。成功扱いしたnodeidは0件です。

以下9 nodeidをrunnerへ渡しましたが、`qstat -Q preflight rc=1`、`child_started=false`、`rc=16`でpytest開始前に停止しました。

- `test_buildcache_v2.py::test_v2_post_oracle_flag_is_exact_one_and_generic_base_only_stays_zero`
- `test_buildcache_v2.py::test_v2_post_oracle_policy_forces_miss_against_same_material_generic_entry`
- `test_buildcache_v2.py::test_v2_post_oracle_rejects_self_consistent_rewritten_manifest_authority`
- `test_buildcache_v2.py::test_v2_post_oracle_manifest_rejects_changed_declared_non_config_file`
- `test_buildcache_v2.py::test_v2_post_oracle_config_mismatch_refuses_before_configure`
- `test_buildcache_v2.py::test_v2_post_oracle_effective_disconnected_off_refuses_before_build`
- `test_buildcache_v2.py::test_v2_post_oracle_policy_separates_only_bound_identity`
- `test_s8b_floor_campaign.py::test_dependency_bound_sort_best_rejects_nonexact_builder_before_call`
- `test_s8b_floor_campaign.py::test_dependency_bound_sort_best_default_builder_receives_literal_capability`

実施済みの非pytest検査:

- 4ファイルのAST parse: 成功
- `git diff --check`: 成功
- U+0300〜U+036F: 検出なし
- literal fixtureをoracle verifierとbuild gateへ通す診断: `POST_ORACLE_FIXTURE_GATE_OK`
- `git status`: 許可された4ファイルだけが変更状態
- runner生成のdispatch一時成果物は除去済み

## 受理集合の変化

- dependency-bound `sort_best` はexact `buildcache.build_v2`だけを受理します。wrapper、partial、spy、custom builderは実行前に拒否されます。
- post-oracle材料はoracleと同じ規則で検証されます。`.git`を含む全regular fileとarchiveがmanifestに宣言されていない入力は拒否されます。
- capabilityなしのgeneric base-only `build_v2` はflag 0本、従来identityのままで変更ありません。
- default official/pilot経路はexact builderへ正規化されるため、F1による追加拒否の対象外です。
- H2によりproduction manifest生成経路が元からdormantである点は変わりません。

静的な波及可能性:

- 所有外caller: direct `build_cells`でdependency-bound `sort_best`へcustom builderを渡すcallerは新たに明示拒否されます。
- 共有fixture: `_make_fake_build` はcapability引数を受け、指定時だけdisconnected tokenを返します。capabilityなしconsumerは不変です。
- consumer tests: production dependency経路の既存6テストはfakeをexact symbolへ据えるsetupへ更新しました。assertや期待値は変更していません。
- `test_paper_story_a1_paired.py`、`test_paper_story_a2_certification.py`、`test_build_site_gate.py`、`test_real_repo_serialization.py`、`test_s8b_materialization.py` はcapabilityなし経路のため静的には非波及ですが、未実走です。

## 実装しなかったもの と 理由

- X1: source tree内の再生成。再取得ではなく書込み権威の別審査。
- X2: mimalloc/googletest束縛。別wave。
- X3: cross-base historical argv。既存受理集合を変更するため別wave。
- X4: process間排他。書込み権威の変更を伴うため別wave。
- X5: resume/durable manifest migration。既存manifestを失効させるため別裁定。
- H2のmanifest generator追加。親裁定で本fixの対象外。
- docs、worklog、commit、push、Web検索は実施していません。

## 総括

F1〜F5は許可された4ファイル内で実装しました。既存事後検知と既存テスト期待値は維持し、許可外差分もありません。

ただしPegasus dispatch障害によりpytestは未実走です。採用判断には、上記nodeidと関連consumer範囲の再実走が必要です。