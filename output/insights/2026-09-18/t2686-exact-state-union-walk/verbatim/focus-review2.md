## 総括

**GO（修正 driver での再測定へ）。must-fix なし。** 既存 producer の正常な merge 省略と実行失敗を区別する局所修正として妥当です。再測定成功の判定ではありません。

以下の `ab_compare.py` は[レビュー対象 driver](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2686-recovery-codex/ab_compare.py)です。closed は静的確認の完了を表します。

| 所見 | 対応 | 根拠・file:line |
|---|---|---|
| 正常 merge 省略の誤拒否 | closed | `ab_compare.py:37`。非decisive・reason不在・整数件数の整合を要求。実raw old-1 の closure=8、reported=6、omitted=unreported=2 と一致 |
| cherry timeout／parse error の拒否 | closed | [check_branch_landed.py:2073](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-measure-codex/tools/check_branch_landed.py:2073) が例外に `reason` を付与。driver:42 で例外許可から外れ、:57 で拒否 |
| 他層・子要素の truncation 拒否 | closed | `ab_compare.py:56` の完全なpath一致のみ許容。:62 の再帰は継続し、`truncated=true` も拒否 |
| 件数不整合の拒否 | closed | `ab_compare.py:43`–45。負数・bool・非整数、加算不一致、未報告数不一致、配列長不一致を拒否 |
| raw/canonical・判定の保持 | closed | `ab_compare.py:33`、:116。patch_id 全fieldを保持し、既存の timing 除外のみ。:124 で省略許容を summary に明示 |
| 修正後の実測成立 | partial | 再測定未実施。run1 の rc=1 は訂正・消去せず保持する |
| 今回の変更による退行 | regressed 該当なし | 指定 producer の経路について静的に確認した範囲 |

親裁定は、比較可能な実行完了と landed 判定を分けるものとして成立しています。`unreported==omitted` は producer が集合差から計算するため、既存経路では非mergeの欠落を許しません。ただし driver 自体はSHA集合を再構築せず、producer の件数を信頼します。任意に改ざんされたJSONまで検証する保証ではありません。

限界：静的読解と指定rawの参照のみ実施。fix報告の「4正例・56負例」は追試していません。同main・canonical一致・244→161 は提示された既存実測の事実として扱い、修正後の成功とはしていません。production/test変更、pytest、性能測定、子起動は行っていません。