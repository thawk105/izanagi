## 変更前の受理・拒否挙動

非空の v3 は `v3_existence_unverified` によって一律に非認定でした。v2 は W の I/U/D による存在履歴を検査せず、今回もその挙動を維持しています。

今回の認定集合変更は、裁定 R1〜R8 による v3 の存在検査と旧印撤去に限定しました。cycle の verdict 優先順位は変更していません。

## 変更内容 (file ごと、追加削除行数)

| file | 追加／削除 | 内容 |
|---|---:|---|
| `orchestrator/verifier/model.py` | +14／−2 | frozen `ExistenceViolation`、件数・詳細、`clean()` 条件、旧印撤去 |
| `orchestrator/verifier/dsg.py` | +90／−3 | 両入口から呼ぶ共通存在検査、winner adapter、決定的な詳細・notes |
| `orchestrator/verifier/core.py` | +9／−9 | 旧印設定・不要参照撤去、v3 JSON の件数・詳細 |
| `orchestrator/tests/test_verifier.py` | +186／−12 | 新規6関数、既存1関数改名、経路・fallback・限定期待の更新 |

production は追加削除127行、試験は198行で上限内です。変更ファイルは上記4本のみ。parse・report・docs・共有 fixture は未編集、commit は作成していません。

存在検査は辺構築後に親で一度だけ実行します。compact は winner のみを読み、表は key token から取得します。重複版・genesis commit があれば省略し、orphan を新件数へ重ねません。

## 試験 (関数名と中身、実走結果)

新規関数は次の6本です。

| 関数 | 検査内容 |
|---|---|
| `test_v3_existence_negative_pairs` | 読み2種・書き3種の独立負例、一行修正の正例、全経路一致 |
| `test_v3_existence_valid_histories_and_self_reads` | 正常履歴、削除前の指定版読み、合成形式の自己版読み |
| `test_v3_existence_version_order_and_table_isolation` | epoch/tid 辞書順、txid/file 順との逆転、表分離 |
| `test_v3_existence_write_duplicates` | 異種 op 群、同種重複、曖昧 object の派生診断抑制 |
| `test_v3_existence_integrity_overlap_and_winners` | 省略条件、orphan、last-wins、先頭 neutral file |
| `test_v3_existence_output_samples_and_cycle` | 全詳細、6件中5件の見本、旧 JSON、cycle 優先、`max_report=0` |

独立負例は共通 helper で cycle 無し、orphan/framing 0、X/P gate 充足、witness 一致、`replace(ig, existence_violations=0).clean()` を要求します。存在検査は stub していません。

既存の overflow・実 worker 終了 fallback にも存在違反を追加し、従来のグラフ期待を維持しました。v2 の期待値は変更していません。

**実走結果：**

- `python3 -m pytest orchestrator/tests/test_verifier.py -q -p no:cacheprovider`
  - **137 passed、1 failed、16.24秒**
  - 失敗 nodeid：`orchestrator/tests/test_verifier.py::test_v3_existence_write_duplicates`
  - 追加 fixture に意図しない cycle があったため、読み手を別取引へ分離しました。assertion は緩和していません。
- **修正後は未実走**です。標準 runner による再実走は `qstat -Q preflight rc=1`、子未起動、rc=16 でした。
- `git diff --check` と変更4ファイルの AST 構文検査は成功しました。

meta-test を検索し、新設・改名関数の名前や件数を固定するものは見つかりませんでした。既存 verifier 関数を参照する `test_skip_classification.py` も実走対象にしましたが、同じ dispatch 障害で未実走です。

## 波及の静的列挙

| 所有外の箇所 | 波及 |
|---|---|
| `report.py:113,165` | `clean()` と notes を通じて反映。旧 JSON の key は不変 |
| `campaign/reflux_result_evidence.py:724` | 既存 `clean()` 必須条件に新件数が反映 |
| `test_campaign.py:5805,5822` | `Integrity(...)` の keyword 構築。新欄は既定値 |
| `test_t1286_commit_receipt.py:356` | 同上 |
| `test_reflux_result_evidence.py:879` | `.clean()` consumer |
| `test_reflux_campaign_issuer.py:589,693` | `.clean()` consumer |
| `test_reflux_formal_consumer.py:833,1610` | `.clean()` consumer |
| `commit_receipt_support.py:112` | capability 発行経由で新判定を受ける |
| 共有 trace fixture・synthetic proof source | 内容・hash を変更せず利用 |

これら所有外の consumer test は今回実走していません。

## 変異の照準表

以下は**親が実行するための照準と期待**であり、KILLED／SURVIVED の実測報告ではありません。表中の短名は上記試験名の `test_v3_existence_` 以下です。

| ID | production の位置 | 殺す試験／期待 |
|---|---|---|
| M0 | `DSG._check_existence`, dsg.py:400 | 等価な `(epoch, tid)` key 指定。SURVIVED 期待 |
| M1 | 同 :401 | `negative_pairs` の unborn。件数・種別で検出 |
| M2 | 同 :423 | `negative_pairs` の deleted read |
| M3a | 同 :408 | `negative_pairs` の insert-on-live |
| M3b | 同 :410 | `negative_pairs` の update-on-absent |
| M3c | 同 :412 | `negative_pairs` の delete-on-absent |
| M4 | 同 :416 | `negative_pairs` の D→U/D |
| M5 | `Integrity.clean`, model.py:518 | `negative_pairs` の非認定・verdict |
| M6 | `DSG.__init__`, dsg.py:334 | `negative_pairs` の object 経路 |
| M7 | `DSG.from_compact`, dsg.py:349 | `negative_pairs` の packed/tuple 経路 |
| M8 | 両入口の v3 guard、dsg.py:333,348 | `violations_and_v2_control` と既存 v2 試験 |
| M9 | `_check_existence`, dsg.py:400 | `version_order_and_table_isolation` |
| M10 | 同 :400、owner は :386 | 同上、txid 順への置換 |
| M11 | 同 :423 | `valid_histories_and_self_reads` の I→D 後 R(I版) 正例 |
| M12a/b | 同 :386–399、混在集合を I/D に単一化 | `write_duplicates` の W のみの独立負例 |
| M13 | `result_to_dict_v3`, core.py:198–203 | `output_samples_and_cycle` の詳細辞書一致 |
| M14 | `_existence_rows`, dsg.py:357,372 | `version_order_and_table_isolation` |

独立負例には、別の integrity・cycle による拒否理由を置いていません。M1 は変異後に `insert-on-live` が生じ得るため、非認定だけではなく**期待する件数・種別の不一致**で検出します。M9/M10/M11/M14 は合法正例の誤拒否も検出します。M13 は出力契約の検査です。

## 裁定からの逸脱と理由

実装仕様・変更量の逸脱はありません。ただし、修正後の全走と meta-test 実走は完了していません。実 trace の公開 API probe と変異実走は、指定どおり親側の未完了作業です。

初期存在は段1の契約に基づきます。初期ロード集合の独立検証、mocc の native 挙動、段2の scan・再挿入まで検証したとは扱いません。

直接 pytest の再試行は PreToolUse hook に拒否されました。標準 runner へ切り替えましたが、計算ノード dispatch の事前確認が失敗したため、実行制限を迂回せず停止しています。

## 総括

- v3 の共通存在検査と旧印撤去を実装しました。
- v2 の期待値、辺構築、worker、parse、report は維持しました。
- production 127行、試験198行、新規試験6関数で上限内です。
- 初回全走は137 passed／1 failedでした。
- 失敗 fixture は修正済みですが、修正後は未実走です。
- AST 構文検査と差分の空白検査は成功しました。
- 変異照準を提示しました。変異実測・実 trace probe は親側に残ります。
- commit は作成しておらず、完了条件 R8 達成・全緑とは報告しません。