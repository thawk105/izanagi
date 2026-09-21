## must-fix

なし。対象 2 commit に成果物の正しさを損なう変更は認めない。

## should

- **real：段 7 の更新予定に runbook §2 P3 の参照先更新を加える。** `docs/phase3-8b-restart-runbook.md:163` は「最新の一次資料」を T-2810 §5 に固定している。同資料の v1 exact 集合には削除前の候補 path が含まれるため、W-3 だけ更新すると現在値への導線が古いままになる。判定規則は維持し、T-2824 の実測節へ参照を更新する。

## nit

- **real：brief の成果物影響欄は説明不足。** historical の停止と held テストの赤だけでなく、「certified 選択・レポート値・台帳・批准参照・live の受理条件は不変」と追記すると、研究前進の範囲が明確になる。
- **refuted：comment の historical 成功が恒久保証として腐る懸念。** `test_s8b_oracle_driver.py:134` 以降は T-2824 の「削除後の実測で成功した」という過去の観測に限定しており、現状でも妥当。

## 反証した懸念

- **refuted：過剰変更。** base→統合 commit の変更は候補 1 file の削除と test 1 file の定数・comment のみ。gate・台帳・fixture・hold 台帳・production コードの変更はない。段 7 の記録も依頼範囲内。
- **refuted：fixture 補助が死んだ分岐になる。** floor_campaign の replay テストと oracle_driver の visible-output テストは候補 path を合成している。補助は現在も意味を持ち、削ると fixture の分離契約を壊す。無関係な sibling を残す検査もあり、維持が適切。
- **refuted：runbook §1.1 の判定規則も変更必須。** 拒否の件数・種別と全 gate 成立要求は変わらない。変わる exact 文字列は一次資料へ記録すればよい。§6 の更新契約に沿って該当状態と実測参照を更新する。
- **refuted：N1・P2 が evidence を超える。** JSON を機械比較し、g1・v1 とも候補 path の除去と hit 4→3 以外の差がないことを確認した。held 定数は削除後 g1 の refusals と集合 exact 一致。v1 は走査拒否 2 件の中身が変わり、拒否総数 4 は不変。
- **refuted：P1 の成功を昇格や許可へ拡張している。** 削除後 evidence は historical 成功と live `manifest-invalid / binary-admission` の継続を示す。comment・commit message は live admission の代替を否定し、certified 昇格や W-4/W-5 開始許可を主張していない。
- **refuted：削除理由や来歴保持が不適切。** 削除 message の根拠は候補 path の役割終了であり、D2077 を許可にしていない。同 bytes は保持の説明。X2 `4d8fb93b7` の候補 blob・削除前候補・現世代文書の SHA-256 一致も確認した。

## 段 7 記録への指摘

- **insight：** 5 経路の削除前後、実測 HEAD、evidence を記録する。historical 成功は `58ec3e928` の観測に限定する。P3 は g1 拒否 2 件・v1 拒否 4 件、両方 `allowed: false`、held checks 不変を明記する。提示 JSON 自体に rc はないため、rc=2 は親の実行ログを根拠に記載する。
- **runbook：** W-3 の hit を run_dir 3 file に更新し、候補削除手番だけを完了扱いにする。§2 の一次資料参照も更新する。policy 移行・spec 承認・W-5 の gate 条件は維持する。
- **phase3・worklog：** historical の障害除去と held 真値追随を完了事項として記録する。テスト・変異結果は親の実走結果を用い、M1 は diagnostic sensitivity の証拠に限定する。
- **帰結：** 候補削除で create-only の存在拒否要因が消えるが、生成全体の成功は保証しない。再生成されれば scan hit が復活しうること、bytes・来歴を X2 履歴 blob と世代文書で保持することを書く。
- **書いてはいけないこと：** historical 成功＝certified 昇格・live admission・W-4/W-5 許可、同 bytes＝削除許可、login の所要時間＝一般的性能改善。

成果物影響：放置時は historical が候補 hit で停止し、実施後は当該 checkout で成功するが、certified 選択・レポート値・台帳・批准参照・live の受理条件は不変であり、「主経路から遠い」と整合する。

## 総括

GO。2 commit の削除範囲・真値追随・記録の限定は妥当。段 7 では現在値と旧資料への参照を整合させること。
本レビューは静的検査と提示 evidence の照合まで。テスト実走は親の担当。