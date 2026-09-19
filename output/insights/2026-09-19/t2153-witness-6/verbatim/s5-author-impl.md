## 総括

**所有6ファイルに実装済み・テスト未実走です。**

- SORT／REPORT を順序どおり登録し、件数を17へ更新。rung1 は factory 経由へ配線しました。
- 正負例、companion argv 検査、REPORT だけの未確立解除、S1 実 evaluator 経路の検査を追加しました。
- `DEFINE_SPECS`、factory、計装・比較・旧宣言・CLI の bytes 不変を確認しました。docs・probe は未変更、commit なしです。

検査結果：

| 検査 | 結果 |
|---|---|
| 指定10ファイルの焦点走 | rc=16、実走 nodeid **0件** |
| B-4 静的 inventory | rc=16、実走 nodeid **0件** |
| `check_codex_agents.py` | rc=0 |
| `check_docs.py`（literal pin 含む） | rc=0 |
| 6ファイルの構文・差分検査 | 通過 |

未実走の原因は `qstat -Q` preflight rc=1。テスト子プロセスは未起動で、テスト所要・増分は評価不能です。件数・順序・`MEANING_SUPPORTED_MACROS` の pin は焦点走対象に含まれます。

静的な波及先は、所有外 caller の S1→s8b floor／oracle・s8c、共有 `SORT_VARIANT_SOURCE` の consumer である `test_p3_exploration_namespace`、`test_p3_build_authority_cli`、`test_sort_swo_oracle` です。p3_s4_loop_sort／s6_sort_sweep は配線を維持しました。

対象経路は変更前の **unestablished admit** から、変更後は **meaning green なら admit／red なら reject** になります。この巡での動的確認は未完了です。