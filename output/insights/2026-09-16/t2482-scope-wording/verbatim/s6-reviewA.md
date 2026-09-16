## 逐語照合

**A1〜A4 は plan v2 と完全一致しています。** 隣接文字列を `ast.literal_eval` で連結し、裁定本文の逐語と比較しました。空白・句読点を含め差異はありません。

| アンカー | 根拠 file:line | 結果 |
|---|---|---|
| A1 | `orchestrator/campaign/artifact_admission.py:76` | identity_scope 全174文字一致 |
| A2 | 同上 `:81` | excluded_scope 全273文字一致 |
| A3 | `orchestrator/tests/test_artifact_admission.py:1371`、`:1376` | 両方とも独立 literal で一致 |
| A4 | `orchestrator/tests/test_s1_9pair_figure_provenance.py:78`、`:83` | 両方とも独立 literal で一致。E0・state・reason_code 不変 |

提示された差分は実 commit `29f463719` と一致し、対象3ファイルの作業ツリーも同 commit と一致しています。変更は指定の3ファイル・4アンカーだけです。

実測JSONは base `a1b40608c` の収載63・発見162・未収載99を記録し、各配列の長さ・重複なしの件数も一致しています。

## 所見

**所見ゼロ。** 必読射影すべて、production の指定範囲、test の指定範囲と歴史 scope の検査を読み、次を確認しました。

- `artifact_admission.py:187` の現行 scope 完全一致検査、`:228` の歴史 scope 固定、`:1048` 以降の E1 導出は変更されていません。E0 certified 拒否を要求する `test_artifact_admission.py:1366` の検査も維持されています。
- `PRE_T733_*`、`FROZEN_E0_EPOCH`、`FROZEN_ADMISSION_VALIDATOR_SHA256`、docstring、収載 tuple、受理述語に変更はありません。比較の緩和や独立 literal の定数参照化もありません。
- `artifact_admission.py:76`〜`:87` は D1651 の5要素を保持しています。docstring は保証内容を再掲せず、2定数を正本として参照しています。
- 「収載 path の source bytes を除く」は例外をソースbytesに限定しています。worker の ssh・interpreter・binary を含む実行全体の保証へ広げていません。「同発見集合に入らない module」も除外対象として列挙されており、集合外への保証にはなっていません。
- 歴史値と現行値の照合は引き続き分離されています。`test_s1_9pair_figure_provenance.py:383` は現行値を、`:740` は凍結済み歴史値を使用します。記録済み成果物の書換えも差分にありません。

## 総括

commit は段4裁定どおりで、規律2の判定緩和・規律7の歴史改変に当たる変更は見つかりません。

ただし、**受理述語の不変は、bytesを束縛する全経路の再検証結果不変を意味しません。** 段4で裁定済みのとおり、新規lockのE1、validator receipt hash、B-4 projection hashにはファイル変更の影響があり得ます。同じ記録済みmapからのE1再導出値は不変です。この既知の区別を、新規の修正所見として再提起していません。

静的点検のみ実施しました。書込み・pytest実行はしていません。