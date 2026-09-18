## 総括

監査対象は `61be923f4d743f94cea4060c3772d098325b2bec`。**実装のmust-fixは0件。既存成果の回収は妥当ですが、現行HEADの記録には訂正が必要です。** 以下は親が訂正予定とした既知事項の確認です。静的検査のみ実施し、変更・commit・pytestは行っていません。

**must-fix（記録、いずれもreal）**

| 箇所（file:line） | 成果物への具体的影響 | 最小対応 |
|---|---|---|
| `docs/spool/worklog/2026-09-18-dev-wave-t2691-rescue-checker-timeout-grace-1.md:14,18,27` | 「閉じた」「実走: 受入全走」「remaining: none」が未実施の受入まで完了扱いにする。旧レビュー・変異成功だけでは現行tipの完了を立証しない。 | 旧成果の実施済み範囲と回収側の未完受入を分け、実結果に基づいて完了を記録する。 |
| `docs/spool/decisions/2026-09-18-dev-wave-t2691-rescue-checker-timeout-grace-2.md:18,24` | 「常に」は観測2走を一般化。「受理集合は緩まない」は、時間内に回収できる報告が増える説明と混同を招く。 | 「観測2走では回収できなかった」「JSON検証述語は不変」に限定する。worklog:15も同様。 |
| `output/insights/2026-09-18/t2691-rescue-checker-timeout-grace/README.md:51–59` | 所要欄の外側wallをテスト実行所要と読むと、試験コストを誤認する。 | `duration_s`が外側wallであると明記する。baselineは外側32.211秒、pytest報告7.40秒。 |

**確認根拠・反証結果**

- **時間契約／検証弱体化の疑い：refuted。** `tools/check_branch_rescue.py:42`の定数は2秒、`:1591`は `min(timeout + CHECKER_EXIT_GRACE_SECONDS, overall_remaining)`。子引数`:1585`、残時間ゼロの早期return、`:1599`以降のJSON検証述語は基準との差分なし。利用者向けdocsの説明もこの式と一致します。
- **F33相当の偽kill：refuted（保存ログの範囲）。** m1/m3は実際に理由が `checker-timeout`へ変化、m2は7.008479秒で上限assertに失敗、m4は2.003515秒で下限2.8秒に失敗しています。全件 `timed_out=false`、artifact errorなし、保存stdoutのSHA256も一致。m4は時間契約pinとしてのみ数える扱いが適切です。m5は等価変異として91 passed／SURVIVEDであり、検出力の実績には数えません。
- **F34・記録後scan：訂正漏れはreal。** 裁定では限定したはずの「常に」や未実施受入が、統合された記録に残っています。旧レビューmust-fix 0を最終記録の正確性へ拡張できません。訂正後の記録は今回の監査対象外です。
- **F41・checkout混同：詳細記録ではrefuted、要約には注意。** README:45は修正前の共有checkoutと修正後wave木を区別し、T=8を同条件対照から除外しています。「0/2 → 4/4」は別条件の観測要約としてのみ扱えます。
- **現行への適合：静的に確認。** 旧変異対象 `b38442a98` と現行HEADで、rescue実装・対象テスト・landed checkerの差分はありません。旧結果を保持する根拠にはなりますが、現行tipの受入成功を意味しません。
- **過剰・削除レンズ：追加変更不要。** 定数1個と待機式1行、独立した3テストに収まっています。定数のCLI化、追加gate、台帳変更、一般化を持ち込む必要はありません。