| 所見 | 判定 | 根拠 file:line |
|---|---|---|
| A Blocker 1: inventory 判定不能 | closed | `tools/mutation_harness.py:1780-1788,1840-1892,2080-2090,2136-2178` |
| A Blocker 2: directory は qsub 証拠でない | partial | `tools/pegasus/dispatch_compute.py:1535-1562,1664-1676`; `orchestrator/tests/test_mutation_harness.py:80-109,945-1002` |
| A Blocker 3: 共有 namespace の誤認 | partial | `tools/mutation_harness.py:1518-1527,1650-1669`; `tools/run_tests.py:930-950` |
| A Blocker 4: local が既存 hold を無視 | closed | `tools/mutation_harness.py:281-290,2023-2032` |
| A must-fix: 非束縛な解除手順 | partial | `tools/mutation_harness.py:2690-2740`; `tools/mutation_worktree.py:1173-1179,998` |
| A 確認事項: dispatch mode と consumer | closed | `tools/mutation_harness.py:321-342,1831-1837`; `orchestrator/tests/test_mutation_harness.py:1226-1245` |
| B-1: queue 由来 terminal `TIMEOUT` は閉鎖 | regressed | `tools/mutation_harness.py:300-301,1650-1669,1904-1908,2080-2109` |
| B-2: runner-mode と argv の不整合 | partial | `tools/mutation_worktree.py:674-705`; `tools/mutation_fanout.py:656-687`; `tools/run_tests.py:1856-1862` |
| B-3: M2 kill の帰属不成立 | partial | `orchestrator/tests/test_mutation_harness.py:80-82,1908-1955`; `tools/mutation_harness.py:1778-1790` |
| B-4: M4/M5 の共有 gate | partial | `tools/mutation_harness.py:2080-2090`; `s4-ruling.md:113-114` |
| B-5: parameterized node 完全集合 | partial | `orchestrator/tests/test_mutation_harness.py:1908-1915`; `s5-author.md:35` |
| B-6: DW-M06 の逐語不整合 | partial | `docs/dev-wave/mutation.md:37-40`; `tools/mutation_harness.py:300-315` |
| B-7: local wrapper receipt の不整合 | partial | `tools/mutation_worktree.py:970-998,1163-1179`; `tools/mutation_harness.py:2715-2740` |
| B-8 | not-applicable | 指定された `s6-revB.md` は所見 7 で終了: `s6-revB.md:99,117` |
| B-9 | not-applicable | 同上。所見 8、9 は入力文書に存在しない: `s6-revB.md:99,117` |

### 最優先所見: nonce は所有証明になっていない

通常の `run_tests.py` 経路では、nonce は次のように運ばれるため、標準的な一回の dispatch では一致する。

`token_hex` → runner 環境 → `run_tests.py` の環境コピー → tests task allowlist → `request.json`

根拠は `tools/mutation_harness.py:1764-1768,1792-1800`、`tools/run_tests.py:930-950,1677-1689`、`tools/pegasus/dispatch_compute.py:76-89,1507-1511,1556-1562`。

しかし、一致は所有を意味しない。

- nonce が他 submission に載る経路: runner の全子孫が同じ環境を継承する。test が別の `run_tests.py` を起動し、それが別 argv を dispatch しても同じ nonce が request に入る。現 classifier は repo、task、argv が不一致でも nonce だけで `matched` にする (`tools/mutation_harness.py:1643-1662`)。
- 別 session も同じ Unix user なら、先行 request に永続化された nonce を読める。128-bit の推測困難性は、同一 UID 内の所有境界にはならない。
- nonce が載らない経路: 許可済みの local runner には `python -m pytest` がある (`tools/mutation_harness.py:741-758`)。test が環境を消すか、環境を明示的に絞った子から dispatcher を起動すると、v2 request は正しいまま `environment` に nonce を持たない。dispatcher は存在する allowlist key だけを記録する (`tools/pegasus/dispatch_compute.py:1507-1511`)。
- その valid request は `unrelated` となり、local timeout は停止を迂回して terminal `TIMEOUT` になる (`tools/mutation_harness.py:300-301,1650-1669,1907-1908`)。実際に qsub 済みでも `completed` が増えるため、B-1 は regressed。
- legacy v1 は dispatcher 自身が受理する (`tools/pegasus/dispatch_compute.py:596-611`) 一方、classifier は `task/args/environment` を必須にしている (`tools/mutation_harness.py:1621-1628`)。共有 namespace に新しい v1 directory が出ると、無関係でも `indeterminate` となって偽の停止を起こす。
- `secrets.token_hex(16)` 自体は通常空にならない。空または欠落は生成器ではなく、途中の環境投影や test 子によって生じる。

### `PYTHONDONTWRITEBYTECODE` の副作用

非空の nonce なので、標準経路では bytecode 生成抑止の意味は保たれる。現在の repo 検索では値が厳密に `"1"` であることを要求する production consumer は見つからず、dispatcher の既存テストも任意 sentinel の透過を明示的に許している (`orchestrator/tests/test_pegasus_dispatch_compute.py:3121-3153,3243-3261`)。

ただし、この変数は秘密用でも走行 ID 用でもない。全 test 子へ公開され、通常の環境継承で複製されるため、所有 nonce の運び屋には不適切である。

### 新たな偽の緑

追加された matched fixture は dispatcher を呼ばず、自分で現在の環境から nonce を読み、同じ値の `request.json` を直接書く (`orchestrator/tests/test_mutation_harness.py:80-109`)。classifier が検査する値を fixture 自身が複製するため、`run_tests.py` が実際には nonce を request へ渡さなくなっても、このテストは緑のままである。

さらに、同 fixture は scheduler を一度も呼ばないのに `job_may_have_been_submitted=True` を正解として固定する (`orchestrator/tests/test_mutation_harness.py:973-1002`)。request は qstat より前に作られるため (`tools/pegasus/dispatch_compute.py:1556-1575,1664-1676`)、preflight 停滞を実投入と区別できない。

`unrelated` 正例も nonce を単に欠落させている (`orchestrator/tests/test_mutation_harness.py:88-104,1005-1037`)。同じ nonce を持つ別 argv、別 repo、別 task が誤って `matched` になる反例は検査していない。

### 未 closed 所見の成果物影響

- A-2: qsub 前の request だけで停止し、未投入変異の terminal record が消えて K/M 台帳が未完了になる。
- A-3 / B-1: nonce の誤共有では無関係な走行が対象 record を消し、nonce 欠落では未実行変異が `TIMEOUT` と `completed` を増やす。
- A must-fix / B-7: wrapper receipt の `failure` が null のまま残り、K/M 台帳未完了の理由参照を機械検証できない。
- B-2: fanout shard が baseline で停止し、merge 済み K/M 値が生成されない。
- B-3〜B-5: M2、M4、M5を KILLED と数えると、帰属しない kill または `MISMATCH` が検出力分子へ混入する。
- B-6:正本どおり実装する次 wave が queue timeout を terminal `TIMEOUT` に戻し、`completed` と検出力分母を再汚染する。

pytest は実行していない。親の 196 passed は事実として受け入れたが、上記の恒真的 fixture と未被覆経路を閉じる証拠にはならない。

## 総括

未 closed は 10 件: partial 9、regressed 1。  
最優先は、nonce 欠落した実 submission が terminal `TIMEOUT` へ落ちる偽の緑。  
nonce 単独一致は所有証明にならず、現テストも実 carrier を検証していない。  
推奨は **NO-GO**。