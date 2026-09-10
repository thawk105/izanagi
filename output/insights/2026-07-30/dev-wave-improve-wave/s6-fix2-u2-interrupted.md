# U2 第2 fix の bounded termination

第2裁定後のU2 owner worktreeでは、次の2 jobがtimeoutしoutputを発行しなかった。
両jobのcurrent bytesを直接green証拠にはせず、後続finalizerの未監査入力とした。

| job | 上限 | rc | output |
|---|---:|---:|---|
| `s6-fix2-u2` | 30分 | 124 | なし・不採用 |
| `s6-fix2-u2-closure` | 20分 | 124 | なし・不採用 |

後続 `s6-fix2-u2-finalize` は10分上限内でrc=0 / output format green。
R2〜R7/R9 closed、R8はlookup pairing negative不足1件だけをpartialとした。
そのpartialはtest-only `s6-fix2-u2-pairing` がrc=0 / format greenでclosedした。

採用するauthor報告は次の2件だけである。

- `s6-fix2-u2-finalize.md`
- `s6-fix2-u2-pairing.md`

timeout jobの可変run logや未発行draftは採用しない。親は最終U2 owner current bytesと
統合bytesのSHA-256一致を各pathで確認した。
