## 所見ごとの対応表 (closed / partial / regressed、所見 ID → 変更箇所)

| 所見 | 状態 | 対応 |
|---|---|---|
| J1 | closed | 新負例の assertion を完全一致から先頭一致へ変更。7ケースの直接呼出し成功 |
| J2 | closed | production・S・登録簿・fixture の fail-closed assert・既存 landed test の期待値は不変 |

## 実装した変更 (file ごと)

[test_s8b_ratified_freeze.py:1539](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-t080-fix5/orchestrator/tests/test_s8b_ratified_freeze.py:1539) の1行のみ変更しました。

```python
assert str(caught.value).startswith(f"receipt base missing input: {missing}")
```

不足 path の検査を維持し、pytest が追記する assertion 説明を許容します。

## 接続正例 fixture の結果

本巡では**呼出し不能**です。driver module の import が `GrowthTestHoldBypassRefused` に拒否されました。guard は解除していません。

各段を現物で静的検算しました。

| 段 | 確認内容 |
|---|---|
| basis | orchestrator・output・role・source closure・ccbench を初期材料として構成 |
| R | 実 draft → validate → finalize → receipt commit |
| selector seed / protocol | copy 内7入力を確認し、protocol・seed・selector 証拠を生成 |
| C | fixture root と既存 ccbench pin を渡し、certificate を commit |
| G | 通常経路は `frozen_at_head=C` として世代を commit |
| A → X | approval、active pointer を順に commit |
| 接続 | 実 load・launch・receipt verifier を使用 |

## 自己検証の結果

| 検証 | 結果 |
|---|---|
| 変更 module の import | 成功 |
| 対象 test の直接呼出し | `tempfile.mkdtemp()` を使用し、7/7成功 |
| m6 predicate 反実仮想 | process 内属性差替えで試行。token 構築が `machine-pin: 未対応 site 'PEGASUS_LOGIN'` で停止。kill 証拠には数えない。属性復元済み |
| 全変更 file の AST parse | 成功 |
| `git diff --check` | 成功 |
| landed test 保護 | 変更対象 test が基点 `24ede1d11` に存在しないことを確認 |
| driver sink pin | `pipeline.evaluate`: 1781、`evaluate_fn`: 1794。両 pin と一致 |
| 最終差分 | 1 file、1行置換のみ |

## 所有外への波及

`grep -rn` で共有 fixture の caller を列挙しました。対象は migration、oracle driver、oracle report、verdict、ratified verify、oracle manifest、および同 module 内の通常 fixture です。

変更は新負例の assertion 本文だけであり、共有 builder・`load_emitter_g1`・g2 emitter・署名・登録簿への変更はありません。

## 変異事前登録への対応 (m0〜m11 の anchor 更新、位置の一意性)

production の行番号は不変です。以下は `orchestrator/campaign/` 配下です。

| ID | anchor |
|---|---|
| m0 | `t080_freeze_migration.py:2231` comment |
| m1 | `s8b_ratified_freeze.py:3550` 完全一致比較 |
| m2a | `s8b_oracle_driver.py:200` `allowed=not merged` |
| m2b | 同`:220` invalid 拒否文言 |
| m3 | `t080_freeze_migration.py:2275` search assertion |
| m4a / m4b | 同`:2215` / `:2202` 束縛比較 |
| m5 | `s8b_oracle_driver.py:1531` campaign-start 再解決 |
| m6 / m7 | `t080_freeze_migration.py:2236` / `:2247` |
| m8a | `s8b_floor_campaign.py:5534` |
| m8b | `t080_freeze_migration.py:1728` |
| m9 / m10 | 同`:2234` / `:2241` |
| m11 | `fresh_validated` 不在。fix-4 報告の除外扱いを変更せず |

m0〜m2b は file 内、残りの現存 anchor は対象関数内で一意と確認しました。m3 の assertion 文字列は file 全体では2箇所あるため、`_verify_holdout_live_scan` に限定する必要があります。

## 未完・未実走・懸念

- pytest／`tools/run_tests.py`、修正後の両木焦点走、正式変異 matrix は未実走です。
- 接続正例と m6 の検出力は、本巡の直接呼出しでは確認できていません。
- 親ログの chain 有り1097 passed／7 failed は修正前の結果です。
- commit・docs 編集・報告ファイル作成は行っていません。

## 総括

**J1 を指定どおり1行修正し、不足入力7ケースの直接呼出し成功を確認しました。** 変更は未 commit で残しています。pytest 下での最終確認は親の焦点走に残ります。