## 変更面

実装は 2 ファイルに限定する。以下の path はすべて指定 parent worktree 相対、行番号は変更前の現物。必読 2 ファイルと指定 repo ファイルは読めた。

| file | 行 anchor | 追加・変更する逐語 |
|---|---|---|
| `orchestrator/qualification/contract.py` | :75 `"orchestrator/verifier/core.py",` の直後、:76 の policy より前 | 下記 A の 3 行 |
| `orchestrator/tests/test_t126_pegasus_tools.py` | :1524 の既存包含 test 終了後、:1527 の preimage test より前 | 下記 B の独立 test 1 本 |

A:

```python
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
```

B:

```python
def test_required_code_identity_includes_verifier_core_dsg_model_parse():
    assert "orchestrator/verifier/core.py" in REQUIRED_CODE_IDENTITY_PATHS
    assert "orchestrator/verifier/dsg.py" in REQUIRED_CODE_IDENTITY_PATHS
    assert "orchestrator/verifier/model.py" in REQUIRED_CODE_IDENTITY_PATHS
    assert "orchestrator/verifier/parse.py" in REQUIRED_CODE_IDENTITY_PATHS
```

T316 の :1487 と同じ個別包含 assert を、T529 の :1505 と同じ独立 test として置く。期待 path を production 集合から導出しないため、4 file のどれを 1 個除去しても赤になる。import の追加は不要。

現物の AST を静的に数えた結果、code 集合は **37 → 40 件**。script 集合は 3 件のままで、両者の和集合は **40 → 43 件**。

## consumer 列挙

直接参照は production 3 ファイル、test 3 ファイル。識別子の出現は計 20 箇所で、定義 1、import 5、コメント 1、実際の読取り 13。script の直接参照は 0。

| consumer | 現物の行 | 追加後の挙動・対応 |
|---|---|---|
| `qualification/contract.py` | :39 定義、:530 使用、:533–534 検査 | `series_identity()` の exact key set が 40 件になる。集合以外の編集不要 |
| `qualification/identity.py` | :27 import、:140 使用 | :124 の `series_identity()`、:140–150 の集合検査と記録 commit blob の SHA256 再導出が自動追随 |
| `qualification/t126_driver.py` | :63 import、:359 使用 | :363–371 が新 3 path の存在・symlink・disk hash と指定 commit blob の一致を検査し、code identity に格納。編集不要 |
| `tests/test_t126_pegasus_tools.py` | :704 import、:980 使用 | `_attempt` が新 3 path を生成。下記のとおり追加分岐不要 |
| 同上 | :1085 使用 | fixture commit の各 blob から SHA256 を生成。自動追随 |
| 同上 | :1486、:1487 | reservation policy と build admission の個別包含。純増で維持 |
| 同上 | :1519、:1522 | activation 閉包の包含と records 除外。純増で維持 |
| 同上 | :1534 | fixture preimage と required 集合の等価。双方が自動追随 |
| 同上 | :1547 | tracked-path test の parameter が 3 個増加 |
| `tests/test_t126_qualification_contract.py` | :21 import、:76 使用 | `_series_preimage()` の辞書内包が自動追随 |
| `tests/test_t419_probe_causality.py` | :38 import、:42 使用 | 既存閉包の部分集合 assert。純増で維持 |

`test_t126_pegasus_tools.py:1026` は adapter の意図的除外を説明するコメントで、読取りではない。

`_attempt` の新 3 path は :983–1023 の特殊分岐に該当せず、:1024–1025 で次の bytes を生成する。

```python
path.write_text(f"fixture {relative}\n", encoding="utf-8")
```

:1050–1051 で fixture repository に commit し、:1085–1088 でその blob を hash する。したがって P4 は成立する。

間接 consumer も追加対応不要。

- `qualification/t126_driver.py:407` は `_identity_files()` を呼び、:1376 は `verify_recorded_series_identity()` を呼ぶ。
- `qualification/collector.py:39,1515` は同 verifier を import・呼出しするため、新集合の検査に追随する。
- `tools/pegasus/submit_t126_qualification.sh:124–134` には **独立した 5 path の追跡検査が存在する**。ただし identity 全集合の複製ではなく、実行入口の限定列挙で、既存 `core.py` も含まない。:142–144 は `orchestrator` 全体を archive するため、新 3 path 用の編集は不要。後段の identity 検査は driver が担う。

## 既存 test の影響

| test／生成箇所 | 静的判定 |
|---|---|
| `test_every_required_identity_path_is_tracked_in_this_repo` (:1545–1566) | parameter node は 40 → 43。新 3 path は `git ls-files --error-unmatch` で追跡済みと確認した |
| `test_series_preimage_exact_code_identity_set_tracks_activation_closure` (:1527–1542) | :1534 の等価比較は維持。fixture と期待集合が双方増える。activation leaf を落とす既存負例も引き続き mismatch |
| `test_t126_qualification_contract.py:76` | preimage が 40 key に自動追随。:279 の toolchain test も更新済み preimage を使うため、旧集合による失敗は生じない |
| `test_t419_probe_causality.py:42` | 部分集合 assert のため維持 |
| 新規包含 test | 旧 production 集合では `dsg.py` の assert で赤。3 path 追加後に通る想定 |

指定された既存 test に、この純増を原因とする失敗は静的には見当たらない。ただし集合から生成する既存 test だけでは、production 集合からの誤削除に追随してしまうため、新規の独立した包含 assert が必要。

過去の 37 key preimage を新コードへ渡すと、`contract.py:533–534` の `series identity code_identity required set mismatch` になる。歴史成果物の書換え・互換化は行わず、P2 の条件どおり据え置く。

## 変異候補

段 4 で親が事前登録する候補。各変異は独立に適用する。

以下の `V` は、この完全な test node id を指す。

```text
orchestrator/tests/test_t126_pegasus_tools.py::test_required_code_identity_includes_verifier_core_dsg_model_parse
```

| ID | tracked 行への変異 | 殺すはずの test node id／期待 |
|---|---|---|
| N1 | `contract.py` の新 `dsg.py` 行を除去 | `V`、dsg の assert で失敗 |
| N2 | 同、新 `model.py` 行を除去 | `V`、model の assert で失敗 |
| N3 | 同、新 `parse.py` 行を除去 | `V`、parse の assert で失敗 |
| N4 | 同、既存 `core.py` 行を除去 | `V`、core の assert で失敗 |
| N5 | 同、`"orchestrator/verifier/parse.py"` を `"orchestrator/verifier/par se.py"` に変更 | `V`、正しい parse path が欠けて失敗 |
| N6 | 同、新 `model.py` 行を `"orchestrator/verifier/core.py",` に置換 | `V`、model の assert で失敗。frozenset の重複により 40 → 39 件 |
| N7 | 新規 test の dsg assertion だけ `in` を `not in` に変更 | `V`、正常な production 集合に対して失敗 |
| E1 | 新規 test の定義行に `# T-1209 verifier identity coverage.` を追加 | `V` は通過する想定。コメントだけの等価変異 |

N7 と E1 の対象は、新規 test を追加する既存 tracked file `test_t126_pegasus_tools.py`。別 test file は新設しない。N7 は test 自体の反転を検出する確認であり、production 欠落を検出する根拠は N1–N6 と区別する。

E1 を test 側へ置く理由は、`contract.py` のコメント変更でも code identity と loader blob の bytes は変わるため。test 側なら、それらの identity 入力を変えない等価対照になる。

## scope 外と残る穴

以下は変更しない。

- `verifier/__init__.py`、`report.py`、`commit_receipt.py` の identity 追加。
- census gate、歴史成果物の互換層、新たな台帳・一般化。
- `schema_version`、hash domain、`series_identity()` の検証ロジック。
- `REQUIRED_SCRIPT_IDENTITY_PATHS`、campaign_lock 閉包、凍結 manifest。
- verifier の判定・受理集合の意味論。

P1 の残る穴: `pipeline.py:39` の package dispatch、`core.py:25,256` の report projection、`core.py:24,264` と `artifacts.py:24,856` の receipt 処理は、除外 3 file の実装に依存する。これらは今回も T126 の個別 `code_identity` hash に直接入らず、verifier import 閉包の完全な束縛にはならない。superproject commit/tree と兄弟 loader 閉包の束縛とは区別し、追加裁定の材料として親へ返す。

P3 は成立する。新規 test は repo の包含不変条件だけを検査し、新しい実行時 gate を設けない。

## loader 閉包の影響

`campaign_lock.py:107` は `contract.py` を含み、実際の HEAD blob と disk の比較は `contract_loader_binding.py:518–531` にある。未 commit の編集は `contract-loader-drift` を起こすが、commit 後の新 binding は更新 blob と整合し、歴史 lock は更新しない。

実 repo を読む `test_p3_b4_raw_record_producer.py:110–112` の `_writer_authority()` に到達する test は未 commit 状態で失敗し得る。一方、`test_t671_source_binding.py:321–325,443–459` は fixture repo を作成・commit して比較するため、親 worktree の未 commit 差分だけでは失敗しない。

補助探索で想定した `test_contract_loader_binding.py` と `test_campaign_lock.py` は存在せず、上記の実在箇所で確認した。指定された必読・repo ファイルの欠落はない。

## 総括

実装は **frozenset への 3 行追加と、4 file を個別に assert する独立 test 1 本**で完結する。consumer・fixture・指定既存 test の追加修正は不要。submit script の独立列挙は存在するが、identity 全集合ではないため変更しない。

本段では読取りと静的検査のみ実施し、ファイル書込み・pytest・変異実行は行っていない。親は上記変異を事前登録し、実装後に関連 test と受入全走を実施する。loader の実 repo 比較を含む検証は、実装 commit 後に評価する。