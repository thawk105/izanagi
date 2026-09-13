## 総括

README の SHA-256 は指定値と一致しました。  
既存テストが旧 README hash を literal で要求しているため、指定の更新と衝突します。  
「期待値が誤りなら実装を変えずに報告して止める」に従い、変更せず停止しました。  
現状の `load_policy(V3_SIZED_STUDY_ID)` は失敗します。

## 所見への対応表

| 所見 | 状態・根拠 |
|---|---|
| README／policy の pin 更新 | partial：README 実測済み。既存期待値との衝突により未編集 |
| M1 訂正と 5 項目の確認 | closed：指定された静的判定を完了。変異実走は未実施 |

## 変更した file と要点

変更なし。テスト・README を含め、編集していません。

## 変異の単独理由性の判定

対象は `test_v3_sized_certificate_requires_registered_parameters[...]`。**pin の整合を回復した後**では、次のすべてが対象項目の削除によって `DID NOT RAISE` になると静的に判定します。

| 削除する定数の項 | 対応 node パラメータ | 判定 |
|---|---|---|
| `search.trials` | `search-trials` | 単独理由で赤 |
| `certification.trials` | `certification-trials` | 単独理由で赤 |
| `candidate_grid.registered_minimum` | `registered-minimum` | 単独理由で赤 |
| `candidate_grid.maximum` | `maximum` | 単独理由で赤 |
| `root_seed.digest` | `root-seed` | 単独理由で赤 |

fixture の正例は項削除では拒否されません。負例は証明書を canonical bytes で書き直し、binding hash も更新します。変更フィールドを他の意味検査は拒否せず、呼出先は policy bytes pin を行わない `_validate_policy_semantics` です。

現状では fixture の `load_policy` が README hash 不一致で先に失敗します。また、上表は「その node の失敗理由」の判定であり、他の負例も同じ変異を検出しうる点には注意が必要です。

## 実走した検査

`PYTHONDONTWRITEBYTECODE=1 python3 -B` で hash 再計算と `load_policy` を実行しました。

テストラッパーは停止指示に従い未実行。pytest の passed／failed 件数はありません。

## 赤と、その帰属

- 実測：`load_policy` が `PaperStoryError: human-readable preregistration bytes differ`。更新済み README と旧 pin の不一致によります。
- 静的確認：[既存テストの期待値](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a1-sizing-certificate/orchestrator/tests/test_paper_story_a1_paired.py:1301) が旧 hash を要求。指定の 3 箇所だけを更新すると、この assertion が失敗します。

## 実測した hash

README：

```text
6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2
```

現 policy bytes（`V3_SIZED_POLICY_SHA256` と一致）：

```text
4a1ff56962538fdeb8ecbde3349a597a633186d8e33f1f4651e960a8edd720be
```

指定の置換をメモリ上だけで行った場合の policy hash（未保存・定数未更新）：

```text
a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a
```

## 親へ返す項目

既存テスト 1301 行目の旧 hash literal の更新を、今回の期待値変更禁止の例外として認める必要があります。認められれば、指定 3 箇所と当該 literal を更新してテスト全体を実走できます。