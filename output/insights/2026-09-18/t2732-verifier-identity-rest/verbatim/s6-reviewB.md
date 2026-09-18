## 所見

**R-B1 — 実装子の波及列挙に、焦点走外の consumer test 7 群の明示が不足している。**

- **主張:** コードの修正漏れは認めないが、`s5-author.md:70–78` だけでは受入全走で確認すべき参照関係を追えない。先例レビュー B の nit 1 と同じ不足が残る。
- **根拠:** `contract.py:79–81` の diff は次の逐語であり、集合と contract の bytes を変更する。

```diff
+    "orchestrator/verifier/__init__.py",
+    "orchestrator/verifier/commit_receipt.py",
+    "orchestrator/verifier/report.py",
```

焦点走外には、現物で確認できる次の参照がある。表内の test と fixture は `orchestrator/tests/` 配下。

| consumer test / fixture | 参照関係 |
|---|---|
| `test_t126_qualification_artifacts.py:42` | contract の `canonical_json_bytes`、`load_protocol` を import |
| `test_floor_submit_receipt.py:14` | contract の `canonical_json_bytes` を import |
| `test_official_perf_closure.py:85,252,379,829` | contract のソースと `series_identity` の述語を検査 |
| `test_t671_source_binding.py:97` | contract を loader 閉包に列挙 |
| `test_campaign_lock_codec.py:77` | contract を loader blob 集合に列挙 |
| `test_artifact_admission.py:341,579` | contract を loader 閉包に列挙 |
| `test_campaign.py:89` → `certified_writer_fixtures.py:12,81,161,190` | fixture 経由で contract の正規化、protocol 読込、attempt identity を使用 |

- **重さ:** nit。
- **是正案:** 親の検証記録に上記 7 群を補記し、commit 後の受入全走の結果を焦点走と分けて記録する。実装 patch の変更は不要。

これらは通常の受入全走で覆える。現行の `orchestrator/test_selection_contract.py:61` は `SANCTIONED_EXCLUSIONS = ()`。contract は既存の loader 閉包 member であり、今回変わるのはその blob であって閉包の構成員ではない。commit 後の clean な隔離 worktree で確認する方針は妥当である。

**直接 consumer の全出現箇所と追随判定**

以下は定数名の production/test における全出現。import・コメントを含めて 6 file、27 箇所。

| ファイルと行 | 用途・判定 |
|---|---|
| `orchestrator/qualification/contract.py:39,536` | 定義と exact key set 検査。43-key へ追随 |
| `orchestrator/qualification/identity.py:27,140` | import と code/script 和集合検査。46-path へ追随 |
| `orchestrator/qualification/t126_driver.py:64,372` | import とソート列挙。追加 3 path の disk/HEAD blob 照合、hash 格納へ追随 |
| `orchestrator/tests/test_t126_qualification_contract.py:21,76` | import と集合由来 fixture。追随 |
| `orchestrator/tests/test_t419_probe_causality.py:38,42` | import と既存部分集合検査。修正不要 |
| `orchestrator/tests/test_t126_pegasus_tools.py:704,980,1085` | import、fixture ファイル生成、blob hash 生成。追随 |
| 同 `:1026` | adapter が集合外である旨のコメント。修正不要 |
| 同 `:1486,1487,1519,1522` | 既存要素の包含・禁止ディレクトリ検査。修正不要 |
| 同 `:1528,1529,1530,1531` | 既存 verifier 4 path の包含検査。修正不要 |
| 同 `:1535,1536,1537` | 今回追加した独立包含検査 |
| 同 `:1547,1560` | 集合同士の比較と tracked parameter 生成。追随 |

docs の直接出現は以下。いずれも実行時の集合の複製ではなく、決定・歴史記録なので書換え不要。

- `docs/decisions.md:5478,64321,65979`
- `docs/archive/worklog-phase3-0801-100.md:94`
- `docs/archive/worklog-phase3-0810-377.md:41`
- `docs/archive/worklog-phase3-0812-496.md:9`
- `docs/archive/worklog-phase3-0816-587.md:21`
- `docs/archive/worklog-phase3-0917-1617.md:708`

`output/` の出現は過去の計画・レビュー・変異台帳等の記録であり、現行定数を読み込む consumer ではない。

shell に定数名の直接参照はない。`tools/pegasus/submit_t126_qualification.sh:124,149` の固定列挙は入口の部分検査であり、required code 集合全体の複製ではない。同 `:141` の `git archive` は `orchestrator` 全体を取得するため、新 3 path も取り込む。`tools/pegasus/t126_qualification.sh:790` の列挙は prologue 用の部分証跡であり変更不要。

間接 consumer も追随する。`submission.py:216` は `build_series_preimage()` 経由、`collector.py:358,473,1168,1487,1515` と `artifacts.py:1291` は identity 契約関数経由である。これらについて実装子の報告は妥当。

**部分 fixture は新集合と衝突しない。**

`test_t126_qualification_driver.py:98` の `_prologue_value()` は `_verify_prologue_evidence()` 単体用。`t126_driver.py:953` は code/script 辞書を合成し、`:964–973` で必要な 5 path を参照する。この関数内では `series_identity()` の exact 集合検査を呼ばない。

実処理では別途 `t126_driver.py:1029,1437` で完全な series identity を検査するため、部分 fixture を 43-key に拡張する必要はない。

**tracked 検査は隔離 worktree でも成立する。**

`test_t126_pegasus_tools.py:1573` の検査は、自身の配置から求めた `_ROOT` に対して `git ls-files --error-unmatch` を実行する。新 3 path と N4 の `cli.py` は、現 index と HEAD `eb0f38969` の tree の双方に mode `100644` の通常 blob として存在する。同 HEAD から作る Git worktree で tracked と判定できる。

## 変異 spec の照合表

spec の SHA-256 は次と一致した。

```text
d292686f1e4ec16289f67e1ede4c63d4d16c0f4f08a8cf174e24bbd41d416cf8
```

各 replacement を独立して `git show eb0f38969:<file>` に照合した。複数行 `old` 全体の完全一致数は全件 **1**。構成行も `grep -Fnx` で位置を確認した。対象 2 file の作業ツリー内容は HEAD と一致する。

**V** は以下の node。spec の文字列と HEAD の関数名は文字どおり一致し、定義は 1 個。

```text
orchestrator/tests/test_t126_pegasus_tools.py::test_required_code_identity_includes_verifier_init_report_commit_receipt
```

| ID | HEAD の anchor 行 | old 出現数 | code 件数 | 静的に予測する失敗 node 完全集合 | 登録との整合 | 既存 test だけで検出 |
|---|---|---:|---:|---|---|---|
| N1 drop-init | `contract.py:78–79` | 1 | 42 | `{V}` | KILLED と一致 | なし |
| N2 drop-report | `contract.py:80–81` | 1 | 42 | `{V}` | KILLED と一致 | なし |
| N3 drop-commit-receipt | `contract.py:79–80` | 1 | 42 | `{V}` | KILLED と一致 | なし |
| N4 report-to-cli-sibling | `contract.py:81` | 1 | 43 | `{V}` | KILLED と一致 | なし |
| N5 commit-receipt-to-core-duplicate | `contract.py:80` | 1 | 42 | `{V}` | KILLED と一致 | なし |
| E1 equivalent-test-comment | `test_t126_pegasus_tools.py:1534` | 1 | 43 | 空集合 | SURVIVED と一致 | 該当せず |

これは指定の焦点走 4 file に限定した静的予測であり、変異実走の観測結果ではない。

**N4:** 新たに生成される次の node は緑になると判断する。

```text
orchestrator/tests/test_t126_pegasus_tools.py::test_every_required_identity_path_is_tracked_in_this_repo[orchestrator/verifier/cli.py]
```

`cli.py` は tracked。`_attempt()` は集合から相対 path ごとに fixture を生成して commit するため、こちらでも欠落しない。V が `report.py` の脱落を検出する。新しい parameter node を `expected_nodes` に入れない登録は正しい。

**N5:** `frozenset` が既存 `core.py` との重複を除去し、`commit_receipt.py` が失われて 42 要素となる。既存の core 包含検査は緑のまま。`test_series_preimage_exact_code_identity_set_tracks_activation_closure` は `_attempt()` が生成した辞書と同じ集合を比較するため追随し、その後に削除する activation path も変わらない。既存 test の追加失敗は予測しない。

**新規検出力:** 今回の N1〜N5 に、既存 test 単独で落ちる変異は見つからない。存在しない path への置換を使った先例の初回 N5 と異なり、今回の N4 は tracked sibling への置換である。ただし新 test が証明するのは 3 path の包含であり、verifier の判定能力や集合外要素の全面禁止ではない。

**E1:** この焦点集合に対して等価と判断する。追加コメントは production bytes、集合、assert、関数名を変更しない。自身の test file を読む `test_fr3_mutation_node_registry_is_exact_and_complete` (`test_t126_pegasus_tools.py:6234`) も確認した。同 test は AST の関数名集合と既存 mutation anchor を検査し、行番号や test file 全体の hash は比較しない。今回のコメントでは検査対象は変わらない。

## 総括

**must-fix 0、should 0、nit 1。実装・consumer の追随・変異 spec に静的な不整合は見つからなかった。**

HEAD `eb0f38969` の親との差分は、提示された `s5-implementation.diff` とバイト一致し、2 file・9 行追加のみ。集合は **40/3/43 → 43/3/46**。新 test 1 node と tracked parameter 3 node の増加により、焦点走の **485 → 489、差分 +4** と一致する。差分から別の増減要因は認めない。ただし、提示ログは要約行なので node 単位の実測比較ではない。

必読 4 file と `s5-author.md` は読了。ファイル変更・pytest 実行は行っていない。親による変異実走と commit 後の受入全走は引き続き必要であり、その結果を先取りして成功とは判定していない。