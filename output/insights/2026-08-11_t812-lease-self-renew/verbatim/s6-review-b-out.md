## 所見

### B-01 / must-fix / 手製 `acquired` payload が実 helper 契約を偽装し、正常な初回取得を拒否する回帰を見逃している

- file:line 根拠:
  - `tools/wave_land_window.py:245-251` の実 `acquired` 応答は `holder_self=True`。
  - `tools/dev_wave_wait.py:609-631` は `acquired` を設定した後も `elif holder_self` に入り、`claim-self-unverified` を送出する。
  - `orchestrator/tests/test_dev_wave_wait.py:196-197` の `_acquired()` は `{"state":"acquired"}` しか返さず、この分岐を回避している。
  - 新 E2E `:2240-2288` は先に lease を取得してから二走目だけを見るため、初回 `acquired` を通らない。
  - 既存 real-helper テスト `:2112`、`:2295`、`:2349` が親実走で同じ stage により赤。
- 具体的な生存系列: 実装を現状どおり「`acquired` かつ `holder_self=True` を拒否」に壊しても、新しい `_FakeEffects` 系は `holder_self` を省略するため緑を保つ。
- 成果物影響: 空 lease からの通常受入が全停止し、受入結果・land・台帳更新を生成できない。
- 修正案: `acquired` を `holder_self` guard から除外する。そのうえで `_acquired()` を実 helper と同じ完全 payload にし、`state=="acquired"`、`holder_self is True` から command が一度実行され、release 権限が `ACQUIRED` になる正例を追加する。

### B-02 / must-fix / M04 は `_same_entry` の呼出し順だけを偽装すれば生存する

- file:line 根拠:
  - 本来の順序は `utime → fstat → _same_entry` (`tools/wave_land_window.py:735-746`)。
  - テストは「lease に対する二回目の `_same_entry` を False」にするだけ (`orchestrator/tests/test_wave_land_window.py:288-301`)。
- 具体的な生存変異:

  ```python
  # os.utime より前へ追加
  if not _same_entry(directory_fd, _LEASE_NAME, lease.metadata):
      return self_renew_failed(...)
  os.utime(lease.fd, ...)
  refreshed_metadata = os.fstat(lease.fd)
  # 更新後の _same_entry は削除
  ```

  テストでは追加した pre-renew 検査が「二回目」になって `unavailable` を返すため緑だが、更新後の pathname 置換は検出できない。
- 成果物影響: lease pathname が更新中に別 inode へ交換されても旧 inode の更新を成功報告し、排他を失った受入を正当化しうる。
- 修正案: `os.utime` の spy 内で pathname を unlink・別 payload の inode に置換し、その後の claim が `self-renew-failed`、置換物 bytes 不変になることを実ファイルで assert する。併せて操作列が `utime < post-fstat < same-entry` であることを固定する。

### B-03 / must-fix / M09 は post-flock `os.stat(path)` への置換で生存する

- file:line 根拠:
  - R-2 実装は flock 後の descriptor `fstat` (`tools/wave_land_window.py:312-324`)。
  - テストは flock callback で同一 inode の mtime を更新し、最終 state/inode だけを見る (`orchestrator/tests/test_wave_land_window.py:364-391`)。
- 具体的な生存変異:

  ```python
  initial_metadata = os.fstat(fd)
  _flock_bounded(fd, ...)
  metadata = os.stat(_LEASE_NAME, dir_fd=directory_fd, follow_symlinks=False)
  ```

  同一 pathname/inode の現 fixture では更新後 mtime が見えるため全 assert を満たすが、必要な post-flock `fstat(fd)` は消えている。
- 成果物影響: flock 対象 fd の payload と pathname 側 metadata が別 inode に由来しうるため、fresh lease の誤回収または誤った holder 判定から排他が破れる。
- 修正案: flock 取得直後に pathname を別 inode へ交換する fixture を追加し、metadata が必ず locked fd の `fstat` 由来で、entry 不一致を fail-closed にすることを assert する。操作ログでも flock 後の対象 fd に対する `fstat` を一回以上要求する。

### B-04 / must-fix / R-5 の「exact」受理条件に対する負例が不足している

- file:line 根拠:
  - 現在の負例は `holder_self=False`、age が文字列、source の値違い、非 hex holder の4件だけ (`orchestrator/tests/test_dev_wave_wait.py:696-723`)。
  - 実装の exact source 比較と厳密 int 判定は `tools/dev_wave_wait.py:619-629`。
- 具体的な生存変異:
  - `source == {...}` を `source.get("status") == "ok" and source.get("reason") is None` に緩和すると、余分な key または欠落 key を受理しても現テストは緑。
  - `type(age_seconds) is int` を `isinstance(age_seconds, int)` にすると `True` を受理しても緑。
  - holder regex を大文字 hex も許す形へ広げても、現負例は殺せない。
- 成果物影響: 裁定外の helper schema を `held-self` として受理し、受入集合を無断で拡大する。
- 修正案: `source` の extra/missing key、`age_seconds=True`、12桁大文字 hex holder を parametrize に追加し、すべて exact `stage=="claim-self-unverified"`、sleep/submission/release 各0を要求する。

### B-05 / must-fix / M11 は status が一時 renew して復元すれば生存する

- file:line 根拠: `test_self_status_does_not_renew_or_rewrite_lease` は呼出し前後の mtime/payload だけを比較している (`orchestrator/tests/test_wave_land_window.py:823-838`)。
- 具体的な生存変異:

  ```python
  old_ns = os.fstat(lease.fd).st_mtime_ns
  os.utime(lease.fd, ns=(now_ns, now_ns))
  os.utime(lease.fd, ns=(old_ns, old_ns))
  ```

  最終 bytes/mtime は一致するため緑だが、並行 claimant は途中の fresh mtime を観測できる。
- 成果物影響: stale lease の回収が監視 `status` との競合で抑止され、受入 timeout・land 停止を引き起こしうる。
- 修正案: setup 完了後に `WLW.os.utime` を spy 化し、`status` 中の呼出し回数が厳密に0であることを、既存の前後 bytes/mtime 比較と併記する。

### B-06 / nit / R-7 の「実 lease」assert は fake release counter と同じ一理由に過剰決定されている

- file:line 根拠:
  - marker holder は固定 `"0123456789ab"` (`orchestrator/tests/test_dev_wave_wait.py:213-230`) だが、実 holder は wave SHA-256 (`tools/wave_land_window.py:101-104`; `_WAVE` の値は `751098ecca7e`)。
  - release 時の unlink も実 helper ではなく fake 内の人工処理 (`orchestrator/tests/test_dev_wave_wait.py:371-376`)。
  - 三テストの lease bytes/mtime assert は `:1432`、`:1454`、`:1474`。
- 恒真・過剰決定系列: 各ファイル assert は `fake.releases == 0` と同じ fake branch の裏返しで、実 helper の ownership 判定から独立していない。なおテスト全体が恒真なのではなく、artifact 部分が冗長。
- 成果物影響: release 呼出し回数自体は別 assert が守るため、追加の未検出成果物影響は示せない。よって nit。
- 修正案: marker を `_holder_for(_WAVE)` 相当で作るか、実 helper の `claim` で作成する。少なくとも一つの赤/signal テストでは subprocess を実 helper へ委譲し、実 release が走れば本当に lease が消える oracle にする。

## M01〜M12 変異評価

| 変異 | 判定 | 検出根拠または生存形 |
|---|---|---|
| M01 | KILL | helper state exact `test_wave_land_window.py:169`、実二走目 `test_dev_wave_wait.py:2288-2292` |
| M02 | KILL | held-self から command 一回 `test_dev_wave_wait.py:648-663` |
| M03 | KILL | 実 mtime exact `test_wave_land_window.py:175` |
| M04 | **等価変異生存** | 登録された単純削除は `:246-310` が殺すが、pre-renew へ検査移動で生存。B-02 |
| M05 | KILL | 4注入の exact unavailable/reason `test_wave_land_window.py:241-310` |
| M06 | KILL | 赤/postclaim/signal の release 0 `test_dev_wave_wait.py:1430,1452,1472` |
| M07 | KILL | merge abort の実行要求 `test_dev_wave_wait.py:1397-1410` |
| M08 | KILL | exact `claim-self-unverified` と sleep 0 `test_dev_wave_wait.py:685-693` |
| M09 | **等価変異生存** | 単純 pre-snapshot 復帰は殺すが、post-flock pathname `stat` で生存。B-03 |
| M10 | KILL | synthetic 0 に対する実 age 7 `test_wave_land_window.py:184-199` |
| M11 | **等価変異生存** | 単純 `utime` は殺すが、更新後復元で生存。B-05 |
| M12 | KILL | 例外が `main` の rc=2 になれば `_claim` の `rc==0` (`test_wave_land_window.py:89-91`) が赤。ただし rc/stage oracle は粗い |

## R-1〜R-7 被覆

| 要件 | 実在テスト | 判定 |
|---|---|---|
| R-1 | renew/state `test_wave_land_window.py:155-181`; waiter進行 `test_dev_wave_wait.py:648-663`; real二走目 `:2206-2292` | **部分被覆・must-fix**。初回 acquired 回帰を fake が隠す（B-01） |
| R-2 | `test_wave_land_window.py:364-391` | **部分被覆・must-fix**。fd 由来を固定していない（B-03） |
| R-3 | `test_wave_land_window.py:184-220` | 被覆あり。age=7 と stale fail-closed が独立 |
| R-4 | producer 4注入 `test_wave_land_window.py:241-313`; consumer exact stage `test_dev_wave_wait.py:726-779` | 被覆あり。M05/M12 は殺す |
| R-5 | positive `test_dev_wave_wait.py:648-663`; legacy/invalid `:666-723` | **部分被覆・must-fix**。exact schema の緩和変異が生存（B-04） |
| R-6 | `test_wave_land_window.py:823-838` | **部分被覆・must-fix**。一時更新を観測しない（B-05） |
| R-7 | merge/red/postclaim/signal `test_dev_wave_wait.py:1388-1474`; cleanup count `:1939-1968` | 被覆あり。sleep、release回数、exact stage、実ファイル最終値あり。ただし artifact oracle は nit（B-06） |

## 弱体化・meta-test 確認

既存テストの skip・削除・期待値反転・parametrize 縮小はない。`test_acceptance_non_acquired_state_never_runs_command` の改名後も対象4 state は同一 (`test_dev_wave_wait.py:622-645`) で、`held-self` を新たな受理 state としたことによる名称修正に留まり、保護性質は減っていない。

両テストファイルは pytest-only allowlist に既存登録済み (`orchestrator/tests/README.md:133,169`) なので、`test_plain_runner_coverage.py:60-86` の静的要求は満たす。親提示の実走には meta-test が含まれないため、その実行結果が緑とは主張しない。

## 総括

- must-fix は **5件**、nit は1件。
- 最危険1: fake `acquired` が実 helper payload を偽装し、通常の初回受入停止を見逃した B-01。
- 最危険2: 更新後 inode 照合を pre-renew へ移せば生存する M04 / B-02。
- 最危険3: locked fd の re-`fstat` を pathname `stat` に替えても生存する M09 / B-03。