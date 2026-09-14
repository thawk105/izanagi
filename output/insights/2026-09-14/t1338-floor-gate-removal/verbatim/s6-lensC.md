## 結論 (採否と最重要 3 件)

**採用可。must-fix はゼロ。** 統合差分の全7ファイル・28 hunk を照合し、現物が差分の変更後 blob と一致することも確認した。

1. 撤去は裁定の A/B/C と、指定されたテスト退役・説明修正の範囲内。
2. admission receipt・store 実体検査を含む、残すと決めた述語は残存。
3. `pipeline.py` は基準 main と byte 一致。8c の保護契約も不変。

以下、ファイル名は `orchestrator/campaign/` 配下を指す。

## must-fix

ゼロ。

## real と判定した所見

- **real：A/C の撤去で受理集合は広がる。** `s8b_oracle_manifest.py:600` の検査は floor 外形・holdout 集合・budget を検査するが、per-pair 値の内部整合には入らない。`s8b_oracle_driver.py:1748` の引数構築から過去 binary hash の供給が消え、`pipeline.py:2091` の optional 照合は通常の oracle 呼出しでは発火しなくなる。いずれも裁定どおり。
- **real：B は文書形も変更する。** `s8b_oracle_manifest.py:55` の key 集合から旧 key が消え、`:965` の exact 比較により旧 key 付き文書は拒否される。`orchestrator/tests/test_s8b_oracle_manifest.py:797` に、その拒否を固定する負例がある。互換性維持とは報告できないが、欠陥ではない。

## refuted と判定した所見

- **refuted：射程外の撤去。** 全28 hunk を確認。A/B/C 以外の実行述語の削除はない。テスト変更も指定の退役、削除 field に追随する fixture 修正、旧 key 拒否の追加に収まる。共有 floor fixture は説明のみ変更され、生成処理は不変。

- **refuted：manifest の残存述語が消失。**

  | 残す対象 | 現物の位置 |
  |---|---|
  | floor/budget の null 拒否 | `s8b_oracle_manifest.py:603`、`:605` |
  | floor 外形・holdout 集合 | 同 `:607`、`:612` |
  | budget 値・holdout 集合・`oracle_shared` | 同 `:616`、`:619`、`:622`、`:627` |
  | freeze byte sha256 比較 | 同 `:975` |
  | schedule holdout 集合・cell product | 同 `:994`、`:997`、`:1002` |
  | top-level key exact 比較 | 同 `:965` |
  | `_holdout_configuration_ids` と使用箇所 | 同 `:568`、`:1000` |
  | `_GENERATOR_SOURCES`・validator・呼出し | 同 `:65`、`:458`、`:734`、`:1021` |

  freeze hash 検査は caller 提供 hash との比較であり、ここで freeze を再 hash するものではない。generator の指定5ファイルも基準 main と byte 一致した。

- **refuted：admission/store 検査の消失。** `s8b_oracle_driver.py:1018` に `admission-missing`、`:1024` と `:1030` に exact keys・policy・pin・binding 等の検証、`:1041` に `admission-mismatch` への例外変換が残る。`:910` は store の実 bytes を SHA-256 化し、`:1049` で `store-missing`、`:1054` で receipt の `binary_sha256` と比較して `store-hash-mismatch` を拒否する。

- **refuted：撤去の取り残し・helper の巻き込み。** B の key・生成・照合は一体で削除済み（`s8b_oracle_manifest.py:55`、`:719`、`:1015`）。production 内に A/B/C の削除対象識別子の取り残しはない。基準 main の全 Python 参照検索では、削除 helper `_finite_positive_or_none` の利用は A 内の3箇所だけだった。共用 helper は `:568` に残る。

- **refuted：`pipeline.py` の変更。** 基準 `f5423e2fff3adb164731963ca33e82ed08d08c4d` と現ファイルの bytes が完全一致。optional 引数と照合は `pipeline.py:1565`、`:2091` に残る。`floor_pair_driver.py` も byte 一致。

- **refuted：verdict の呼出し消失。** `s8b_verdict.py:847` に `_validate_execution_snapshot` 呼出しが残る。変更は `:846` のコメントだけで、変更前後の AST も一致。

- **refuted：8c 前文が保護契約を変更。** 追記は `docs/phase3-8c-preregistration.md:18` からの前文。`s8c_preregistration.py:710` の境界抽出は §1〜§7 を起点とし、`:1026` で §5/§6 を抽出、`:1032` で規範本文を構築する。前文は保護 hash に入らない。ただし文書全体の構文検査は受ける（`:1022`）。

  実 parser に基準版と現物をメモリ上で渡した結果、契約 object は完全一致。evidence contract も byte 一致し、前後の protected hash はともに
  `1e325f9d9ce483b14d02e2c857f785007afa45005112127312b409d77cfee684`。

- **refuted：絶対規律2の判定を撤去。** A/B は floor/budget の内部整合、C は過去 binary との同一性要求。今回測定の correctness 経路は `s8b_oracle_driver.py:1750`、`pipeline.py:2115` に残り、anomaly 結果の処理も `:2127` に残る。judge の correctness-red 失格は `s8b_oracle_judge.py:281`、legacy/S2 双方の PASS 要求は `:295`。判定コードの変更はない。

## scope 外の裁定候補

新規候補なし。新しい gate・検査・互換層の提案なし。

## 総括

指定レンズでは裁定違反の所見はゼロ。受理拡大と旧 key 付き文書の拒否を明示して採用できる。静的照合とメモリ上の parser 比較のみ実施し、pytest・編集・commit は行っていない。