## 所見

**R-B1 — 実装子の波及列挙には、焦点走外の consumer test の明示が不足している。**

- **主張:** 実装の修正漏れは認めないが、`s5-author.md:66` 以降の列挙だけでは受入全走の確認対象を追えない。
- **根拠:** diff の `+"orchestrator/verifier/dsg.py",`、`+"orchestrator/verifier/model.py",`、`+"orchestrator/verifier/parse.py",` は `contract.py` の bytes と定数を変更する。焦点走外にも次の参照がある。

| consumer test / 補助 fixture | 参照関係 |
|---|---|
| `orchestrator/tests/test_t126_qualification_artifacts.py:42` | contract の `canonical_json_bytes`、`load_protocol` を import |
| `orchestrator/tests/test_floor_submit_receipt.py:14` | contract の `canonical_json_bytes` を import |
| `orchestrator/tests/test_official_perf_closure.py:85,252,379,829` | contract のソースと `series_identity` の述語を棚卸し |
| `orchestrator/tests/test_t671_source_binding.py:97` | contract を loader 閉包の対象として列挙 |
| `orchestrator/tests/test_campaign_lock_codec.py:77` | contract を loader blob 集合に列挙 |
| `orchestrator/tests/test_artifact_admission.py:341,579` | contract を loader 閉包に列挙 |
| `orchestrator/tests/test_campaign.py:89` → `certified_writer_fixtures.py:12,81,161,190` | fixture 経由で contract の正規化、protocol 読込、attempt identity を使用 |

  定数追加によってこれらの期待値を変更する必要は静的には見つからない。loader 閉包の**構成員**も変更されないが、contract の blob は変わる。
- **重さ:** nit。
- **是正案:** 親の検証記録に上記の参照関係を補足し、受入全走の結果を焦点走とは別に記録する。

**直接 consumer の全出現箇所と追随判定**

以下は `REQUIRED_CODE_IDENTITY_PATHS` の repository 内検索結果。import・コメントも含む。

| ファイルと行 | 用途・判定 |
|---|---|
| `orchestrator/qualification/contract.py:39,533` | 定義と exact key set 検査。40-key へ追随 |
| `orchestrator/qualification/identity.py:27,140` | import と code/script 和集合検査。43-path へ追随 |
| `orchestrator/qualification/t126_driver.py:63,359` | import とソート列挙。新 3 path の disk/blob 照合と hash 格納へ追随 |
| `orchestrator/tests/test_t126_qualification_contract.py:21,76` | import と集合由来 fixture。追随 |
| `orchestrator/tests/test_t419_probe_causality.py:38,42` | import と既存部分集合検査。修正不要 |
| `orchestrator/tests/test_t126_pegasus_tools.py:704,980,1085` | import、fixture ファイル生成、blob hash 生成。追随 |
| 同 `:1026` | adapter が集合外である旨のコメント。修正不要 |
| 同 `:1486,1487,1519,1522` | 既存要素の包含・禁止ディレクトリ検査。修正不要 |
| 同 `:1528,1529,1530,1531` | 今回追加の独立した包含検査 |
| 同 `:1541,1554` | 集合同士の比較と tracked path の parameter 生成。追随 |
| `docs/decisions.md:5478` | 過去の整理方針の記述。全集合の複製ではない |
| `docs/archive/worklog-phase3-0810-377.md:41` | 別変更集合との共通部分の記録 |
| `docs/archive/worklog-phase3-0816-587.md:21` | 対象集合の記録 |
| `docs/archive/worklog-phase3-0812-496.md:9` | submission 自己包含の記録 |
| `docs/archive/worklog-phase3-0801-100.md:94` | 過去の整理方針の記録 |

shell に定数名の直接参照はない。`submit_t126_qualification.sh:149` の 7-path 検査は入口の個別照合であり、全集合の複製ではない。同 `:141` の `git archive` は `orchestrator` 全体を取得するため、新 3 path も取得される。`submission.py:216` は `build_series_preimage()` 経由で追随する。`t126_qualification.sh:787` 以降は prologue 用の部分証跡であり変更不要。

**3-key fixture は衝突しない。** `test_t126_qualification_driver.py:98` の `_prologue_value()` は `_verify_prologue_evidence()` 単体用。`t126_driver.py:882` は code/script を合成し、`:892` 以降で必要な 5 path の値を参照するだけで、ここでは `series_identity()` の exact 集合検査を呼ばない。実処理では別途 `:957,1365` に identity 検証がある。実装子のこの説明は妥当。

**tracked 検査も隔離 worktree に対応できる。** `test_t126_pegasus_tools.py:1556` は自身の配置から求めた `_ROOT` に対して `git ls-files --error-unmatch` を実行する。新 3 path は現 index だけでなく HEAD `c09211d17` の tree にも通常 blob として存在することを確認した。同 HEAD から作る Git worktree では tracked と判定できる。

## 変異 spec の照合表

各 replacement を**独立して** `git show HEAD:<file>` に照合した。全件 `old` はちょうど 1 回出現し、対象 2 ファイルの disk 内容も HEAD と一致した。

略号:

- **V** = `orchestrator/tests/test_t126_pegasus_tools.py::test_required_code_identity_includes_verifier_core_dsg_model_parse`
- **P[pars.py]** = `orchestrator/tests/test_t126_pegasus_tools.py::test_every_required_identity_path_is_tracked_in_this_repo[orchestrator/verifier/pars.py]`

| ID | old 出現数 | 静的に予測する失敗 node 完全集合 | 登録との整合 | 既存 test だけで検出 |
|---|---:|---|---|---|
| N1 drop-dsg | 1 | V | 一致、KILLED 予測 | なし |
| N2 drop-model | 1 | V | 一致、KILLED 予測 | なし |
| N3 drop-parse | 1 | V | 一致、KILLED 予測 | なし |
| N4 drop-core | 1 | V | 一致、KILLED 予測 | なし |
| N5 misspell-parse | 1 | V、P[pars.py] | 一致、KILLED 予測 | **あり** |
| N6 model-to-core-duplicate | 1 | V | 一致、KILLED 予測 | なし |
| E1 equivalent-test-comment | 1 | 空集合 | 一致、SURVIVED 予測 | 該当せず |

これは指定の 4-file 焦点集合に限定した静的予測であり、変異実走の観測結果ではない。

N1〜N4/N6 では、`_attempt()` のファイル生成 (`:980`) と hash 生成 (`:1085`)、contract test の fixture (`:76`)、tracked parameter (`:1554`) が同じ変更後の集合へ追随する。既存の独立した部分集合検査は verifier 4 path を要求しない。N6 は frozenset の重複により model が消え、39 要素になる。

**N5 の KILLED 自体は新規検出力に数えない。** 新テストがなくても P[pars.py] が存在しない tracked path を検出する。V の追加失敗は冗長な検出経路である。

**E1 はこの焦点集合に対して等価。** コメント追加は production bytes を変更しない。test 自身を読む `test_fr3_mutation_node_registry_is_exact_and_complete` (`test_t126_pegasus_tools.py:6228`) も AST の関数名と mutation anchor を検査しており、追加コメントではそれらが変わらない。T126 identity 集合と campaign loader 閉包にも、この test ファイルは含まれない。

## 総括

**must-fix なし。実装・consumer の追随・変異 spec に静的な不整合は見つからなかった。** 指摘は実装子の検証対象列挙を補う nit 1 件。

`s5-focus-run.log:23` は **461 passed in 22.82s**、`:11` は child rc=0。FAILED 行はなく、実装起因か loader drift かを分類すべき失敗 assertion はない。末尾の `recording-unavailable:series-invalid` は pytest の FAILED ではなく、これだけから回帰とは判定できない。

必読 4 ファイルと `s5-author.md` は読了。pytest・変異走・受入全走は本レビューでは実行していない。親の変異実走と受入全走による確認は残る。