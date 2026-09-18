## brief 訂正

以下の行番号は指定 worktree の現物基準。`C` は `orchestrator/campaign/autonomous_trial_completeness.py`、`T` は `orchestrator/tests/test_autonomous_trial_completeness.py`、`P` は `orchestrator/campaign/p3_autonomous_workload_trial.py` を指す。

| 事実 | 検証・訂正 |
|---|---|
| F1 | 内容は一致。producer 定数は `P:142`、role payload での使用は現物では `P:2926`、run-start は `P:5107-5139`。 |
| F2 | `a506633ef`・`4c6f03048`・HEAD の run-start 生成を比較し、無条件3 key・条件付き4 keyの追加、および v4 導入時と HEAD の key 集合一致を確認。**現行形は journal の `seq`・`ts` を含め非 binding 時16 key、binding 時23 key**。「新形20 key」は現行形の説明として不正確。 |
| F3 | `C:2240-2241` が版を直接照合する。`trial_registry.py:5967-5993` と `s8c_acceptance_receipt.py:1496-1506` は、それぞれ binding field と `arm_execution` を検査し、その箇所では版を照合しない。 |
| F4 | 4本にあるのは lifecycle の `run_start_receipt_sha256`。journal の run-start 版検査を追加する対象ではない。「当初の6本が grep 先頭6件由来」という起草経緯そのものは現物から確定できない。 |
| F5 | 指定 artifact の **2行目**に v3・13 key の run-start が存在する。`orchestrator`・`tools` の Python ソースで当該 artifact 名への直接参照は検出しなかった。ただし「repo 全体で唯一」「動的な読み手も皆無」「v3 新形記録は皆無」までは今回独立に証明していない。親調査の探索範囲を付記すべき。 |
| F6 | `T:476-494` は v4・16 key・binding なし。`T:2007-2012` の既存正例がこの fixture を通す。さらに後述の producer 統合正例が存在する。ただし今回テストを実行した意味での「通った」ではない。 |
| F7 | run-start の旧文言を固定するのは `T:2893-2907` と `T:2910-2928` の2関数。report 側の文言も同居しているため、**run-start 側だけ更新**する。現行2ファイルの SHA-256 は `output/`・`docs/` の検索で hit なし。契約 JSON の398行付近は path・field_paths の参照である。 |
| F8 | `C:427` と `s8c_generation_projection.py:18` の独立定義を確認。ただし「run-start 側だけが producer 定数を見る」は role との比較に限定した記述。同じ関数の **report 版も `C:2238-2239` で producer 定数を見る**。 |

追加の訂正：

- P5 の「共有定数が根本原因」は強すぎる。共有は role 改版を run-start に波及させる要因だが、今回直接修正する問題は **consumer の読める版が現行 producer 定数に追随してしまうこと**。
- 成果物を「検査2行」と固定しない。旧世代と未知版を区別する診断には、局所的な分岐と文言組立てが必要。
- D1851 は「形を変えない bump は禁止」とまでは述べていない。v5 を提案しない根拠は、現在の v4 に対する新たな形変更がなく、今回の目的を consumer の修正で満たせることである。

## P1〜P7 の判定

| 裁定 | 判定 | 理由・条件 |
|---|---|---|
| P1 | **条件付き同意** | v5 は不要。4c6f03048 により run-start にも v4 が出るため、旧 v3 と現行出力を区別する版境界は既にある。ただし「T-1170／D1898 の対応として当時完了した」とは記録せず、既存 bump を今回利用し、正例と consumer 契約を明示して残課題を閉じる。v3 内に既に存在した形の混在を遡及的に解消したとも言わない。 |
| P2 | **同意** | consumer 所有の独立リテラル定数を使う。現時点の版に関する受理集合は変更前後とも `{v4}`。旧版を変換・受理せず、その記録が旧世代であることを診断する実装なら「互換層なし」に適合する。 |
| P3 | **同意** | D1898 が参照する D1669 の本文は「実在成果物と読み手」が条件。v3 artifact の存在だけで decoder を追加しない。「旧版として読む」はここでは版の識別と拒否理由の提示であり、旧契約の内容検証を行ったとは表現しない。 |
| P4 | **同意** | 4本は別種の receipt。trial_registry／acceptance への新規版 gate も今回の修正には不要。 |
| P5 | **条件付き同意** | producer は変更しない。ただし根本原因の説明は上記のとおり訂正する。producer 定数分離は別論点。 |
| P6 | **同意** | report 版照合は据え置く。1関数内の統一より、今回指定された run-start の境界を優先する。これにより「過去 run 全体が現行 producer から独立して再検証できる」とは主張しない。provider・budget も `C:2253-2254,2289` で producer に依存する。 |
| P7 | **同意** | 既存 producer 統合正例で担保できる。静的な定数比較 gate は追加しない。具体的な nodeid は次節に示す。 |

## 実装プラン (file:line)

| file / 行範囲 | 変更前の要旨 | 変更後の要旨 | 理由 |
|---|---|---|---|
| `C:426-428` | role の consumer 版定数だけ存在 | `_ROLE_SCHEMA_VERSION` の直後に `_RUN_START_SCHEMA_VERSION = "p3-autonomous-workload-trial/v4"` を追加 | run-start の読める世代を独立所有する。producer／role 定数への代入参照にしない。 |
| `C:2240-2241` | producer の `SCHEMA_VERSION` と比較し、一律の不一致文言 | 下記の局所分岐へ置換 | 受理版を固定し、記録版・世代分類・consumer 対応版を示す。 |
| `T:2892-2907` | report／start の欠落を旧文言で期待 | start のみ `recorded=None; generation=unknown` の全文期待へ変更 | 欠落も fail-closed。report 分岐は維持。 |
| `T:2910-2928` | v3 の版名を付けた現行形を旧文言で拒否 | start のみ `generation=legacy` の全文期待へ変更 | 現行形でも版が v3 なら拒否する負例を残す。既存の版リテラル assert は変更不要。 |
| `T:2928` の後 | binding なし・旧形・未知版の専用 test なし | 次節の3 test を追加 | D1898 正例と世代別診断を明示する。 |

版検査の具体案：

```python
recorded_version = start.get("schema_version")
if recorded_version != _RUN_START_SCHEMA_VERSION:
    generation = (
        "legacy"
        if recorded_version == "p3-autonomous-workload-trial/v3"
        else "unknown"
    )
    _fail(
        "run-envelope",
        "run-start.schema_version unsupported: "
        f"recorded={recorded_version!r}; generation={generation}; "
        f"consumer_supported={_RUN_START_SCHEMA_VERSION!r}",
    )
```

期待される例外全文：

```text
[run-envelope] run-start.schema_version unsupported: recorded='p3-autonomous-workload-trial/v3'; generation=legacy; consumer_supported='p3-autonomous-workload-trial/v4'
```

未知版では `recorded='p3-autonomous-workload-trial/v99'; generation=unknown`、欠落では `recorded=None; generation=unknown` とする。実在を確認した v3 だけを旧世代と分類し、版番号の大小を解釈する一般化は加えない。

期待文言は test 側の独立リテラルで固定する。`pytest.raises(...) as exc` と `assert str(exc.value) == expected` を使えば、ピリオド等の regex 解釈を避けられる。

親が追記する `docs/failures.md:11313-11318` の直後への案：

> 恒久対応（T-1170）: 4c6f03048 で run-start にも導入済みの v4 を現行世代として、完全性 consumer が読める run-start 版を独立定数で固定した。現行 producer の版との直接照合をやめ、拒否理由に記録版・旧世代／未知の分類・consumer 対応版を明示する。受理する版は v4 のみで変更せず、v3 decoder・alias は追加しない。binding のない v4 正例、v3 旧形と未知版の負例、現行 producer の出力を再検証する既存統合正例で検出する。既存 artifact は書き換えず、旧成果物の再検証には生成時のコード版と契約を用いる。

実測結果は親が確認後に別途付記する。

## テスト計画

以下で `T::name` は `orchestrator/tests/test_autonomous_trial_completeness.py::name` の略記。

| nodeid | 内容 |
|---|---|
| `T::test_run_start_v4_without_binding_is_accepted`〔新規〕 | `_complete_trial` を使い、start の版が独立リテラル v4、無条件3 field が存在し、binding 7 field がすべて不在であることを確認して `_verify` を呼ぶ。 |
| `T::test_run_start_v3_legacy_shape_is_rejected`〔新規〕 | `_complete_trial` の start を v3 にし、`generation_driver`・`gating_spec_sha256`・`honest_accounting_authority` を削除。下記13 keyの集合と一致することを確認し、`_persist` 後、旧世代の例外全文を期待する。 |
| `T::test_run_start_unknown_schema_version_is_rejected`〔新規〕 | 現行形の版だけ v99 に変更。`_persist` 後、未知版の例外全文を期待する。 |
| `T::test_report_and_run_start_schema_versions_are_required[start]`〔更新〕 | 欠落版を `recorded=None; generation=unknown` と診断する。 |
| `T::test_role_schema_v4_and_report_schema_v3_are_required`〔更新〕 | **v3＋現行形**を引き続き拒否し、旧世代文言を固定する。report 側も従来どおり検査する。 |

旧形13 key：

```text
event, schema_version, trial_id, provider, workloads,
generation_budget_per_workload, max_wall_s, do_build,
performance_early_stop, scientific_claim, launch_admission, seq, ts
```

これは実在 artifact の **key 形を再現する合成負例**。記録済み artifact を変更したり、旧 report 全体を現行 fixture に移植したりしない。

binding なし正例で不在を確認する7 field：

```text
prereg_commit, prereg_content_commit, prereg_effective_commit,
slot_id, measurement_head, manifest_sha256, arm_execution
```

同期を担う既存統合 nodeid：

```text
orchestrator/tests/test_p3_autonomous_workload_trial.py::test_transport_admission_error_persists_verified_partial_report
```

`3038-3098` に存在し、`A.run_trial` の現行出力を保存した後、`completeness.verify_autonomous_trial_files` で再検証する。consumer の版検査を stub 化しておらず、binding のない実生成出力を使う。ここでの「実走」はテスト内で producer を実行する意味で、transport や性能測定の本走ではない。

通常完走側の補助正例：

```text
orchestrator/tests/test_p3_autonomous_workload_trial.py::test_fixture_trial_runs_ycsb_abc_and_binds_descriptor
```

`1293-1422` の `A.run_trial` は producer 内の report 公開前の完全性検査を通る。この2本があるため、新規の定数同期 test は不要。

## 変異 matrix 事前登録案

`T` の略記は前節と同じ。すべて未実測の事前期待。

| ID | 変異内容 | kill する test nodeid | 期待 |
|---|---|---|---|
| M1 | run-start の版検査ブロック全体を削除。report 版検査は残す | `T::test_run_start_unknown_schema_version_is_rejected`、`T::test_role_schema_v4_and_report_schema_v3_are_required` | KILLED |
| M2 | `_RUN_START_SCHEMA_VERSION` の値だけ v3 に変更 | `T::test_run_start_v4_without_binding_is_accepted`、`orchestrator/tests/test_p3_autonomous_workload_trial.py::test_transport_admission_error_persists_verified_partial_report` | KILLED |
| M3 | 版不一致時の `"legacy"` と `"unknown"` の割当てを交換 | `T::test_run_start_v3_legacy_shape_is_rejected`、`T::test_run_start_unknown_schema_version_is_rejected` | KILLED |
| M0 | 新規定数に付ける説明コメントの句点だけ変更 | 上記 matrix 選定 test 全体 | SURVIVED |

M1 は旧形だけに依存しない。旧形は版検査を削除しても後続の `generation_driver` 検査等で拒否されるため、単なる「例外が出た」の検査では版 gate の削除を見逃す。現行形＋v99／v3 の負例と全文診断を使う。

brief の **docstring 変異は無条件には等価でない**。`__doc__` が変わるため、観測可能な値が変わる。M0 はコメント変更へ置き換える。コメント変更なら Python AST と実行意味は同じであり、本件の受理・診断契約について等価である。ただし source bytes の digest まで同一という意味ではない。matrix は該当ソースの byte pin を検査するものと混同しない。

## 焦点走対象

現物では completeness 本体への名前参照が16ファイルあり、これを「16本の直接 importer」と同一視しない。直接 import を確認した test は本体 test を含め7本、すなわち **本体以外6本**。

最低限の焦点走対象は次の8本：

```text
orchestrator/tests/test_autonomous_trial_completeness.py
orchestrator/tests/test_layer3_admission_diagnosis.py
orchestrator/tests/test_p3_autonomous_workload_trial.py
orchestrator/tests/test_s8c_acceptance_receipt_v2.py
orchestrator/tests/test_role_session_isolation.py
orchestrator/tests/test_layer3_report.py
orchestrator/tests/test_trial_registry.py
orchestrator/tests/test_s8c_acceptance_receipt.py
```

親の16ファイル調査に含まれる間接参照も回収する対象：

```text
orchestrator/tests/test_s8c_preregistration_invariant.py
orchestrator/tests/test_s8c_arm_inputs.py
orchestrator/tests/test_s8c_preregistration_predicates.py
orchestrator/tests/test_reflux_formal_consumer.py
orchestrator/tests/test_official_perf_closure.py
```

合計13 test file。親は `tools/run_tests.py` 経由で焦点走・変異実測・全走を実施する。今回は read-only の静的検査のみで、pytest の成功は報告しない。

## 裁定パッケージ候補 (scope 外)

- **producer の run-start／role 定数分離**：共有による改版波及を扱う別課題。今回は独立した producer schema 名を導入しない。
- **report schema の consumer 所有化**：run-start と同じ依存は残るが、別契約。今回の関数内の流儀統一を理由に拡張しない。
- **v3 歴史 decoder**：実在する読み手と用途が確認された場合に限り、D1669 に従って検討する。
- **trial_registry／acceptance の追加版 gate、全版 registry、一般的な版番号解析**：具体的な欠陥が示されるまで追加しない。
- **過去 run 全体の現行コード再検証**：今回保証する範囲ではない。生成時のコード版・契約を使う原則を維持する。

## 総括

v5 への bump は提案しない。consumer に run-start の対応版 v4 を独立固定し、v3／未知版の拒否理由を構造化する最小変更が妥当である。

受理版は v4 のみで不変。producer・既存 artifact・互換層には手を加えず、既存統合正例と専用3 test、事前登録した変異 matrix で確認する。今回の成果は静的に検証した実装プランであり、実装・テスト実測は未実施。