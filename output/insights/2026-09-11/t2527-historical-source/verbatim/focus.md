## 総括

**追加must-fixなし。実装修正は妥当ですが、consumer再走・変異の実測確認は残っています。**

未commitの5ファイルは`integrated.patch`と完全一致し、`git diff --check`も成功。旧artifactのSHAは既存rootと一致しています。本レビューではpytest・変異を実走していません。

| 対象 | 判定 | 根拠・残件 |
|---|---|---|
| R1 | **closed** | 既知旧文書の歴史閲覧では6種コードをresolver前に除外。不要なgenerator読取りも除去。親報告の109 passed / 10 skippedと公開verify成功が裏付け。M7は未実走 |
| consumer赤 | **partial** | 対象1テストの旧source拒否期待だけを裁定に整合。コード上の問題は解消しているが、修正後oracle走行結果は未確定 |
| 退行 | **検出なし** | 非コード入力束縛、現行意味照合、既存hold・他テスト期待を維持 |

**残所見：実在する追加修正事項なし。** 確認した主要箇所は以下です。

- `s1_known_axes_freeze.py:909`：R1の除外条件は既知旧文書・歴史閲覧・6種コードに限定。非コードの存在・SHA検査は残る。
- `s1_known_axes_freeze.py:953`：補正は比較用コピーのSHAだけ。path/key/件数等を含む全文比較を維持。
- `test_s8b_oracle_driver.py:4399`：pin拒否は実Git HEADと旧記録から構成し、不一致をfixtureへ追加していない。ROOT差替え除去はlive module再構成との整合。
- 同`:4443`：held時はfloor/budgetだけ、released時はpin・generator拒否を加えたexact集合。generator実bytes改竄、sentinel到達、verify呼出し回数・引数、`allowed=False`を維持。最小修正はいずれも不要。

**変異の実効性確認**

| 変異 | 静的に確認した検出点 |
|---|---|
| M1・M7 | 旧実物の正例がgenerator比較復活／コード存在検査復活を検出する構造 |
| M2 | 旧内容・識別子改竄の歴史識別負例。非コード入力検査の証拠には数えない |
| M3 | 未改変旧文書＋非コード入力コピーのSHA改竄。generator拒否との混同なし |
| M4・M5 | 実builder出力へのflags／source key単一差。期待側への同時伝播による恒真化なし |
| M6 | measurement・calibrationは現行意味照合を維持。calibrationはread-heavy外の差で後段maskを回避 |
| M6 oracle・M8 | 特定拒否理由の追加／消失を検出する**診断感度**。最終`allowed`反転のkillには数えない |

全変異のkill成立は親の実走待ちです。調査したmeasurement・calibration・oracleの呼出しに取り残しはありません。旧実物＋不存在resolverの成功を実コード削除実験へ、builder差分注入を旧artifact実物の変更へ一般化していません。
