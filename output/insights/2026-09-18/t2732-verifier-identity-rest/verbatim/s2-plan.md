## 変更面

行番号は変更前の現物。以下の相対 path はすべて指定された parent worktree 基準。必読 4 file は読了し、書込み・pytest 実行はしていない。

| file | 行 anchor | 追加・変更する逐語 |
|---|---|---|
| `orchestrator/qualification/contract.py` | :78 `"orchestrator/verifier/parse.py",` の直後、:79 の policy より前 | 下記 A の 3 行を追加 |
| `orchestrator/tests/test_t126_pegasus_tools.py` | :1527–1531 の既存包含 test の後、:1534 の次 test より前 | 下記 B の新規 test を追加。既存 test は変更しない |

A:

```python
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/commit_receipt.py",
    "orchestrator/verifier/report.py",
```

B:

```python
def test_required_code_identity_includes_verifier_init_report_commit_receipt():
    assert "orchestrator/verifier/__init__.py" in REQUIRED_CODE_IDENTITY_PATHS
    assert "orchestrator/verifier/report.py" in REQUIRED_CODE_IDENTITY_PATHS
    assert "orchestrator/verifier/commit_receipt.py" in REQUIRED_CODE_IDENTITY_PATHS
```

AST による現物確認では code 集合 40、script 集合 3、和集合 43。変更後はそれぞれ **43、3、46** になる。frozenset の記述順序は identity に影響しない。

P1 の新規 1 本を推奨する。既存 4 file の test を維持し、今回の 3 file による失敗を別 node へ帰属できる。
7 file を 1 本に統合しても包含検査の検出力は同等だが、既存 node の変更が必要になる。どちらも個別 assert なら欠落 path は失敗行で識別できる。

## consumer 列挙

現物の `rg` と tracked file の `git grep` で、定数名の直接出現は **6 file・24 行**。内訳は定義 1、import 5、comment 1、実参照 17。production は 3 file、test は 3 file、script の直接参照は 0。

| file・行 | 用途 | 追加対応 |
|---|---|---|
| `orchestrator/qualification/contract.py:39` | 定義 | A を追加 |
| 同 :533–537 | `series_identity()` の exact key set 検査 | 自動追随。43-key 形だけを受理 |
| `orchestrator/qualification/identity.py:27,140–150` | import、code/script 和集合の exact 比較、記録 commit の blob hash 検証 | 自動追随 |
| `orchestrator/qualification/t126_driver.py:64,372–384` | import、各 code path の regular file 検査と disk/指定 commit blob 照合 | 自動追随 |
| `orchestrator/tests/test_t126_pegasus_tools.py:704` | import | 不要 |
| 同 :980–1025 | `_attempt` の fixture file 作成 | 自動追随 |
| 同 :1026 | adapter が集合外である旨の comment | 実 consumer ではない |
| 同 :1085–1088 | fixture commit の blob から code hash 作成 | 自動追随 |
| 同 :1486–1487 | reservation policy、build admission の包含検査 | 不要 |
| 同 :1519,1522 | activation 閉包の包含、record directory の除外検査 | 不要 |
| 同 :1528–1531 | verifier 既存 4 file の独立包含検査 | 据え置き。今回分は B |
| 同 :1541 | preimage と required set の等価比較 | 自動追随 |
| 同 :1554 | tracked 検査の parameter 生成 | 自動追随、3 node 増加 |
| `orchestrator/tests/test_t126_qualification_contract.py:21,76` | import、preimage の code map 生成 | 自動追随 |
| `orchestrator/tests/test_t419_probe_causality.py:38,42` | import、環境契約閉包の部分集合検査 | 不要 |

`_attempt` は :981 で `repo / relative`、:982 で親 directory を作り、追加 3 path はいずれも :1024–1025 の generic 分岐で `fixture {relative}\n` を書く。その後 :1050–1051 で commit し、:1085–1088 で hash を得るため、fixture 専用分岐の追加は不要。

間接 consumer と script の独立列挙は次のとおり。

| file・行 | 現物の動作 | 判定 |
|---|---|---|
| `orchestrator/qualification/submission.py:216–217` | `build_series_preimage()`、`series_identity()` を呼ぶ | driver/contract 経由で追随 |
| `tools/pegasus/submit_t126_qualification.sh:124–134` | 実行入力 **5 path** の tracked 検査 | 独立列挙は存在するが、code identity 全集合の複製ではない。変更不要 |
| 同 :149–164 | 実行入力 **7 path** の disk/blob 照合 | 同上。追加 3 path は driver の照合対象になる |
| 同 :142–144 | `orchestrator` を commit から archive | 追加 3 file も staging に含まれる |
| `tools/pegasus/t126_qualification.sh:790–798` 付近 | source-stage evidence 用の固定 field/path | code identity 全集合の列挙ではなく、変更不要 |

したがって、P4 の「script は path 名を列挙しない」は訂正が必要。「required code 集合を独立に全列挙していない」が正確である。

## 既存 test の影響

- `test_every_required_identity_path_is_tracked_in_this_repo`（:1552–1573）は **43 → 46 node**。増える parameter は `orchestrator/verifier/__init__.py`、`orchestrator/verifier/report.py`、`orchestrator/verifier/commit_receipt.py`。現物の `git ls-files --stage` で 3 file とも mode `100644` の tracked file と確認した。
- `test_series_preimage_exact_code_identity_set_tracks_activation_closure`（:1534–1549）は fixture と期待集合がともに追随する。:1545–1549 の activation leaf 欠落検査も維持される。ただし production 集合から今回の path が誤削除されても双方が追随するため、B が必要。
- `test_t126_qualification_contract.py:76` の preimage は定数から生成されるため修正不要。:279–315 の toolchain 検査も同じ生成関数を使用する。
- `test_t419_probe_causality.py:42` は部分集合 assert なので純増で壊れない。
- `test_t126_qualification_driver.py:98–113` の `_prologue_value` は prologue 検査用の部分 fixture。完全な code identity 集合を表す fixture ではなく、今回の追加は不要。

`__init__.py` の basename を特別扱いする分岐は対象処理にない。path 結合・map key・parameter は完全な相対 path を使用し、parametrize に独自 `ids` もない。既存の qualification/campaign/calibrator の同名 file と衝突しない。

指定された既存 test について、この変更に起因する赤は静的には予測しない。焦点走 4 file 全体では、新規 test 1 と parameter 3 の **計 4 node 増**を期待する。実行結果は未確認。

## 変異候補

親の段 4 で、実装後の baseline に対して事前登録する。

期待失敗 node `V` は以下の完全な node id を指す。

```text
orchestrator/tests/test_t126_pegasus_tools.py::test_required_code_identity_includes_verifier_init_report_commit_receipt
```

| ID | tracked 行への変異 | code 件数 | 殺すはずの test node id |
|---|---|---:|---|
| N1 | `contract.py` の追加 `"orchestrator/verifier/__init__.py",` 行を削除 | 42 | V |
| N2 | 同 `"orchestrator/verifier/report.py",` 行を削除 | 42 | V |
| N3 | 同 `"orchestrator/verifier/commit_receipt.py",` 行を削除 | 42 | V |
| N4 | 同 `"orchestrator/verifier/report.py",` を `"orchestrator/verifier/cli.py",` に置換 | 43 | V |
| N5 | 同 `"orchestrator/verifier/commit_receipt.py",` を既存 member `"orchestrator/verifier/core.py",` に置換 | 42 | V |
| E1 | test file の B の def 行直後に `    # Identity membership regression coverage.` のみ追加 | 43 | なし。SURVIVED を期待 |

N4 の `cli.py` は現物で tracked regular file と確認済みで、現在の required set にはない。件数維持だけでは不正置換を見逃すことを検査できる。N5 は frozenset の重複除去を伴う。

N1–N5 の期待失敗集合は `{V}`。集合由来の fixture・等価比較は追随し、tracked 検査も欠落や tracked 兄弟への置換自体を検出しないため、新 test の独立した検出力を確認できる。

存在しない path への置換と、変異下でしか生まれない parameter node の期待登録は行わない。先例 insight §5 erratum のとおり、harness が baseline collection で中止する。V の baseline 実在を確認し、各置換 anchor が対象 file に 1 回だけ現れる形で登録する。test assert の反転は production 欠落の検出力を示さないので採らない。

## scope 外と残る穴

census gate、歴史成果物の互換層・二重受理、`schema_version`、hash domain、`REQUIRED_SCRIPT_IDENTITY_PATHS`、campaign_lock 閉包、凍結 manifest、verifier package 以外の新 path は変更しない。検証ロジックと verifier の判定意味論にも触れない。

40-key 形は変更後の `series_identity()`（変更前 :533–537）で `required set mismatch` になる。受理形は 43-key 形への置換であり、受理形の追加ではない。過去の成果物の bytes と当時の判定は保持し、この不受理を過去の測定の無効化に使わない。

`ls orchestrator/verifier/` の現物は **9 file**。今回で集合に入るのはそのうち 7 file で、`__main__.py` と `cli.py` が残る。
したがって「verifier package 全 file を包含」は成立しない。残る 2 file は所見に留め、今回の実装には追加しない。

## loader 閉包の影響

`campaign_lock.py:107` は既に `contract.py` を含む。`contract_loader_binding.py:518–532` は HEAD blob と disk を比較するため、未 commit の変更でこの実 repo binding を取得する test は drift 赤になり得るが、変更を commit して disk と HEAD を一致させれば整合する。
焦点走 4 file には当該実 repo loader 比較は見当たらない。fixture 内の Git/blob 検証とは区別し、先例 §4 の commit 前成功とも整合する。loader 比較を含む受入全走は commit 後に行う。

## 総括

実装は **contract.py の 3 行追加と独立包含 test 1 本**で足りる。P1・P2・P3・P5 は採用し、P4 は script の限定的な独立列挙が存在するという表現に訂正する。

親へ返す主要所見は、verifier directory が 9 file であり、今回の追加後も 2 file が集合外に残ること。静的確認では consumer の追加修正は不要。次段では上記変異を事前登録し、実装後に指定 4 file の焦点走と変異検査、commit 後の受入全走で確認する。