## 結論 (採否と最重要 3 件)

**条件付き差戻しです。B の key ごと撤去は支持しますが、A/C 全撤去を「既存述語で代替済み」として実装へ渡すことには反対します。**

最重要の 3 件は以下です。

1. **real：公式 candidate 生成も floor 再計算を通りません。** 段 2 の未代替範囲は generic API だけではありません。
2. **real：撤去後も成功する、撤去対象の正例テストは少なくとも 4 件あります。** 加えて、段 2 が schedule 検査の発火証拠に挙げたテストは validator を呼びません。
3. **real：C の既存 2 負例は、今回の binary との一致検査を検証していません。** 両方とも、その前段の admission validator が拒否します。

以下、`M`＝`orchestrator/campaign/s8b_oracle_manifest.py`、`F`＝`orchestrator/campaign/floor_pair_driver.py`、`TM`＝`orchestrator/tests/test_s8b_oracle_manifest.py`、`TF`＝`orchestrator/tests/test_floor_pair_driver.py` とします。判定は静的読解によるもので、pytest は実行していません。

## must-fix

**1. real — 親 brief の「各撤去には代替が必要」と、A/C 全撤去の扱いを整合させる。**

brief:42–43 は代替の発火を撤去条件にしていますが、同:59 は C の代替を「無し」としています。A も、`M:625` が比較する floor の pair 集合を、`M:1078` の schedule 検査は読みません。

具体例は、完全な schedule と binding を維持し、ある holdout の `pairs` から 1 key だけ消した freeze です。A は拒否しますが、schedule 述語は拒否しません。freeze と manifest の hash を整合させれば hash 比較も代替になりません。

**放置時の変化：floor 内部不整合や別 binary の receipt が新たに受理されるのに、受理集合を維持した撤去として記録されます。**

新しい検査は不要です。撤去する検査と、残す検査、受理拡大を採用する理由を明確にしてください。

**2. real — 上流代替の説明に公式 candidate 生成入口を追加する。**

`M:1198 build_approved_manifest` は、`:1205–1206` の static loader・選択規則確認から、`:1245` の builder に進みます。`launch_validate`／`reverify_published_freeze` は呼びません。

しかも static loader の投影一致は、`s8b_holdout_freeze.py:1367–1370` で pair 値等をコピーしたものとの比較です。floor source と freeze の両方を同じ不整合値にすれば、この比較自体は成立します。`s8b_ratified_freeze.py:3587` の選択検査も、選択した結果の床値再計算ではありません。

**放置時の変化：A 撤去による candidate 生成側の検査減少が、generic API だけの問題として見落とされます。**

これは入口の射程についての所見です。現在の批准済み artifact が不正だとは確認していません。

**3. real — 成功するだけの正例を、残存検査の発火証拠に数えない。**

次節の 4 件は、A/C 全撤去後も対象検査なしで成功する構造です。また `TM:324` は schedule の生成結果を test 自身で数えており、`validate_schedule` を呼びません。

**放置時の変化：production の検証呼出しが消えても、完了証拠が成功のまま残ります。**

**4. real — C の撤去範囲と既存負例の意味を対応させる。**

`TF:1198` の両 parameter は以下で止まります。

- `record-binary-sha`：record だけ変更するため、`s8b_binary_admission.py:398–399` の record／subject 不一致。
- `receipt-trace`：outer hash を再計算しても、同 `:351–352` の trace 拒否。

したがって `F:1107–1115` の狭い撤去なら、**両負例の拒否期待は維持**されます。今回の binary との一致検査を外した証拠にはなりません。また、その範囲を文字どおり削除すると `:1111` の `subject` 定義も消え、残す `:1116` が未定義変数を参照します。

**放置時の変化：狭い撤去の実効性を確認できず、範囲指定どおりの削除では正常 receipt も例外になります。**

## real と判定した所見

**代替表の全行照合**

| 段 2 の入力 | 判定と具体的な到達条件 |
|---|---|
| freeze bytes 変更・manifest hash は旧値 | **real：条件付き代替。** 新 bytes の hash を渡せば `M:1053` が拒否。`TM:797` → helper `:297–303` は実際に現在 bytes を hash する。ただし改変は改行追加であり、floor 意味検査の証拠ではない。 |
| holdout を丸ごと欠落 | **real：拒否する。** 残存行を再採番し、schedule hash を更新しても `M:1072–1074` が拒否。 |
| 全 replicate から同じ構成を欠落 | **real：拒否する。** 各 replicate を同じ縮小集合にしても `M:1080` が freeze 由来の構成集合との差を拒否。 |
| 特定 replicate の cell 欠落・重複 | **real：拒否する。** 再採番して先行検査を通しても `M:367–370` が拒否。 |
| floor の pair key だけ欠落・余分・stock 混入 | **real：代替なし。** `M:1075–1078` は floor の pairs を読まない。 |
| holdout floor が scalar／field 欠落・余分 | **real：API 単体では代替なし。** A 後に残る `M:680–686` は外側の floor・holdout 集合まで。 |
| pair が 0・負値／scalar 不整合／null 相関違反 | **real：API 単体では代替なし。** 拒否本体は `M:632–670`。 |
| freeze document だけ変更・引数 hash は旧値 | **real：hash 比較は通る。** `M:1053` は引数同士の比較。A/B と同値ではない。 |
| B field だけ変更・ID は旧値 | **条件の訂正が必要。** key を残す案では、B 照合撤去後に `M:1161` が拒否。推奨の key 撤去案では `M:1043` が先に拒否し、ID 検査には到達しない。 |
| B field と ID を整合的に変更 | **real：案 (b) では通り得る。** 案 (a) では旧 key が残れば schema 拒否。 |
| 有効な別 binary の receipt | **real：C の対 artifact 一致は未代替。** record／subject／receipt hash を別 binary に整合させれば admission 内部検査は通り、現状では `F:1107` が拒否する。`F:1138` は今回の binary と spec の一致だけ。 |

「代替あり」の最初の 4 行に恒真な比較はありません。ただし、それらを **A の floor 検査の代替**と一般化する主張は成立しません。

**撤去後に対象検査を通らず成功する正例**

対象述語の正例として名指されているテストを列挙すると、次の 4 件です。

| テスト | 撤去後の状態 |
|---|---|
| `TM:935 test_snapshot_accepts_valid_per_pair_floor` | `_snapshot` は残るが、per-pair 値を検査しない。 |
| `TM:946 test_snapshot_accepts_explicit_null_pair` | null と scalar の相関を検査せず成功し得る。 |
| `TM:967 test_snapshot_accepts_all_null_holdout` | all-null 相関を検査せず成功し得る。 |
| `TF:1176 test_build_receipt_uses_real_binary_admission_validator_and_binds_sha` | fixture の import 修正後は、test 本体 `:1186` の直接 validator 呼出しと自己比較で成功し得る。 |

さらに、**代替発火証拠として不適切**なのが `TM:324 test_each_replicate_is_complete_product_and_each_cell_occurs_n_times` です。helper `TM:114` は builder を呼び、`:340–345` は test 自身の集計です。

一方、`test_p3_b4_floor_artifact_issuer.py:206` は撤去後も成功し得ますが、実際の finalizer・protocol 導出を検証しています。これを test 全体として恒真と呼ぶのは不正確です。ただし strict receipt 検証の証拠には転用できません。

**期待赤と二段の依存**

確認した主な連鎖は以下です。

- `TM:_snapshot` → `_validate_execution_snapshot` → A。
- `TM:_v2_document` → `s8b_v2_freeze_fixture.fill:63` → `per_pair_floor:31`。
- `TF:_prepare_spec:443`／`_document_only:475` → `_write_inputs:157` → `_portable_build_record:56`。
- issuer の `_synthetic_source:53`／正例 `:206` → driver test helper → 同 receipt fixture。
- report／oracle driver → reviewed-spec・v2 freeze fixture。
- `conftest.py:424–430,701–730` は oracle driver 等の保留・memo 分類であり、A/C の拒否述語を注入していません。

この範囲で、**A 全撤去の意味上の期待赤 8 関数、C helper 全撤去の 2 parameter に追加は見つかりませんでした**。

A は `TM:957,977,986,994,1003,1011,1020,1037`。C は `TF:1198` の 2 parameter です。import 未修正による広域 `AttributeError` は、この意味上の期待赤とは別です。

**上流を通らない入口**

| 入口 | 上流代替の到達範囲 |
|---|---|
| `M:1019 verify_manifest` | Mapping と hash を直接受け取り、ratified 再計算を要求しない公開 API。 |
| `M:818 _build_manifest` → `:740` | strict JSON 読込から直接構築する private 経路。探索した呼出しは test 側。 |
| `M:842 _build_manifest_from_ratified` | exact type は要求するが full 再検証は要求しない。 |
| `M:1198 build_approved_manifest` | 実在する公式 candidate 入口。static loader・選択検査まで。 |
| `F:load_frozen_spec` → `:1122` | oracle の批准・floor 再計算と別の production 入口。C の strict receipt 検査の代替はない。 |

投影一致単独では内部整合の代替になりません。`s8b_floor_stats.py:1080–1088` の再計算と、`s8b_ratified_freeze.py:3315–3324` の拒否まで通る経路では、実効性があります。

**pin と参照**

path・撤去識別子・現物 SHA-256 の 3 通りで探索しました。

- 現 M／verdict の全体 hash 記録は、段 2 の `trace-freeze.json:429–430`／`review-b.md:18` と一致。F／8c 文書の現 hash literal は追加 hit なし。
- 独立 golden は `TM:63–106`、`test_s8b_oracle_driver.py:149–258`。`M:65–75` の generator 集合に撤去対象 module はなく、今回の編集による更新根拠はありません。
- 段 2 が個別列挙していない過去の行番号参照として、`output/insights/2026-09-03_t2067-bcd-selection-closure/README.md:124` の `M:1019`、同 `verbatim/s1-brief.md:80–83` の builder 群を確認しました。**過去時点の記録として保持**すべきです。
- 段 2 の編集候補にない現行説明として `M:47–49` も残ります。A 全撤去後は「per-pair floor 検証時」という説明が古くなります。**nit**。
- `p3_b4_floor_artifact_issuer.py:760–762` の行番号参照訂正は必要です。

過去 insight の検索は 275 file に一致しましたが、**全行の参照先まで照合した完全な pin 閉包ではありません**。追加の強制 golden を発見した、とは報告しません。

## refuted と判定した所見

- **refuted：「公式 driver の公開 gate が上流を迂回する」**
  `s8b_oracle_driver.py:628–664` は v2 を full `launch_validate` に通します。judge は `s8b_oracle_judge.py:749–751`、verdict は `s8b_verdict.py:828–830` で再検証します。API 単体の受理拡大と区別が必要です。

- **refuted：「共有 fixture のため所有分割が必ず衝突する」**
  `s8b_v2_freeze_fixture.py:31–74`、`s8b_oracle_spec_fixture.py:38–99` の正例値は変更不要です。C 側の import 修正は `TF` 内で完結します。段 2 の分割は現範囲で素集合にできます。

- **refuted：「親の実アンカー表の位置が大きくずれている」**
  A=`M:609`、B=`:807`、B'=`:1093`、B''=`:58`、C=`F:1091`、E の `:96,:214,:443–449` は一致しました。D の `s8b_verdict.py:846` は説明コメントで、呼出しは `:847`。P1 の `reflux_formal_consumer.py:1480` も `P6Unavailable` の return と一致します。問題は位置より代替意味論です。

- **refuted：「C 撤去で admission consumer がゼロになる」**
  他 consumer は残ります。さらに issuer は `p3_b4_floor_artifact_issuer.py:775–805` で receipt の genome から protocol を導出します。ただし hash 照合だけでは receipt の意味検証を代替しません。

## scope 外の裁定候補

新しい gate・台帳・互換層の提案はありません。

API の provenance 強制や、新しい独立した発火検査が必要と判断する場合は別 scope です。本 wave では、既存検査の残置／撤去と、証拠・受理拡大の明記までに限定できます。

## 総括

段 2 の A/C 全撤去への留保は妥当です。補うべきなのは、**公式 candidate 入口の再計算欠落、成功し続ける正例 4 件、C 負例の実際の拒否箇所**です。

静的確認のみ実施しました。編集・commit・pytest 実行はしておらず、過去 artifact 全件の pin 閉包と、import 未修正時の全破損 node 列挙は未完了です。