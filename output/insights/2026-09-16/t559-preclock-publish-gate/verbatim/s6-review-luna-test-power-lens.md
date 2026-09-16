## 判定と確認範囲

**must-fix は確認できませんでした。静的レビューの範囲では land 可です。** pytest・変異テストは実行していません。以下の「検出する」はコードからの判定であり、KILLED の実測報告ではありません。

参照の略記は `cli.py`＝`orchestrator/calibrator/cli.py`、`certify.py`＝`orchestrator/tests/test_calibrator_certify.py`。その他は射影に列挙された同名ファイルです。

## 既存テストの弱体化

**real / nit（違反なし）。** `applied.patch` の既存テスト部分の変更は、`certify.py:41` の `_EARLY_CLOCK_NOT_EVALUATED` への許可済み 1 項目追加だけです。既存 assertion・fixture・helper の変更はありません。

確認対象の helper は `certify.py:254`、`:287`、`:368`、`:380`。未評価一覧の完全一致 assertion は現在の行番号で `:842`、`:960`、`:1238`、`:1455` にあり、共通定数の追加が追随します。

既存 policy 変更テストも破壊される形ではありません。`certify.py:991` は既存 self reason の**包含**を要求するため、新 reason の追加と両立します。

## 新設テストの assertion 別検出力

**real / nit。** 必須の入力と主な故障検出は揃っています。ただし、個々の assertion が証明する範囲は以下に限られます。同じ性質の assertion はまとめています。

`test_cli_pre_post_clock_rejects_high_outlier`：

| 根拠：certify.py | assertion | 検出する欠陥 | 単独では検出しない欠陥 |
|---|---|---|---|
| :1673 | `rc != 0` | 誤った正常終了 | 無関係な例外による失敗 |
| :1674 | `calls == [0,1,2]` | post probe の省略・余分な取得 | benchmark との時間的順序 |
| :1676 | reason の完全一致 | gate 削除、自己照合への退化、reason 欠落・余分な reason | 同じ reason を別の判定で生成する実装 |
| :1677 | status が rejected | 判定結果の status への反映漏れ | 拒否原因の正当性 |
| :1678 | registered 不在 | 拒否後の公開領域作成 | 既存 registered がある場合の保全 |
| :1680 | candidate・公開 receipt 不在 | 拒否時の不要な publish 関連成果物 | 一度作成して削除する一過性の動作 |
| :1692 | 最後の比較入力が完全一致 | expected/observed 逆転、static pre・自己照合への取り違え | 戻り値の無視、比較呼出し全体の回数・順序 |
| :1693 | sidecar 全体の完全一致 | schema、profile、hash、入力、policy 等の欠落・誤記 | 同じ実関数を oracle に使う診断計算自体の誤り |
| :1705 | profile hash 再計算一致 | profile と記録 hash の不整合 | 誤った profile と hash の同時置換。前段の完全一致が補う |
| :1710 | sidecar 入力の canonical 再判定と `passed` が同一 | 記録された判定結果との不整合 | その戻り値が production の分岐を支配したこと |
| :1713 | 帯外件数が 1 | 件数の誤記 | 全ての複数帯外ケース |
| :1714 | 違反位置が指定 index | 先頭・中間・末尾の位置取り違え | 未選択の位置や複数違反の列挙 |

`test_cli_pre_post_clock_accepts_using_dynamic_pre`：

| 根拠：certify.py | assertion | 検出する欠陥 | 単独では検出しない欠陥 |
|---|---|---|---|
| :1733 | `rc == 0` | 恒真拒否、static pre 使用による過剰拒否 | gate の削除 |
| :1734 | probe 3 回 | 取得の省略・追加 | 各取得のタイミング |
| :1735 | benchmark 1 回 | benchmark の省略・重複 | 実 benchmark の挙動。ここは stub |
| :1737 | 公開 JSON が 1 件 | 公開漏れ・重複 | 公開内容の正しさ |
| :1738 | published と attempt の bytes 一致 | 両ファイル間の不一致 | **変更前との bytes 不変性**、両方への同じ誤変更 |
| :1740 | accepted | status の誤記 | gate が実行されたこと |
| :1741 | reasons が空 | 成功時の不要 reason | 判定の省略 |
| :1742 | profile 標本が dynamic pre と一致 | post/static pre の artifact 混入 | 標本以外の field の変化 |
| :1743 | sidecar 不在 | 成功時にも失敗用 sidecar を生成 | 成功時の比較実行そのもの |
| :1744、:1745 | 公開 receipt 2 種が存在 | receipt の作成漏れ | receipt 内容・再読検査の正しさ |

`test_cli_pre_post_clock_rejection_mechanisms`：

| 根拠：certify.py | assertion | 検出する欠陥 | 単独では検出しない欠陥 |
|---|---|---|---|
| :1755 | post 自己照合が通る | 負例の前提崩れ | production が pre→post を使うこと |
| :1773 | 非 0 終了 | 誤った正常終了 | 別 gate だけによる拒否 |
| :1774 | probe 3 回 | post 取得省略・追加 | 時間的順序 |
| :1780 | reason 列の完全一致 | 下側見逃し、post 自己照合、既存 reason 上書き・並べ替え、policy 不一致の見逃し | 同じ reason を作る別実装一般 |
| :1783 | rejected | status 反映漏れ | 比較方法 |
| :1784、:1786 | registered・candidate・receipt 不在 | 拒否後の公開処理 | 既存公開物の保全 |
| :1788 | expected 完全一致 | dynamic pre／凍結 tolerance の取り違え | 実際の呼出し入力との結合 |
| :1789 | observed 完全一致 | sidecar に pre を記録する誤り | 実際の呼出し入力との結合 |
| :1790 | canonical 再判定が False | sidecar の入力が拒否を再現しない | sidecar の `passed`・hash・全 profile。主要負例のみで検査 |
| :1792 | policy が 3.0 | 旧 policy 値の記録 | 別 process での再現 |
| :1793、:1794 | band=True、policy=False | policy 負例の前提崩れ、診断 field の誤り | この assertion だけでは production の判定依存 |
| :1796 | direction が below | 下側診断の取り違え | 違反件数・位置の完全性 |

主要な不足は `:1738` です。published と attempt の一致は、親裁定の「同じ既存入力に対する変更前後の published bytes 不変」を直接検査していません。ただし実装差分は `_assemble_v2`・serialization を変えず、post 情報も artifact に挿入していないため、**現実装の違反は確認できず nit** とします。

## monkeypatch と機構を通らない緑

**real / nit（迂回は確認できず）。**

- **監視 wrapper**：`certify.py:1664` は入力を deepcopy して記録し、`:1666` で `eg.effective_clock_comparison_passes` の実物へ委譲します。差し替えるのは CLI 側の import binding（`:1668`）であり、canonical 実装自体ではありません。`cli.py:47` の import と `execution_guard.py:324` の本体が対応しています。
- **policy 変更**：`certify.py:1765` は機構が読む policy 状態を変更する故障注入です。比較関数を成功・失敗 stub に替えてはいません。benchmark の注入先は既存 `calibrate_fn` seam（`certify.py:425`、`cli.py:992`）です。

`comparisons[-1]` だけなら、実物を呼びながら戻り値を捨てても緑になり得ます。しかし今回の policy 負例は、帯内でも新 reason を要求します（`certify.py:1780`）。したがって、戻り値を捨てて `diagnostics["band_pass"]` で判定する M05 は、この完全一致 assertion で検出される構造です。旧 self gate だけの拒否では、新 reason が欠けます。

これは登録された変異に対する検出力であり、任意の等価な再実装まで排除する証明ではありません。実装本体は `cli.py:1025` で canonical の戻り値を直接分岐に使っています。

## consumer への波及と凍結 pin

**real / nit（射影内で破壊的波及なし）。** 参照関係は次のとおりです。

| 変更対象 | 実際の参照経路 |
|---|---|
| `_EARLY_CLOCK_REJECTION_NOT_EVALUATED` | `cli.py:899` → `rejection_not_evaluated` → `:1161` の `_write_rejection` → `:791` の JSON field。テスト consumer は `certify.py:842、960、1238、1455` |
| `_certify_main` | `cli.py:1192` の `main(--certify)` から呼出し |
| CLI entry | `orchestrator/calibrate.py:12` で `main` を import、`:15` で実行 |
| certify テスト | `certify.py:417` の `_invoke` → `cli.main`。`:633` にも直接呼出し |
| policy テスト | `test_effective_clock_policy.py:20` は policy ソース・値、`:40` は `build_parser` を検査。変更した 2 symbol を参照しない |
| Pegasus workload テスト | `test_pegasus_calibration_workload.py:18` が import するのは `CertificationError` と `_canonical_genome_from_receipt`。新 gate を直接参照しない |

後二者について、今回の差分による期待値との矛盾は見当たりません。これは実走の合格報告ではありません。

登録済み Pegasus 較正 2 件は `env_contract.py:263` と `:276` の固定 path、`:266` と `:279` の固定 SHA-256 で束縛されています。

- `calibration-753f535a8d024727.json`
- `calibration-94a4b79fa31bba3c.json`

loader への引渡しも `env_contract.py:617` で固定 path/hash を指定し、attempt の最新ファイルを探索しません。CLI は `cli.py:1069` で artifact bytes から名前を作り、`:1097` の create-only publish を使います。衝突時に上書きしない処理は `:338` にあります。

したがって、この差分が既存 2 件の bytes・pin・現行選択を変更する経路は確認できません。変わるのは将来の CLI publish の受理集合です。**凍結 JSON 本体は射影外なので、現在の実 bytes と pin の実測一致までは未確認**です。

## sidecar・schema・attempt 全体の扱い

**real / nit（全リポジトリの consumer 不在は未確認）。**

`cli.py:833`、`:835`、`:1028` により、sidecar は指定どおり `attempts/<job>/effective-clock-pre-post-comparison.json` に書かれます。射影内の読取 consumer は新設テスト `certify.py:1682`、`:1787` だけです。

CLI の公開対象は `_assemble_v2` が返す `artifact` bytes（`cli.py:1048`、`:1086`）であり、attempt ディレクトリ全体ではありません。sidecar はその dict に入らず、`schema_v2.py:770` の validator も渡された JSON の exact keys を検査するだけです。**sidecar は calibration/v2 の検証対象外**です。

射影内の `copytree` は tools の fixture 複製（`test_pegasus_calibration_workload.py:431、1497`）や第三者ソース複製（`:1198`）で、較正 attempt 全体の公開・複製ではありません。

外側 wrapper や収集ツール本体は射影外です。そのため「attempt 全体を収集・参照する経路がリポジトリ全体にない」とまでは断言できません。

## 限定文の正確さ

**real / nit（CLI の保証範囲と整合）。**

凍結 dynamic pre は `cli.py:878`、benchmark 呼出しは `:992`、その返却後の post 取得は `:1007`、canonical 照合は `:1025`、publish は `:1097` です。提示された限定文に、CLI 実装と矛盾する保証はありません。

「benchmark **直後**」は「`calibrate_fn` の返却直後」という制御順序では正確です。最終測定からの経過時間上限や同時観測を保証する語としては読めません。post までに戻った変動を検出しない、probe を是正しない、という限定も適切です。

外側 `attestation-post.json` を新 gate が読まない点は確認できます。ただし、その wrapper が「CLI 終了後」に撮るという実装順序は射影外のため、親裁定に依拠します。

成功時に比較証拠が残らず、成果物だけでは成功判定を再計算できない点は **scope 外だが real な裁定パッケージ候補**です。根拠は失敗分岐だけの sidecar 出力（`cli.py:1025`）と成功時不在 assertion（`certify.py:1743`）。親が既に scope 外と裁定しているため、must-fix に戻しません。

## 総括

- **must-fix：なし。** 既存テストの許可外変更、canonical を迂回する stub、既存 pin への変更経路は確認できませんでした。
- **検出力が不足する assertion：** `certify.py:1738` は変更前後の bytes 不変を証明しません。`:1692` は単独では戻り値依存を証明せず、policy 負例の `:1780` が補います。receipt 存在 assertion は内容までは検査しません。
- **このまま land：yes（静的レビューとして）。** pytest・変異テストの緑、射影外 consumer の不在、凍結 bytes の hash 実測は主張しません。