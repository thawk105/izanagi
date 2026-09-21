## 変更の要約

`test_s8b_oracle_driver.py` の指定定数と直上コメントだけを更新しました。rr80 / rr20 の hit を各3件へ変更し、候補 path を除去。削除後の live P3 実測と集合完全一致しています。

コメントには候補削除、historical reverify 成功、およびその成功が live admission の代替ではないことを記載しました。

## 変更前の挙動

- 第1要素：rr80 / rr20 とも official run_dir の3 file＋候補 path の計4件を列挙。
- 第2要素：`rr20::backoff_fixed_best` の admission receipt と現行 policy の不一致による `manifest-invalid` 拒否。

## 不変の確認

差分は指定定数とコメントの1箇所だけです。コメントの前3行、第2要素、`frozenset`、隣接文字列リテラル形式を維持しました。他ファイル・他行、新規ファイルの変更はありません。

`_assert_exact_refusals` の件数比較・集合完全一致、および6 node の assertion は不変です。揮発 payload は追加していません。git のステージ操作・commit 等は実行していません。

## 自己検査

指定 AST 照合の出力：

```text
MATCH True 2 2
CANDIDATE_ABSENT True
```

指定 `git diff --stat` の出力：

```text
 orchestrator/tests/test_s8b_oracle_driver.py | 14 ++++++++------
 1 file changed, 8 insertions(+), 6 deletions(-)
```

`git diff --check` も終了コード0でした。

## 波及

全参照は以下の6関数です。

`test_s8b_oracle_driver.py`：

1. `test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing`
2. `test_nonnull_floor_without_active_generation_is_refused`
3. `test_active_resolution_and_manifest_structure_refusals_are_aggregated`
4. `test_cli_subprocess_returns_rc_2_on_gate_refused`

`test_s8b_binding_driftguards.py`：

5. `test_run_block_broken_binding_manifest_refuses_and_writes_nothing`
6. `test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal`

1〜4は定数を直接、5〜6は `driver_fixtures._ACTIVATED_G1_REFUSALS` 経由で参照します。全関数が実 repo を root とする結果を `_assert_exact_refusals` へ渡すため、追加変更なしで新真値に追随します。

## 変異の見込み

- **M0：SURVIVED 見込み。** 等価なコメント変更は実行結果に影響しません。
- **M1：上記1〜6の全 node が KILLED 見込み。** 第1要素を旧値へ戻すと、各 node の拒否集合完全一致が失敗する想定です。件数は2のままですが、hit 数・候補 path が不一致になります。

これは診断感度の確認であり、production の受理集合に対する kill とは数えません。実測確定は親に委ねます。

## 未了・懸念

pytest・held 6 node・変異走は実行していません。親による計算ノードでの実測が残っています。

## 総括

指定範囲の更新と自己検査を完了しました。差分は working tree に残しています。