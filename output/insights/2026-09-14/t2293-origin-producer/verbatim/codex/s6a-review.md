## 総括

**must-fix 1 件、nit 3 件。判定は要 fix。** 静的読解のみで、テストは実走していません。

新しい record 回収経路には、regular file 判定より先に FIFO の open で停止し、失敗レポートと試行台帳の終端記録へ進めない入力があります。従来拒否していた証拠を新たに formal 受理する経路は確認できませんでした。

## 裁定内容と実物の一致

1. `OriginMemberPlanInput.evidence_path` は削除済み。capability の origin、attempt 0 の batch、run の ordinal から導出しています（`p3_autonomous_workload_trial.py:439`, `:1398`）。
2. producer の `evidence_root` と `result_record_bytes` は削除済み。consumer への root は runtime root に固定されています（同 `:462`, `:1936`）。
3. member 順にファイルを回収し、全件終了後に評価しています（同 `:1899`, `:1919`）。
4. 指定された検査は実装されています。ただし非 regular file の確実な拒否には後述の穴があります。

回収例外は `AutonomousTrialError` に変換され、path 不一致も直接同例外になります。評価・formal commit へ進む握り潰しはありません（同 `:1910`, `:1915`, `:1947`）。

## 恒真化の所見

**nit N1：件数・順序・相異は、通常の producer 経路では恒真です。**

`RecoveryEnvelope.__post_init__` が member 検査を呼び、33 件、正確な行順、path 相異を保証します。producer の ordinal も `range(33)` 由来です（`reflux_origin_topology.py:286`, `:330`, `:364`, `:371`; `p3_autonomous_workload_trial.py:1296`）。後段の 3 検査を、通常入力の受理集合をさらに狭める独立ゲートとして数えてはいけません。

**record/member の path 比較は恒真ではありません。** `0.json` に有効な `1.json` の bytes を置く入力が反例です。schema 検査は member の期待 ordinal を参照せず、path 関数は読み取った record の ordinal を使います（`reflux_result_evidence.py:802`, `:959`）。テストの `wrong-query` がこの入力です（`test_p3_autonomous_workload_trial.py:11526`）。

なお、parse が既に validate を行い、path 関数も再度 validate するため、回収部の明示的 validate は重複です（`reflux_result_evidence.py:917`, `:962`）。

## 負例の単一理由性

静的に確認できる最初の拒否点は次のとおりです。

| ケース | 拒否点・証明の範囲 |
|---|---|
| `caller-path` | dataclass の未定義引数による `TypeError`。回収ゲートの負例ではありません（テスト `:11495`）。 |
| `caller-root` | 同様。root と bytes の入力欄削除を検査します（`:11505`）。 |
| `missing-record` | `_normalized_reference_target` 内の component `lstat` が先に拒否。読取り関数には届きません（`:11510`; evidence `:1414`）。 |
| `query-order` | 通常構築なら topology が先に拒否。`object.__setattr__` 後に限り回収順序検査へ到達します（`:11512`）。 |
| `duplicate-path` | 同様に通常構築が先に拒否。強制変異後は相異検査で停止します（`:11515`）。 |
| `missing-member` | 同様。強制変異後の最初の拒否は件数検査です。ただし ordinal 列も同時に不正になり、厳密な単一述語違反ではありません（`:11520`）。 |
| `wrong-query` | 有効 record のコピーなので schema 検査を通り、path 不一致で停止します。後段には重複 ordinal 等の拒否理由も残ります（`:11526`）。 |
| `symlink-record` | normalized-target の component 検査が先に拒否。`O_NOFOLLOW` は未到達です（`:11530`; evidence `:1434`）。 |
| `symlink-parent` | 同じ component 検査が先に拒否します（`:11535`）。 |

**nit N2：このテスト群は `O_NOFOLLOW` と regular-file 判定の独立した負例を持ちません。** 共通の例外メッセージだけでは、その二つの検査が働いた証拠になりません。

token テストの 14 ケースは helper の直接呼出しです。空文字・NUL・surrogate は `_text`、`.`・`..`・区切り文字は `_safe_path_token` が拒否します（`reflux_result_evidence.py:319`, `:952`; テスト `:11586`）。上位の capability 発行や envelope 構築を通した攻撃到達性の証明ではありません。

## private symbol の跨ぎ使用

**must-fix M1：FIFO で regular-file 検査前に停止します。**

新しい呼出し箇所は `p3_autonomous_workload_trial.py:1903`。呼ばれる helper は `O_RDONLY | O_NOFOLLOW` で open した**後**に `fstat` します（`reflux_result_evidence.py:1442`, `:1444`, `:1448`）。

導出された `0.json` を writer のいない FIFO に置き換えると、component 検査は通りますが、open が待ち続けます。path 申告や envelope 改変は不要です。共有 helper に既存の性質ですが、本差分で record 本体にも到達可能になります。

**成果物への影響：** 回収が戻らず、材料レポート生成と試行台帳の終端記録へ進めません（`p3_autonomous_workload_trial.py:3843`, `:5256`, `:5280`）。非ブロッキング open と fd の regular-file 判定を組み合わせ、FIFO を拒否する負例が必要です。

その他の契約は次の範囲です。

- `_safe_path_token` の戻り値・例外変換は呼出しと一致します。
- `_normalized_reference_target` は絶対 path と正規化後の root 外脱出を拒否します。内部の `a/../b` は正規化して許しますが、producer の token からこの形は生成できません（evidence `:1421`）。
- **nit N3：親 directory の競合差替えまで防ぐ契約ではありません。** component の `lstat` と通常の絶対 path open は別操作で、`O_NOFOLLOW` は最終成分だけに作用します（evidence `:1434`, `:1444`）。競合する directory writer を仮定すれば、確認後に親を外部への symlink に変える余地があります。これは唯一 writer 性の運用前提を外した場合の限界であり、本差分による新しい認証保証として扱えません。

commit の名乗りは入力欄削除と runtime root への固定までです。writer 認証や一意な deployment root の保証へ拡張して読むことはできません（`reflux_formal_consumer.py:1386`）。

## 既存テストの弱体化

提示差分には期待値反転・緩和・skip・削除・xfail 化はありません。

材料の保存先変更後も、保存した bytes と同じ `materialized` を台帳封印へ渡しています（`test_p3_autonomous_workload_trial.py:10692`, `:11006`）。既存の `P6Unavailable`、receipt、origin 終端、lifecycle projection の確認も残っています（同 `:11169`）。

ただし fixture が証拠を作成・封印する構造は残っており、本番 executor や唯一 writer 性の証明にはなりません。

## blocker / must-fix / nit の一覧

| 分類 | 所見・根拠 | 放置時の成果物への影響 |
|---|---|---|
| must-fix M1 | FIFO の blocking open（evidence `:1444`; trial `:1903`） | 材料レポートと試行台帳の終端記録が未生成のまま停止し得ます。 |
| nit N1 | 正常構築下で恒真の 3 検査（topology `:330`; trial `:1886`） | 実際の受理集合は変わりません。独立ゲート数の過大評価になります。 |
| nit N2 | symlink 負例が読取り前に拒否（テスト `:11530`; evidence `:1434`） | 現在値への直接影響は未確認。読取り層の退行を見逃す検査不足です。 |
| nit N3 | 親 directory 差替え競合への限界（evidence `:1434`, `:1444`） | 競合 writer を認める場合、root 外の record を回収し得ます。formal 受理成立までは未確認です。 |

blocker はありません。

## 判定 (採用可 / 要 fix / 差し戻し)

**要 fix。** M1 の非 regular file に対する停止経路を閉じ、親側で FIFO の拒否と既存テストを実走確認してください。