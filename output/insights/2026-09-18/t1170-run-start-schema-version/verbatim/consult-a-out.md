## must-fix 所見

なし。提示された具体案に、現時点の受理集合を広げる経路・縮める経路は見つからなかった。

現行 producer の `SCHEMA_VERSION` は v4 なので、比較先を独立リテラル v4 に置き換えても版判定は同じ。`legacy`／`unknown` は不一致分岐の内側で診断を選び、両方とも `_fail` するため、新しい受理経路を作らない。

以下、パスの略記は指定 worktree 内の次のファイルを指す。

- `C`: `orchestrator/campaign/autonomous_trial_completeness.py`
- `T`: `orchestrator/tests/test_autonomous_trial_completeness.py`
- `P`: `orchestrator/campaign/p3_autonomous_workload_trial.py`
- `PT`: `orchestrator/tests/test_p3_autonomous_workload_trial.py`

他の入力を有効に保った具体例は次のとおり。

| run-start の入力 | 変更前／変更後 |
|---|---|
| v4、現行形、binding なし | 両方受理 |
| v4、`generation_driver` 欠落 | 両方 `C:2309–2310` で拒否 |
| v4、`gating_spec_sha256` 欠落 | 両方 `C:2316–2317` で拒否 |
| v4、`honest_accounting_authority` 欠落 | 両方 `C:2327–2328` で拒否 |
| v4、`do_build=0` | 両方 `C:2257–2258` で拒否 |
| v4、未参照の追加 field `extra=1` | この関数では両方とも追加 field を理由に拒否しない |
| v3、現行形／旧形 | 両方版で拒否。変更後は旧世代と診断 |
| v99、現行形 | 両方版で拒否。変更後は未知版と診断 |
| 版欠落／`null`／数値／配列／object | 両方版で拒否 |

したがって「受理版は v4 のみ」は正しいが、「v4 なら形を問わず受理」「v4 の exact-key 契約を新設する」という意味ではない。

## nit 所見

1. **改版からの独立性そのものを、現行 matrix は検出しない。**
   新定数を残し、比較式だけ `_producer_module().SCHEMA_VERSION` に戻す変異は、producer が v4 のままなら予定テストを通り得る。今回直す依存関係を戻す変異なので、追加するなら本題内である。producer の版だけをテスト内で変え、記録済み v4 の判定が変わらないことを確認する案がある。production の同期 gate は不要。現行案に受理集合の誤りがあるわけではないため nit とする。

2. **「構造化」は例外メッセージ内の構造化である。**
   `C:447–448` は文字列を持つ例外を送出する。plan は `recorded`・`generation`・`consumer_supported` を明示するが、機械可読な例外属性や report field は追加しない。brief の「構造化文言」には適合する。「構造化データを追加した」と成果報告しないこと。実装全体は比較先の所有者も変えるため、単なる文言変更ではない。

3. **世代別診断は版 gate に到達した場合の保証に限定する。**
   journal hash、event 順序、transport、report 版などの検査が先行する（`C:3085–3093`、`2238–2239`）。壊れた v3 artifact が必ず旧世代メッセージになるわけではない。plan の負例は他の部分を有効にし、`_persist` するため、この点を満たす。

## brief の誤り・飛躍

- **F2：7 key 追加は確認できるが、key 集合一致から「形不変」全般は導けない。**
  `a506633ef` と `4c6f03048` の producer を比較し、無条件3 key・binding 条件付き4 keyの追加を確認した。現在は journal の `seq`・`ts` 込みで非 binding 16 key、binding 23 key。「新形20 key」は現行出力の説明として不正確。今回の比較では `4c6f03048` と HEAD の producer ファイル全体に差分がなかったが、参照先の生成関数まで含む契約不変や、途中の全履歴は証明しない。plan の限定は妥当。

- **F3：「直接、版を照合する箇所」と限定すべき。**
  `C:2240–2241` が直接照合する。`trial_registry.py:5967–5993` と `s8c_acceptance_receipt.py:1496–1506` はそれぞれ binding／arm 内容を見る。確認範囲で第二の直接照合箇所は見つからなかったが、completeness を呼ぶ間接 consumer が存在しないという意味ではない。

- **F5：「読み手0件」は探索結果以上の断定。**
  指定 artifact の2行目に v3・13 key を確認した。`output/` の JSON／JSONL 検索で、ほかに見つかった v3 参照は変異仕様・台帳だった。`orchestrator/`・`tools/` の Python には指定 artifact 名への直接参照がなかった。ただし任意パスを受け取る reader、動的参照、repo 外の用途の不在は証明していない。「確認できた読み手なし」と書くのが適切。plan はこの飛躍を訂正している。

- **P1／P5 の因果説明は plan の訂正を採用すべき。**
  D1851 は「形を変えない bump の禁止」までは述べない。また直接の問題は consumer が producer の可変定数を受理条件に使うことであり、producer 内の共有定数だけを根本原因とするのは強すぎる。

- **P7 の統合テストの実体は確認できた。**
  `PT::test_transport_admission_error_persists_verified_partial_report` は `A.run_trial` を実行し（3058行付近）、生成した journal/report を `completeness.verify_autonomous_trial_files` に渡す（3096行付近）。差し替えるのは transport admission 等であり、版 gate ではない。role を実行しない経路なので、run-start の同期確認として有効。通常完走側の `PT::test_fixture_trial_runs_ycsb_abc_and_binds_descriptor` も、producer 内の completeness 呼出し（`P:3958` 付近）を通る。

## 変異 matrix への所見

**記載された kill node は代表例であり、完全集合ではない。** 選定 node だけを走らせる計画なら、その旨を明記すればよい。全焦点走の expected killed 集合として使うなら不足する。

| 変異 | 静的な帰属・追加の kill 期待 |
|---|---|
| M1：版検査削除 | 現行形＋v99／v3 は、他の field を有効に保つため版拒否が消える。適切な主検出例。版欠落の既存 node も kill 期待。旧形 v3 は後続の `generation_driver` 検査でなお拒否されるが、全文診断が違うため新規旧形 node も kill 期待 |
| M2：対応版を v3 に変更 | v4 正例と transport 統合正例が版 gate で拒否される。さらに旧形 v3 は後続 gate へ進み、未知版・欠落版は診断中の対応版が v3 になるため、これらの全文期待も kill する。既存の現行形 v3 負例も拒否が消える |
| M3：legacy／unknown 交換 | 受理集合は変わらず、診断契約で kill。新規2負例に加え、既存の現行形 v3 負例と版欠落負例も kill 期待 |
| M0：コメントの句点変更 | 受理・診断契約について等価。source bytes は変わるが Python AST は変わらない。plan のコメント変異への変更は妥当 |

旧形 v3 の M1 検出は「不正入力を受理させた」検出ではなく、**拒否理由が別 gate に移ったことの検出**である。台帳ではこの違いを残すこと。M2 でも複数の診断期待が同時に壊れるため、「唯一の node／理由で kill」とは記載しない。

## 裁定パッケージ候補 (scope 外)

- report 版や provider／budget まで含む、過去 run 全体の現行 producer からの独立。
- producer の run-start／role schema 定数の分離。
- 実在する用途・読み手が確認された場合の v3 歴史 decoder。

今回の受理形拡大、追加 exact-key gate、他 consumer への版 gate は提案しない。

## 総括

レンズ A として plan は採用可能。現行 v4 に対する受理集合は不変で、旧世代／未知版の診断分岐にも受理への抜け道はない。統合正例は producer の実生成出力を検査している。

親には、F2／F5 の断定範囲を限定し、変異 matrix を代表 node と完全集合で混同せず記録することを勧める。静的検査のみ実施し、ファイル変更・pytest 実測は行っていない。