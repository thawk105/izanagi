## 総括

実装は完了しましたが、pytest はインフラ都合で本体へ到達していません。状態は **実装済み・未実走** です。docs 編集、`git add`、commit は行っていません。

変更前の挙動は次のとおりでした。

- S15 旧形式を受理。
- S7 は未承認 1-operation 草案を受理し、承認 v2 の 2-operation を拒否。
- `compose_core` は draft を合成可能で、registry 分類を検査しない。
- ID 別 exact-key grammar がなく、S15 への `new_sha256` 追加などを拒否できない。

変更後は、S15 旧 blob をそのまま受理しつつ、S7 承認 v2 のみを2-operation grammarで受理します。旧 S7 草案と指定された各変種は拒否します。

実装箇所:

- [erratum.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-impl-a/orchestrator/preregistration/erratum.py:22)
  - 221/333 行と旧・新 digest を完全な64桁で固定。
  - `較正` exact 2件・対象行一致・適用後0件を検査。
  - S15/S7それぞれの top-level、operation、locator exact grammarを実装。
  - `APPROVED_ERRATA` を2 ID、`DRAFT_ERRATA` を空集合に変更。
  - `compose_core` 冒頭で `_validate_erratum_registry()` を必須化。
  - S7文書内とcaller双方の composed digestを照合。
- [test_t139_preregistration_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-impl-a/orchestrator/tests/test_t139_preregistration_binding.py:54)
  - 承認 v2 のpath/commit/SHAと `e0b0…8e0c` に更新。
  - 指定された負例を独立nodeとして追加。
  - 非export禁止集合へ `verify_prereg_receipt` を追加。

承認 artifact のbytesは不変です。

- S7 v2: `deedd71b97640213035c76dac1b22ea15bb21d447991000b0e433de873684df2`
- S15: `a1abc60ef8e3f4346f61fbdd8282c295f353ca272062af02a856e3c5de9dd6d3`

### 検査と赤

期待赤集合は事前指定どおり空です。

実走nodeidは **0件** です。次の全file走を2回、collect-onlyを1回試しましたが、いずれもテスト開始前に `rc=16` で停止しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_t139_preregistration_binding.py -q
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

したがってpytestの赤・緑はありません。インフラ停止を回帰赤には数えていません。

実施済みの非pytest検査:

- `py_compile`: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- 承認2 blobの単発parse・合成診断: `e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c`
- 適用後の `較正`: 0件

新・改名nodeを制約するlive meta-testは検索上存在しません。

### 波及可能性

`compose_core` の全数検索結果:

- production実呼び出し: 0件
- package façadeのimport/export: [__init__.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-impl-a/orchestrator/preregistration/__init__.py:15)
- 実呼び出し: 所有test file内の6箇所のみ
- `compose_core_from_blobs`: 未新設、caller 0件

所有外への可能性:

- `ErratumDocument` / `ErratumOperation` にfieldを追加したため、公開façade経由の将来consumerは構築方法の影響を受けます。現repo内consumerは対象test以外にありません。
- `__init__.py`、`blobref.py`、`addendum_envelope.py` のdocstringには旧名 `verify_receipt` が残っています。所有外かつ非機能面なので未変更です。
- 共有fixtureや他consumer testから対象定数・新node名への参照はありません。
- 歴史的な `output/` mutation ledgerには旧node名がありますが、live meta-testではなく変更していません。

現在の差分は指定された2 fileだけで、commit/addはありません。