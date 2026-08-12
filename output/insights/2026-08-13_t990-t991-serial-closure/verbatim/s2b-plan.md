## 推す設計

推奨は「案 A+B: fail-closed fixture 閉包 + AST 資源 witness 固定点解析」。

配置先は `orchestrator/tests/test_real_repo_serialization.py` とする。

- `:360-433` の `_collect_xdist_group_report()` を拡張し、既存 1 回の collection JSON に各 item の fixture 閉包と fixture 定義元 `(path, function, lineno)` を追加する。
- `_build_real_resource_ast_index()`、`_derive_real_resource_contact_nodes()`、`_assert_real_resource_contacts_covered()` を追加する。
- 新しい subprocess は増やさず、`:567` の `test_real_repo_group_collection_exactly_matches_canonical_nodes()` 内で新検査と positive control を実行する。
- 追加量は約 200〜260 行。内訳は collection 情報追加約 30 行、AST・固定点解析約 150〜200 行、assert/control 約 20〜30 行。
- AST は `ROOT`、`_ROOT`、`K.ROOT` から実 root を識別し、`"external"/"ccbench"`、`patchharness.checkout`、`build_snapshot`、`K.build_document` 等への到達を追う。repo 内 import alias、通常の helper 呼出し、fixture 依存、`prepare_fn=prepare_cell` のような callable 引渡しを、深さ制限なしの固定点まで伝播する。
- 手書きの「資源 fixture 名リスト」は置かない。collection が返した有効 fixture 定義を AST 結果へ照合して自動生成する。
- 残る小さな witness 登録簿は双方向に守る。各登録規則が実ソースへ最低 1 件一致すること、および root/path/sensitive-call 候補がすべて `real` または機械的に証明された `tmp/hermetic` へ分類されることを検査し、未分類・解決不能は赤にする。
- `item._fixtureinfo.names_closure` / `name2fixturedefs` がない、型が変わった、資源 fixture の定義元を一意に取れない場合は subprocess 内で明示的に例外とする。空集合へフォールバックしないため、pytest private API の変更は fail-open せず赤になる。
- 最終条件は `derived_nodes <= REAL_REPO_SERIAL_NODES` とする。既存正本には保守的に残す node があるため逆包含は要求しない。正本と golden の完全一致は既存検査へ残す。

この検査自身は実 worktree の Python source を読み、実 suite を collection する。そのため  
`test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes` 自体も `REAL_REPO_SERIAL_NODES` と独立 golden へ追加する必要がある。親確定の 20 node と合わせて 21 node の追加となる。検査自身が導出集合にも現れることを assert し、手書き追加だけで済ませない。

弱点は、reflection、動的 `getattr`、実行時生成された import/path が、root・path・sensitive-call の全 witness を避けた場合である。その完全性までは AST で保証できない。認識済み witness から動的 edge に入った場合は未解決として赤にするが、未知の構文体系そのものは将来の witness 追加が必要になる。

## 3 系統の検出可否

- 系統 1: 検出可能。AST が `real_known_axes_doc` の `K.build_document()` を資源 fixture と導出し、collection の `freeze_env → real_known_axes_doc` 閉包から消費 11 node を得るため、正本外の確定 1 node が差分になる。
- 系統 2: 検出可能。`prepare_cell → patchharness.checkout(...実 external/ccbench...)` を固定点で taint し、その callable を `prepare_fn=` へ渡す 2 test node を直接導出する。
- 系統 3: 検出可能。`benchmark_snapshots` の `TOOL.build_snapshot(_ROOT, ...)` を資源 fixture と判定し、collection が返す有効 fixture 閉包から module setup の支払順に依存せず 17 node 全件を導出する。

## positive control の形

`CONTROLS` は系統 1 の確定漏れ、系統 2 の最初の canary、系統 3 の `test_parent_numstat_controls_remain_pinned` をそれぞれ指す。これは control 用の選択であり、導出集合の入力にはしない。

```python
report = _collect_xdist_group_report(HERE, cwd=ROOT)
by_kind = _derive_real_resource_contact_nodes(report, ROOT)
configured = set(_load_suite_conftest().REAL_REPO_SERIAL_NODES)
_assert_real_resource_contacts_covered(by_kind, configured)
for kind, victim in CONTROLS.items():
    assert victim in by_kind[kind]
    broken = configured - {victim}
    with pytest.raises(AssertionError, match=re.escape(victim)):
        _assert_real_resource_contacts_covered(by_kind, broken)
```

実 collection と実 AST から得た同じ `by_kind` に対し、正本のコピーから 1 node だけ除く。同じ本番 assertion が赤になるため、合成 AST、恒真 assert、別機序の control ではない。

## 純増検出力と既存との重複

純増検出力は「正本にも独立 golden にも存在しないが、fixture 閉包または資源到達 AST から導出された node」を赤にすること。

- `test_real_repo_group_collection_exactly_matches_canonical_nodes`、2 本の xdist 負例、2 本の handwritten-marker 検査、priority 検査、loadgroup scheduler 検査は、正本・golden・marker・順序・配置を守る。導出後の membership/marker 確認は重複するが、両リスト外 node の発見は新設分だけである。
- `test_protocol_builder_repo_tree_guard_is_wired_to_real_root` と `test_ratified_memo_has_a_real_resolution_payer` は特定配線の実効性を守る。該当 node を新 AST が再発見する部分は重複だが、3 系統の閉包導出は行わない。
- tmpdir 関係の残り 5 関数は filesystem 種別と TMPDIR 結線の検査であり、本設計との重複はない。

## コスト見積り

想定は 1 回 5〜15 秒、うち新設 AST 部分の純増は約 1〜3 秒。未実測である。

根拠は次のとおり。

- `:567` が既に行う `pytest --collect-only` subprocess の report を拡張して再利用するため、collection 起動回数は増えない。
- 静的棚卸しでは対象 3 配下に Python file 425 件、合計約 15.7 MB。全件を上限としても AST parse と固定点集合演算は秒オーダーである。
- `.git`、commit 履歴、clone、build、実 submodule 内容は走査しない。したがって履歴・commit 数には比例せず、現行 worktree の Python source bytes と collected item 数だけに比例する。

## 却下した案とその理由

案 A 単独は却下する。系統 1 と 3 は fixture 閉包で取れるが、fixture を介さない系統 2 を導出できない。手書き fixture 登録簿も、新 fixture の追加や rename に対して drift する。

案 B 単独は却下する。固定点解析なら helper の段数制限は除けるが、pytest の override、autouse、module scope、parametrize を静的に再実装することになる。実 collection の有効 fixture 閉包とずれる危険が大きい。

案 C は却下する。全 node の setup/call を実行しなければ skip を含む接触集合を得られず、受入全走へ大幅なコストを加える。また `open`・`subprocess` 等を同一 run で観測するため観測者効果を導入し、絶対規律 1 に触れる可能性がある。

## 未確認のまま残した点

- pytest private API の現環境での具体的な fixturedef shape は、pytest を実行して確認していない。
- AST candidate 全件の false-positive 数と、tmp/hermetic と機械判定できない箇所は網羅していない。実装時に未分類を緑へ逃がさず、必要なら限定的な理由付き除外として裁定する必要がある。
- 5〜15 秒という値はソース量からの見積りで、実測値ではない。
- 静的検査のみであり、テストの緑は確認していない。
- 調査は 18/40 call で終了しており、予算到達によって打ち切った追加項目はない。

## 総括

既存 collection subprocess に fail-closed な fixture 閉包を同載し、AST の資源到達を深さ制限なしで伝播する A+B 混合を推す。これにより 3 系統すべてを正本・golden から独立して導出でき、正本から実導出 node を 1 件抜く同機序の positive controlで再発を赤にできる。