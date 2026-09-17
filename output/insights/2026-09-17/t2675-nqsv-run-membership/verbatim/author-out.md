## 総括

- 作成: [tools/probe_t2675_run_membership.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2675-nqsv-run-membership/tools/probe_t2675_run_membership.py)
- 実測: **656 行、30,373 bytes**
- SHA-256: `f781162298f8885bd8d73f9e5d65d0d763fa14cc7e1673dd9961d42f9dc5b3e1`
- selftest: **13 passed, 0 failed、rc=0**。60秒以内の検査も通過。
- 未解決なし。変更は指定の1ファイルのみ。git add／commit、本走は未実施。

実装した条件と所属変更は次のとおりです。全子条件で fd 1/2 を保持します。

| 条件 | membership_change | change_seconds |
|---|---|---:|
| `no-child` | `none` | None |
| `keep` | `none` | None |
| `setsid-now` | `setsid` | 0 |
| `setsid-30` | `setsid` | 30 |
| `setpgid-now` | `setpgid` | 0 |
| `setpgid-30` | `setpgid` | 30 |

事象は `start`、`fork`、`parent-exit`、`child-start`、`before-change`、`after-change`、`child-alive`、`child-exit`、`child-error`。既定寿命では heartbeat を5〜70秒の14回記録し、30秒では所属変更を先に行います。

`change_membership()` は変更前所属を採取し、syscall を1回だけ呼び、変更後の不変条件を検査します。所属不整合・syscall 失敗・不変条件違反では、phase、errno、例外型・本文、取得済みの前後所属と syscall 時刻を `child-error` に記録して `os._exit(1)`。再試行や event loop への復帰はありません。

selftest の観察方法と結果：

| ID | 観察方法 | 結果（逐語） |
|---|---|---|
| S1 | subprocess rc、evidence 不在、fork／Recorder sentinel | `PASS S1` |
| S2 | 不正時間・順序の拒否、同上 | `PASS S2` |
| S4 | `/dev/full` の記録失敗、pidfd による1.9〜2.5秒の終了 | `PASS S4` |
| S5 | 親終了後も子の pidfd が未ready、その後終了 | `PASS S5` |
| S6 | `start`／`parent-exit` のみ、t0 存在 | `PASS S6` |
| S7 | setsid 後の evidence・外部 `/proc`・fd inode 照合 | `PASS S7` |
| S8 | setpgid 後の同照合、sid 不変 | `PASS S8` |
| S9 | 30秒前の所属、syscall 時刻、変更後所属 | `PASS S9` |
| S10 | S9と並行起動し、setpgid の同項目を検査 | `PASS S10` |
| S11 | 両 syscall に EPERM 注入、pidfd、`/proc` の rc=1、失敗後0.5秒以内の終了 | `PASS S11` |
| S12 | ゼロバイト短書き注入、write 回数・エラー保持・終了期限 | `PASS S12` |
| S13 | heartbeat 時刻・連番・30秒の順序、環境値非記録、metadata 読取り失敗注入 | `PASS S13` |
| S14 | 子の1秒 alarm、pidfd と `/proc` の SIGALRM 終了 status | `PASS S14` |

実走コマンド：

```text
python3 -B tools/probe_t2675_run_membership.py --selftest
```

stdout 全文：

```text
PASS S1
PASS S2
PASS S4
PASS S5
PASS S6
PASS S7
PASS S8
PASS S11
PASS S12
PASS S14
PASS S9
PASS S10
PASS S13
13 passed, 0 failed
```

終了コード: `0`

s4-ruling.md との実質的な差異はありません。小数の親時間を受理するため、整数秒を要求する `signal.alarm()` には `ceil(parent_seconds + 55)` を渡しています。S3 は登録していません。login selftest の成功は、計算ノードの内側 namespace での成功を証明するものではありません。

所有外の編集はありません。`git status --porcelain` の出力全文：

```text
?? tools/probe_t2675_run_membership.py
```