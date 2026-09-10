## 総括

**NO-GO（静的判定）。** F1〜F4 は closed。F5 は改善しているものの、`fold_date` の単独改変が pin されておらず partial です。pytest は実行していません。

| ID | 判定 | コード根拠 |
|---|---|---|
| F1 | **closed** | `apply_fold` は noop の transaction ID・closure・targets・fragments・GC paths をすべて検査する。[spool_fold.py:2936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2936) |
| F2 | **closed** | author 全体を timestamp/timezone 込みで `re.fullmatch` するため、identity 後方への任意 bytes 追加は拒否される。[spool_fold.py:3106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:3106) |
| F3 | **closed** | 別の実在 ref だけを origin に設定し、transaction ID・closure・commit identity を整合させた fixture がある。拒否行だけを消すと recovery が finalize へ進むためテストが落ちる。[test_dev_wave_land.py:3532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_dev_wave_land.py:3532)、[dev_wave_land.py:2375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2375) |
| F4 | **closed** | path 集合、target status、blob OID、GC status の fixture が分離された。各 fixture は残る author/message/path/mode/OID/status 条件を明示確認しており、対応条件だけを欠かせる。[test_spool_fold.py:2316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:2316) |
| F5 | **partial** | 新設表は GC、fragment 全 field、projected bytes、rotation、target path/before/after SHA を一方だけ改変し、元の ID を保持している。しかし payload の `fold_date` が表にない。[test_spool_fold.py:2103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:2103) |

### 残る must-fix

**real / must-fix — `fold_date` の transaction-ID 束縛が単一理由で pin されていない**

- 実装項: [spool_fold.py:2184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2184)
- テスト上の穴: 既存の日付テストは transaction ID に加えて rendered worklog bytes、したがって target SHA も同時に変える。[test_spool_fold.py:2548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:2548)
- そのため `"fold_date": fold_date,` の一行だけを削除しても、target SHA の差によって `first.transaction_id != later.transaction_id` は成立し続ける。
- 成果物影響: transaction ID が state の宣言日を直接束縛しなくなる回帰を mutation/acceptance が見逃し、同じ target payload の state JSON で `fold_date` だけを改変できる。
- 必要な修正: 新設 state mutation table に `fold_date` 単独改変を加え、元の transaction ID を保持したまま exact ID 不一致を要求する。

なお origin 全 7 field・closure・target `before_exists` は旧テストで payload 行の削除自体は検出できますが、今回指定された「state JSON 側の一項改変」という形ではありません。[test_spool_fold.py:2057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/orchestrator/tests/test_spool_fold.py:2057)

### 追加確認

- 正当な noop は拒否されない。正規 plan は ID/closure/targets/fragments/GC が空で、観測済み `projected_worklog_bytes` や origin は許容されたままです。
- 実在 fold commit の raw author は以下で、F2 の正規表現に一致します。

  ```text
  author Izanagi Dev Wave <dev-wave@izanagi.invalid> 1786453944 +0900
  ```

- F1/F2 はいずれも受理集合を狭める変更で、新しい fail-open は見つかりません。
- F1〜F4およびF5の追加済み各 caseについては、対象実装条件の一行削除を検出します。残る未検出行は上記 `fold_date` です。
- fix の実装差分は `tools/spool_fold.py` の F1/F2 に限定され、finalize 冪等性、state CAS、手動 commit provenance、rollback 残骸など裁定パッケージ／backlog 項目への部分実装はありません。