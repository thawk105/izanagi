# 逐語の可逆最小正規化 (DW-S07)

`git diff --check` に抵触する行末空白 (space / tab) だけを除去した。可視文字は不変。原本は wave job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/` の同名 file (codex/ 配下、または直下)。
復元法: 原本の sha256 と byte 数を下表で照合する。除去したのは行末の space / tab だけで、行の追加・削除・並べ替えはしていない。

| file | 原本 sha256 | 原本 byte | 変更行数 | 正規化後 byte |
|---|---|---:|---:|---:|
| `codex/author-a1.md` | `bfc3f4371f262e07e42ddefd2f9a6cc7b9ad70ffa86d3003ae58412b4aa0815d` | 10899 | 3 | 10893 |
| `codex/author-mocc.md` | `09de3a41ac748ccc2c4569ffd81058d5e42ed7732e1ece8c774998af82ab0b02` | 10795 | 3 | 10789 |
| `codex/consult-A.md` | `b71a6fbc2413f181859761706c8d59bb31db70a7d5e5792ecbbdde7f4b3bb969` | 8840 | 6 | 8828 |
| `codex/consult-B.md` | `be230a0e40c3836dfcced4133f8af8599f283d8015aaf158c48db954cc93cd8f` | 10804 | 7 | 10790 |
| `codex/focus.md` | `defc20c86dee844838eee9f5316bdae2ffd3c70a2fc509db9f10847d83140f1b` | 6852 | 3 | 6846 |
| `codex/review-A.md` | `3ecad09495e5fe80adf251f488d5420e1cf22851659805bf83122dcb40317797` | 8088 | 7 | 8074 |
| `codex/review-B.md` | `6084fba3fa97c92663c82ef43a867c8e25825fe65e74219486b886e3c1f71827` | 4260 | 6 | 4248 |
| `focus-1.log` | `99575ce52c32092a86bb36e182384b35579cd45bbc7032d987d55d7917a9d121` | 40700 | 117 | 40327 |
| `focus-2.log` | `cadfb19da811484c2750a20fa677db2905d0d276b15c088f606e73af872533ab` | 6405 | 2 | 6403 |
