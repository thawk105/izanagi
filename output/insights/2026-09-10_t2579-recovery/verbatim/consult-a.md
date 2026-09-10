## 総括

**指定3ファイル・5 hunkの回収を妨げる正しさ上の反証は見つからない。負側変異は既存production拒否gateの単一理由変異へ差し替えるべき。** 同一workerへ集約されるという旧説明は誤りだが、D1936の承認前提を覆す未見事実ではない。

以下、T＝`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py`、C＝`orchestrator/tests/conftest.py`、R＝`orchestrator/tests/test_real_repo_serialization.py`、P＝`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py`。行番号は現行HEAD基準。ただし「回収元T」は指定commit基準。

### real候補

- **テスト代表性：負側変異の射程不足。scope内で修正可能。**
  [plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2579-recovery/plan.md:71)の注入除去は、負例を正常入力へ戻して拒否期待を破るだけ。production拒否gateを検査できる証拠にはならない。T:621–624の不正snapshot注入を維持し、P:261のdetached拒否だけを一時無効化する案へ再照準する。

- **ドリフト：登録による同一worker集約・timeout解消の断定は不成立。説明訂正はscope内。**
  C:1993、C:2102で対象nodeの`@real-repo`は除去される。登録だけではreader同士の同時走査を禁止しない。[brief.md:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2579-recovery/brief.md:2)の「解消」は実測前の保証にできない。これは旧説明の誤りであり、[D1936項43:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2579-recovery/d1936-43.md:5)に全worker合計1回という条件はない。scheduler変更・process-memo追加への拡大はscope外。

- **テスト代表性：二段copy・別root委譲の変異検出力は未証明。**
  T:649–654はtest自身でbefore/afterをdeep copyし、snapshot関数も再patchするため、fixtureの二段copyを直接検証する根拠としては弱い。別repositoryを使うT:486–489もsnapshotを再patchし、fixtureの委譲分岐を通らない。実装の静的保持は確認できるが、既存testが各削除変異をkillするとは言えない。新test追加はscope外。

### refuted候補

- **二段copy欠落・別rootの正常値偽装：refuted。**
  回収元T:90でtemplateからfunction用へ、T:94で返却時にdeep copyする。T:93–95のroot比較と`original(root)`委譲も維持される。ネストした辞書・リストを共有する変更はない。

- **恒真ゲート化・正負期待の変更：refuted。**
  回収対象はfixtureと4集合への登録のみ。既存の正側T:226、負側T:635–637、production拒否P:259–266は変更されない。clean値の合成も既存fixtureからの移動である。

- **P1の登録漏れ・過剰登録：refuted。**
  ASTで30関数・静的展開51nodeを独立確認した。回収元4集合の対象登録は各30件で、欠落・余分・重複はゼロ。autouse依存なので直接`observe`しないtestも対象になる。

- **後続変更巻戻し・所有逸脱：現時点の対象差分ではrefuted。**
  HEADは`c68d08d…`。指定commitの親とHEADの対象3ファイル差分は空だった。これは現在の回収可能性の証拠であり、将来の統合時まで所有競合がない保証ではない。全commitのcherry-pickや親による実装編集へ広げる根拠はない。

### 負側変異の具体案

[P:261](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2579-recovery/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:261)の一意な2行anchorを使い、条件だけ一時置換する。

```python
if False:  # mutation only: bypass detached rejection
    raise ProbeError("job repository HEAD is not detached")
```

既存の次のnodeを使う。

```text
orchestrator/tests/test_t1259_qsub_env_delivery_probe.py::test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False]
```

不正値はdetachedだけ。before/afterは同じ不正snapshotなのでP:841の比較は一致し、他のmanifest条件が成立すればP:849でevidenceが返り、T:635の`accepted_evidence is None`が失敗する。**単一拒否理由を外す変異として静的に成立する。** 正側変異とは独立適用し、恒久production差分はゼロに戻す。

分類登録側の二集合同時削除案も静的には妥当。C:545のpartition不一致を避け、R:1520の独立golden不一致を狙える。ただし、その前のcollection処理が正常終了することは親の実測で確認する必要がある。

### 未実測

pytest collection・本走・変異・正式受入は未実施。KILLEDや緑は主張しない。親が既存経路でbaseline、実node ID、期待失敗箇所、余分な失敗やsetup errorの有無を確認する。

成果物・一時ファイルは書いていない。`git status`で既存の未追跡`output/insights/dev-wave-t2579-recovery/`を観測したが、変更していない。