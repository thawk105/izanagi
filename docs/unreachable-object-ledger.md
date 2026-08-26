# 到達不能 object 台帳

> **警告:** この台帳は所在を記録するだけで Git object を延命しない。救出は Git の ref を作り、
> その ref から到達可能であることを再検査して初めて成立する。同じ事実を機械可読にした固定 field は
> `object_retention_provided: false` である。

この文書は期限つき台帳と、`/cleanup-branches` dispatcher を通る掃除の可視化を保証する
rescue gate の運用契約である。schema 名は `izanagi-unreachable-object-ledger-v1` とする。

## 台帳 schema

各 entry の field は次の 23 個だけとし、追加も省略もしない。

| field | 型 |
|---|---|
| `schema` | string。`izanagi-unreachable-object-ledger-v1` |
| `entry_id` | string |
| `recorded_at` | string |
| `source_refs` | array[string] |
| `source_tips` | object。key=full refname、value=full oid string |
| `assessment_report_sha256` | string |
| `object_oid` | string |
| `object_type` | string。固定値 `commit` |
| `assessment_schema` | string。固定値 `izanagi-branch-landed-v1` |
| `assessment_verdict` | string enum: `landed` / `not-landed` / `indeterminate` |
| `assessment_reason` | string |
| `storage_kind` | string |
| `object_mtime` | string または null |
| `loss_possible_not_before` | string |
| `lower_bound_basis` | string |
| `gc_auto_threshold` | integer または null |
| `loose_count_at_loss` | integer または null |
| `gc_headroom_at_loss` | integer または null |
| `status` | string enum: `pending` / `rescued` / `accepted-loss` / `reachable-again` / `object-missing` |
| `resolved_at` | string または null |
| `rescue_ref` | string または null |
| `resolution_note` | string または null |
| `object_retention_provided` | boolean。固定値 `false` |

## 追記と状態遷移

entry は 1 object につき 1 JSON とし、この文書の末尾へ `- ` に続く単一行 JSON object として追記する。
削除・撤去後、事前 report の `deletion_loss_closure.commits` に含まれた commit が恒久 ref から
到達不能になった場合に追記する。`--ledger-check` が `unledgered-audit-finding` を出した object も
追記対象である。新規 entry の `status` は `pending` とする。

許される解決遷移は `pending` から `rescued`、`accepted-loss`、`reachable-again`、
`object-missing` のいずれかである。`rescued` は救出 ref を作り、その ref から object が到達可能と
再検査できた場合だけ使い、`rescue_ref`、`resolved_at`、`resolution_note` を記録する。
`accepted-loss` は人間が喪失を明示的に受容した場合、`reachable-again` は救出操作とは別に恒久 ref から
再び到達可能と確認した場合、`object-missing` は object が既に存在しないと確認した場合に使う。
解決済みまたは陳腐化した entry は削除せず、解決 field を更新して監査履歴として残す。

`tools/check_branch_rescue.py` はこの台帳を自動編集しない。追記候補と判断材料を JSON へ出すだけであり、
台帳の更新は出力を確認した作業者が行う。

## rescue gate の運用契約

削除する全 branch と撤去する全 worktree を、掃除操作と同じ集合のまま 1 回で起動する。

```text
python3 tools/check_branch_rescue.py --ledger-check \
  --branch <name>... --retire-worktree <absolute-path>...
```

`--branch` と `--retire-worktree` は必要な回数だけ反復する。一候補ずつ別々に実行してはならない。
候補が無い台帳照合だけの場合は `python3 tools/check_branch_rescue.py --ledger-check` とする。
`--ledger-check` は dangling audit の要確認 commit と台帳を照合し、未記帳 object および期限が
近いか過ぎた `pending` entry を JSON の通知へ出す。これは object を保持せず、台帳も変更しない。

rc の契約は次のとおりであり、削除可否そのものを表さない。

| rc | 意味 |
|---|---|
| `0` | root snapshot、閉包、全 commit の判定と期限を含む可視化が完全 |
| `2` | timeout、上限超過、root 移動、期限算出不能、台帳 parse 不能などで技術的に不完全 |
| `3` | 可視化は完全だが、未記帳 object または期限が近い未裁定 entry の通知あり |
| `64` | usage error |

rc `1` は使わない。`not-landed` は技術的失敗ではなく JSON 内の判断材料である。全 rc と JSON 結果を
`/cleanup-branches` §5 の報告へ含める。

### dangling audit の分岐

`python3 tools/audit_dangling_commits.py --offrepo-root <runbook §7.2 の dir>` は単独実行し、
パイプへ渡さず rc を直後に保存する (F152)。rc `0` は削除手順を続行できる。rc `1` は §5 へ報告し、
救出を判断する。rc `2` は実行不能なので削除を停止する。抑止行が出た場合は rc `0` でも §5 へ報告する。
最終 `elapsed_seconds=` が欠けた場合と未知の rc は削除を停止する。上限超過行は §5 へ報告するが、
rc と削除可否を変えない。上限の正本は tool の `--help` とする。

## 覆わない範囲

1. 手で打つ `git branch -d`。
2. `DW-O28` の自動撤去 (`tools/dev_wave_cleanup.py`)。
3. D978 の未施行部分。

## entry

現在、記録済み entry はない。
