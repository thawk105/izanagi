## must-fix

0件。今回の静的レビューで、結果値・主張上限を覆す欠陥は見つからなかった。

- v4→v5の保存diffは実ファイル間の差分と一致。変更関数は `validate_arms`、`configure_argv`、`run`、`selftest`、追加は `validate_defines` のみ。`classify`、manifest、verifier/discriminator呼出し、逐次保存の変更なし。
- define値の完全一致検査、固定7 keyへの限定、既存argv項だけの置換、arm自身のargvからのbinding生成、runnerのpath/SHA/bytes保存は段4裁定に適合する。
- witness軽量化案は、publish直後の採取、不一致値の保存、unlock後の同順出力を維持する。`unlockCLL()`がwrite_setを消さないこと、validation失敗時にwritePhaseへ入らないこと、INSERT/DELETE・decode失敗の終了経路を実ソースで確認した。
- READMEは陰性・非有意・個別の`certified=true`を認証や不在証明へ拡張していない。異常終了prefixと軽量化効果も未検証として区別している。

## should

1件。

**[ドリフト][手順漏れ] launcherの「30固定」は実装上の固定ではない。**

対象: [launch-block.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/codex/launch-block.sh:6)、同18行、`s4-ruling.md`「設計の確定」3。

根拠: 裁定は「launcherは`--rounds 30`を固定」とするが、実体は第三引数を`N`へ取り込み、`--rounds "$N"`へ渡す。保存済みB1〜B4はすべて30 round・90走であり、今回の分母への影響はない。

修正案: README §4へ「launcherはround数を引数で受ける実装だが、本走4 blockはいずれも30だった」と記録する。既存裁定・保存launcherの書換えや再計測は不要。

## nit

1件。

**[ドリフト] stampの行番号がmemcpyを指している。**

対象: [README.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2779-recovery-codex/output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md:63)。

根拠: 保存ソースではstamp呼出しは`M:1167`、`M:1169`はmemcpy。前後関係の説明自体は正しい。

修正案: `stamp (M:1169)`を`stamp (M:1167)`へ訂正する。

## 総括

**must-fix 0件／should 1件／nit 1件。GO（本観測記録のレビューAとして）。**

独立検算は一致した。

- 全360走のresult/run JSONとrun directory集合。
- 4 blockのarm別binding、runner・arms・patch・入力結果のSHA。
- 通常5/120、診断0/120、backoff 2/120とblock別件数。
- Fisher片側p値 `0.029950744134314918`、`0.2230864755405355`。
- 3 armのCP区間、repo内summaryとrecovery-summaryの内容。

未検査: 生traceの全面再解析、設計時の検出力数値の再計算、軽量witnessの実装・実測。pytest・selftest・再計測は実行せず、ファイル変更も行っていない。
