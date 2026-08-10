R1/R2 は実装しましたが、指定テストが collection 前に停止したため、判定はどちらも `partial（実装済み・未実走）` です。

### R2 の切り分け

原因は fixture ではなく verdict 側の過剰拒否でした。

`_paired_verdict()` が正しい inside 観測である `denied` を、先行条件で「`reached` ではない」と拒否していました。このため S3/S5 が `inconclusive` となり、正常な `_good_stages()` でも overall `go` に到達できませんでした。

修正後の判定契約は次のままです。

- outside が `reached` でなければ `inconclusive`
- inside が欠落・不正なら `inconclusive`
- inside が `reached` なら `no-go`
- inside が `denied` かつ `inside_blocked=True` の場合だけ `go`

封じ込め要求は緩めていません。

### 第1巡 F1〜F15 の回帰確認

| 所見 | 状態 | 第2巡の確認 |
|---|---|---|
| F1 | partial | 正しい `DENIED` のみ GO。欠落・不正 sentinel は引き続き `inconclusive`。 |
| F2 | partial | PID identity・子孫消滅判定は未変更。 |
| F3 | partial | infinite-loop の子孫消滅判定は未変更。 |
| F4 | partial | execution binding は未変更。 |
| F5 | partial | write path 分離・errno 判定は未変更。 |
| F6 | partial | final publish を hard link create-only へ修正。部分永続化と fsync 順序は維持。 |
| F7 | partial | 反転反復測定・中央値/MAD 等は未変更。 |
| F8 | partial | runtime/build 両 profile は未変更。 |
| F9 | partial | proxy redaction・制御 UNIX socket は未変更。 |
| F10 | partial | outside build・source identity は未変更。 |
| F11 | partial | toolchain 契約は未変更。 |
| F12 | partial | EINVAL preflight と S1〜S7 双方向結線テストを追加。 |
| F13 | partial | DNS 対象は未変更。 |
| F14 | partial | declared configuration 表現は未変更。 |
| F15 | partial | R3-1 未 discharge 項目の明示は未変更。 |

静的確認では `regressed=0` ですが、pytest 未実走なので closed とは判定していません。

## 総括

| 所見 | 状態 | 対応 |
|---|---|---|
| R1 | partial | `renameat2(RENAME_NOREPLACE)` を完全に除去し、`os.link(tmp, final)` → `os.unlink(tmp)` に変更。実出力先 job directory で起動直後に sentinel を publish・検証・清掃し、失敗時は測定前に rc=4 で停止。EINVAL 注入時に canonical receipt、`COMPLETED`、sentinel 残骸が無いテストを追加。 |
| R2 | partial | fixture は正当、verdict が過剰拒否と切り分け。矛盾した inside `reached` 要求を除去し、正常な全7 stage が GO、各 stage の1項目破壊で当該 stage と overall が非 GO になるテストを追加。 |

集計は `closed=0 / partial=2 / regressed=0` です。

第2巡の編集ファイル:

- [t316_sandbox_backend_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:80)
- [test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py:239)

第1巡から dirty の `.pbs`、policy JSON、`test_hooks.py` は今回変更していません。docs 編集、commit、PBS 操作も行っていません。

指定検査は2回試行し、いずれも rc=16、実走 nodeid は0件でした。

```text
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

その他の検査:

- Python `py_compile`: 成功
- PBS `bash -n`: 成功
- policy JSON 構文検査: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし
- `renameat2` / `RENAME_NOREPLACE` の実装・テスト内残存: 0件
- docs 差分: 0件

残る既知の限界は、pytest nodeid が一件も実走していないことと、修正後 self-check を計算ノード上の実 `/work` 出力先ではまだ実走していないことです。F15 の variant 性能差、trace-enabled correctness、floor 再較正判断も引き続き scope 外です。