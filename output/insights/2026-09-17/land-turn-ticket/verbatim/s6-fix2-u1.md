## 所見対応表 (closed / partial / regressed)

**項目11の明示的な停止条件に該当したため、修正前に停止しました。今回の編集はありません。**

| 所見 | 判定 | 状態 |
|---|---|---|
| R2 | partial | 最新 journal の再照合不足を確認。未修正 |
| R3 | partial | ticket 作成前に空 registry が永続化されないことを確認。未修正 |
| R4 | partial | 汎用例外処理による retryable 分類の消失を確認。未修正 |
| N1 | partial | 同 key の完了解消が `waiting` になることを確認。未修正 |
| R1 再確認 | partial | fix-1 報告を確認。今回の実走・seq 保持検証は未実施 |
| B1 | partial | grant・終了順の assertion 未追加 |
| B2 | partial | `applied` 再入 parameter 未追加 |
| B3 | partial | 元票・grant・採番対象の観測未追加 |
| B4／M7 | partial | 再照準未完了 |
| B5 | partial | subprocess 死亡 test 未追加 |
| 残1件 | partial | ancestor-symlink が static 受入検証に影響することを確認。指定どおり停止 |
| 焦点走の赤 | partial | 上記 test 1件。未解消 |

## 変更の要約 (関数・行)

変更なし。停止の根拠は以下です。

- [ancestor-symlink fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/orchestrator/tests/test_dev_wave_land.py:5379) は、`git rm -r tools` 後に `tools` 自体を symlink として commit します。このため tested tip の Git tree に `tools/dev_wave_wait.py` が存在しません。
- [`_verify_acceptance_static`](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/tools/dev_wave_land.py:970) は、作業ツリーだけでなく、次の Git object lookup を必須としています。

```python
waiter_result = _git(
    repository.wave,
    "rev-parse",
    f"{tested_tip}:tools/dev_wave_wait.py",
)
if waiter_result.returncode != 0:
    raise _acceptance_rejected(retryable_same_request=True)
```

Git tree 内の symlink は、外部ディレクトリを辿ってこのパスを解決しません。したがって **`make_acceptance_receipt=True` だけでは、この case に有効な受入 receipt を持たせられず、provenance の rc=29 より先に受入拒否 rc=23 になります。**

これは項目11の「影響を受けるなら……報告して止める」に該当します。期待 rc=29、検証処理、既存差分は変更していません。

## 追加・変更した test と理由

なし。停止対象は次の node です。

`orchestrator/tests/test_dev_wave_land.py::test_provenance_checker_missing_and_symlink_components_are_rejected_clean`

ancestor-symlink case の fixture と登録前提 h′ の両立について、追加裁定が必要です。

## M7 の再照準結果

未完了。fingerprint の実装は確認しましたが、候補入力の検証・変異実走はしていません。KILLED／SURVIVED は申告しません。

## 変異 exact 登録表 (id / file / old / new / 期待 node)

停止により未作成です。M0〜M13（U2 所有の M10 を除く）の一意な置換・対応 node を検証できていないため、登録可能な表としては提示しません。

## 実走結果

今回の pytest・変異実走はありません。

提供された `focus-u1-land-2.log` の `IZANAGI_FAILURE rank=1` は、上記 node の **missing case** における期待 rc=29／実際 rc=23 でした。ancestor-symlink の停止判断は、fixture と static verifier のコード照合に基づきます。

## 総括

**項目11で指定された停止条件を確認したため、未編集・未実走で停止しました。** ancestor-symlink case は waiter の Git tree entry も削除するため、receipt 作成を有効化するだけでは登録前提を通過できません。残りの修正・変異登録も未完了です。
