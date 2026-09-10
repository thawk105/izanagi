## 総括

**指定3ファイルの差分回収は可能。P1の30関数・51nodeは静的監査で一致した。ただし、全51nodeを同一workerに集めて実snapshot取得を全体で1回にする保証は、現行collection経路にはない。**

HEADとmainはともに`c68d08d9e452138c383e9b92076bf91451912700`。対象3ファイルについて、回収元`559bcbc29cfa27412f103b608e8ac708dcfae6b9`の親との差分は空だった。したがって当該3ファイルの5 hunkだけを回収できる。旧worktreeにはアクセスしていない。

以下の行番号は回収前の現行main基準。パスの略記は次のとおり。

- **T**: `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py`
- **C**: `orchestrator/tests/conftest.py`
- **R**: `orchestrator/tests/test_real_repo_serialization.py`
- **P**: `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py`

## 最小実装plan

| 編集点 | 回収内容 |
|---|---|
| T:73 | 旧差分どおり`_clean_detached_source_snapshot_template`をmodule fixtureとして追加。実snapshot取得とclean/detachedへの上書きを移す。 |
| T:74 | 既存function autouse fixtureにtemplateを注入し、`copy.deepcopy(template)`を各test用に作る。 |
| T:82 | `clean_snapshot`内の返却時deep copyと、別rootへの`original(root)`委譲を保持する。 |
| C:260、C:402 | inventoryとparent-onlyへ対象30関数を明示登録する。 |
| R:52、R:163 | 独立golden二集合へ同じ30関数を明示登録する。conftestから導出しない。 |

test本体、正負期待、productionは変更しない。回収元コミット全体のcherry-pickはせず、同居する裁定fragmentなどは取り込まない。

親が統合する際は、その時点のmainとの差分を再確認する。今回の「後続変更との衝突なし」は現在のHEADについての結論であり、ファイル全置換の根拠にはしない。

## P1・不変条件の監査

**列挙は過不足なし。** 現行TのASTから30個のtest関数を抽出し、各parametrizeの要素数を数えた。20関数が単一node、残り10関数が31nodeで計51node。

| parametrizeの関数位置 | 展開数 |
|---|---:|
| T:306、T:337 | 各2 |
| T:401、T:510 | 各3 |
| T:610 | 4 |
| T:751、T:980、T:1077 | 各3 |
| T:1151 | 5 |
| T:1281 | 3 |

現行4集合には対象登録が各0件。回収元には各30件あり、現行関数集合との欠落・余分・重複はいずれも0件だった。集合全体の件数はinventory/goldenが99から129、parent-only/goldenが34から64になる。

T:73のautouseが全testに適用されるため、PBSテキスト検査や、T:486でsnapshotを再patchするtestもconsumerである。`observe`を直接呼ぶ関数だけへの登録縮小は誤り。

**独立copyは二段とも必要。** templateからfunction fixtureへのdeep copyと、各snapshot返却時のdeep copyを保持する。ネストした`source_sha256`辞書や`untracked_paths`を共有しない。T:621のsnapshot改変、T:649のbefore取得もこの境界のconsumerである。ただし既存testがcopy削除変異を必ず検出するとは未確認であり、検出力を追加する計画にはしない。

**site分類への依存はない。** P:163の取得内容はHEAD、tracked status、untracked paths、detached判定、3ソースのdigest。hostnameやsite判定は読まない。P:133、P:147は環境をGitに渡すため「環境全般から独立」とまでは主張しない。追加site偽装は不要。30秒timeout、`--ignore-submodules=none`、未追跡走査範囲を保持する。

**親の期待への反証:** C:702はパラメータ付きnodeを関数単位へ正規化し、C:2033で登録nodeへmarkerとaccessを付ける。しかしC:1993、C:2102以降はshard確認後、process-memo以外の`@real-repo`を除去する。対象30関数はprocess-memo集合に属さない。

したがって回収で成立するのは、既存のshard分類と`parent=read, ccbench=None`の登録、および**各worker内のmodule fixture実体ごとの取得1回**である。C:2118のnode protocolがsetupを含めてread lockを取るが、reader同士の同時走査は禁止しない。全体1回やtimeout解消、速度改善は未証明。これを補うscheduler変更や追加登録は本回収に含めない。

## 規定変異の具体案

親が回収後の固定HEADに対し、既存`tools/mutation_harness.py`で実施する。各変異は独立適用し、既存testだけを選択する。以下はすべて`KILLED`期待、`hang_risk=false`の案。

**正側:** T:73から移したtemplate関数内の連続anchor

```python
    snapshot["detached"] = True
    snapshot["tracked_status"] = ""
    snapshot["untracked_paths"] = []
```

の`True`だけを`False`へ置換する。期待nodeは

`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py::test_r1_binds_all_three_explicit_values_and_skips_real_driver`

単一理由はP:261のdetached拒否で、T:226の`ok is True`が失敗する。他のclean値、HEAD、digestは変えない。

**負側:** T:623の次の連続anchorだけを一時除去する。

```python
    monkeypatch.setattr(
        probe, "_repo_snapshot", lambda _root: copy.deepcopy(snapshot)
    )
```

期待nodeは

`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py::test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False]`

bad snapshotの注入が外れ、既存fixtureの正常snapshotで受理されるため、T:635の拒否期待が失敗する。これは既存負例の注入と期待が生きていることの確認であり、production拒否判定やcopy境界の検出力を証明する変異ではない。

**分類登録側:** Cのinventoryとparent-onlyから、同じ1関数の登録を同時に除去する。対象は`test_r1_binds_all_three_explicit_values_and_skips_real_driver`。各集合内で直前の`test_build_and_write_leave_repo_tree_unchanged`行と対象行を含むanchorを使い、必要なら集合宣言まで拡張して出現1回にする。Rのgoldenは変更しない。

期待nodeは

`orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`

単一理由はR:1520付近のaccess mapと独立goldenの不一致。C片側だけを削るとC:548付近でimport時のpartition不一致になり、目的のtest失敗まで届かないため採らない。

親は上記3nodeを共通の選択集合にし、harnessのanchor一意性検査、実collection、baseline、期待失敗nodeの照合を使う。自動生成param IDは実collectionで確定する。追加の失敗やsetup errorを単一理由の成功として数えない。

## 未実測・scope外

実施済みは資料読解、Git差分比較、ASTによる件数・集合照合のみ。pytest collection、本走、変異、正式受入は未実施で、緑の主張はない。親が`tools/run_tests.py`経由で対象51nodeと既存登録検査を実走する。

新規gate・test・台帳・fixture一般化、production編集、process-memo登録、scheduler変更、較正変更はscope外。成果物や一時ファイルは書いていない。