# verbatim の可逆最小正規化 (DW-S07)

`git diff --check` に抵触する行末空白 (space / tab) を除去し、EOF の改行を 1 つにした。可視文字は不変。
原本 (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/` の同名 file) の sha256 と byte 数を下表に記録する。
復元法: unified diff の空文脈行は 1 個の space (` `) に戻す。log / md の行末空白は元の出力の区切り文字であり意味を持たない。
README.md の本文は正規化前後で可視文字が同じ。

| file | 原本 sha256 | 原本 byte | 変更行数 | 正規化後 byte |
|---|---|---:|---:|---:|
| `README.md` | `85b2b4a330ea86177e1663203feebe835fa745dc898bb7071041c8c9ae3243c9` | 31635 | 0 | 31634 |
| `verbatim/W.patch.txt` | `4ef9c387068abf9dcdd123ba87691b4d613cdb36fff9c541448c147367095aff` | 2412 | 3 | 2409 |
| `verbatim/check-smoke-witness-001.log` | `94e017747775df8cd22f4a92c066352152ecc5b422d93bb18823db29dcf7a3cb` | 535 | 2 | 533 |
| `verbatim/check-smoke-witness-003.log` | `97ee3dd3ebaa84ac6138314ff1626fe6620b82b8360a062f37b0d2e67128e096` | 539 | 2 | 537 |
| `verbatim/dispatch-W1.log` | `a4430e28f77895154e7d61581f5ab85de09f1bef19c92a5f69dc0a6a422aad64` | 4178 | 1 | 4177 |
| `verbatim/dispatch-W2.log` | `021a2876e277dae4e6f2d3560ced3ecd2f10a5dbdc81a115ecb10a06eb761d07` | 4148 | 1 | 4147 |
| `verbatim/dispatch-W3.log` | `3f4d9fb38c8a2248f36c6444c6ada59f45a642747725e742ddb6a43ab0d872d0` | 4127 | 1 | 4126 |
| `verbatim/dispatch-W4.log` | `7be5141062d54f8b38ebb19eecbd576f3898d8ae17a9aac1fc564ad77583063b` | 4148 | 1 | 4147 |
| `verbatim/dispatch-smoke.log` | `2edeb3859f84622a2a97e54e14d2985682d68403860c4f38fe3d21998b9b1d3a` | 4364 | 1 | 4363 |
| `verbatim/mk-W-commit.log` | `d01c071f51957ab802de70abb6831fe61e14a602412c3f1727e3f88ff9425091` | 2202 | 2 | 2194 |
| `verbatim/s2-plan.md` | `12086ddda86d03557c387b9f268cb1b0089fdc50144515245a4950724b262146` | 34891 | 3 | 34889 |
| `verbatim/s3-lensA.md` | `1187c95291582510740122feeae3a7f29c57c0cca027055c5024bc99274d9ab3` | 14242 | 0 | 14243 |
| `verbatim/s3-lensB.md` | `7a57acc2f04209934c8ee36c256284a1a10ea6e016eb41589505e4c9191daceb` | 17548 | 0 | 17549 |
| `verbatim/s5-author.md` | `a5fd21dd3b22a7079d304751286f0039c73e70cc249ec2fdff445501f187f466` | 4491 | 1 | 4490 |
| `verbatim/s6-reviewA.md` | `26eebea2b88444bc38ea67d3cd7dba88aa10fdd7c266c1594b90f5d5cf39a68f` | 11756 | 0 | 11757 |
| `verbatim/s6-reviewB.md` | `e6326a4960edf30d05145e0d612e980591ff0a1045ae00ef4d8d920a44a3e3c2` | 13633 | 0 | 13634 |
| `verbatim/witlight.patch.txt` | `0648e2c6de46319da02056cb516d706ff9f09c3c0ffb2cadb6c94ee069473363` | 2557 | 5 | 2552 |
