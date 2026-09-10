## 結論

production 変更なしで実装できる。ただし (P1-3) の「1 file」は realizability と両立しないため、`trace_0.log` と `trace_1.log` の **2 thread 構成**へ変更する。1 thread は逐次実行なので、後発 T3 が T0 より前に genesis を読む実行を表せない（[parse.py:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:5)、[parse.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:20)）。

設計する DSG は次の単純環である。

```text
T0 --wr--> T1 --wr--> T2 --wr--> T3 --rw--> T0
```

辺はこの4本だけなので、短い巡回も複数巡回も生じない。

## 新 fixture の trace 全行

`orchestrator/tests/fixtures/r9_dense_cycle4/trace_0.log`:

```text
C 0 0 1 1 0 2
W 0 0000000000000001 U 1 1
W 0 0000000000000002 U 1 1
E 0
C 1 0 1 2 1 1
R 1 0000000000000002 1 1
W 1 0000000000000003 U 1 2
E 1
C 2 0 1 3 1 1
R 2 0000000000000003 1 2
W 2 0000000000000004 U 1 3
E 2
```

`orchestrator/tests/fixtures/r9_dense_cycle4/trace_1.log`:

```text
C 3 1 1 4 2 0
R 3 0000000000000001 1 0
R 3 0000000000000004 1 3
E 3
```

実現可能な一例は、T3 がまず key 1 の genesis を読み、その間に thread 0 が T0→T1→T2 を逐次 commit し、最後に T3 が T2 の key 4 を読んで commit するスケジュールである。

## trace 各行から生じる辺

`C/R/W/E` の解釈は [parse.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:240)–[parse.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:346)、producer と版列の登録は [dsg.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:49)–[dsg.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:75)、read 辺は [dsg.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:81)–[dsg.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:105) に従う。

| file:line | 行 | DSG への効果 |
|---|---|---|
| `trace_0.log:1` | `C 0 0 1 1 0 2` | T0、commit `(1,1)`、R=0/W=2 を宣言。辺なし |
| `trace_0.log:2` | `W 0 …0001 U 1 1` | key 1 `(1,1)` の producer=T0。後の genesis read と組み `T3→T0` の rw |
| `trace_0.log:3` | `W 0 …0002 U 1 1` | key 2 `(1,1)` の producer=T0。`trace_0.log:6` と組み `T0→T1` の wr |
| `trace_0.log:4` | `E 0` | T0 frame を正常終了。辺なし |
| `trace_0.log:5` | `C 1 0 1 2 1 1` | T1、commit `(1,2)`、R=1/W=1。辺なし |
| `trace_0.log:6` | `R 1 …0002 1 1` | 読んだ版の producer=T0 なので wr `T0→T1`。key 2 に後続版がなく rw なし |
| `trace_0.log:7` | `W 1 …0003 U 1 2` | key 3 `(1,2)` の producer=T1。line 10 と組み wr `T1→T2` |
| `trace_0.log:8` | `E 1` | T1 frame を正常終了。辺なし |
| `trace_0.log:9` | `C 2 0 1 3 1 1` | T2、commit `(1,3)`、R=1/W=1。辺なし |
| `trace_0.log:10` | `R 2 …0003 1 2` | producer=T1 なので wr `T1→T2`。後続版なし |
| `trace_0.log:11` | `W 2 …0004 U 1 3` | key 4 `(1,3)` の producer=T2。`trace_1.log:3` と組み wr `T2→T3` |
| `trace_0.log:12` | `E 2` | T2 frame を正常終了。辺なし |
| `trace_1.log:1` | `C 3 1 1 4 2 0` | T3、commit `(1,4)`、R=2/W=0。辺なし |
| `trace_1.log:2` | `R 3 …0001 1 0` | genesis は producer 不在でも orphan にならない。直後版が T0 の `(1,1)` なので rw `T3→T0` |
| `trace_1.log:3` | `R 3 …0004 1 3` | producer=T2 なので wr `T2→T3`。後続版なし |
| `trace_1.log:4` | `E 3` | T3 frame を正常終了。辺なし |

各 key の real version は1個だけなので、[dsg.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:107)–[dsg.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:114) の ww 辺は0本である。したがって隣接関係は正確に `{0:{1}, 1:{2}, 2:{3}, 3:{0}}` となる。

非自明 SCC は `{0,1,2,3}` の1個だけ（[dsg.py:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:122)–[dsg.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:172)）。そこに chord がないため、[dsg.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:174)–[dsg.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:196) の BFS が返せる巡回は `[0,1,2,3]` だけであり、長さ2・3の巡回は存在しない。

## Integrity の全 counter

対象 counter と `clean()` の条件は [model.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/model.py:139)–[model.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/model.py:174)。

| counter | 0 になる根拠と収集箇所 |
|---|---|
| `orphan_reads` | key 2/3/4 の実版には producer が存在する。key 1 の producer 不在 read は `rv == GENESIS` なので増加分岐へ入らない（[dsg.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:92)–[dsg.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:97)） |
| `version_dups` | `(key, commit)` は4 keyすべて一意。T0の2 write は key が異なる（[dsg.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:61)–[dsg.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:70)） |
| `dup_txids` | `C` は txid 0,1,2,3 が各1回だけ。重複収集は [parse.py:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:267)–[parse.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:272)、core 配線は [core.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:43) |
| `genesis_commits` | 全 commit が `(1,1)` 以上で、`<= GENESIS` 分岐へ入らない（[dsg.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:51)–[dsg.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:60)） |
| `missing_txids` | 全ファイルを束ねた集合が密な `0..3`。`expected=4`、`len(txns)=4`（[parse.py:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:401)–[parse.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:431)、[core.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:47)） |
| `write_version_mismatch` | 全 W の版が対応する C の commit と一致（[parse.py:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:288)–[parse.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:298)、[core.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:53)） |
| `malformed_keys` | 全 key が小文字・偶数長 hex。[parse.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:180)–[parse.py:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:184) が R/W の各行から呼ばれる |
| `framing_violations` | 各 C の宣言件数と実 R/W 数が一致し、各 frame に E が1個ある。件数照合は [parse.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:187)–[parse.py:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:215)、正常 close は [parse.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:319)–[parse.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:346) |
| `lock_coverage_violations` | X 行なし。収集箇所は [parse.py:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:299)–[parse.py:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:309) |
| `write_intent_violations` | I 行なし。収集箇所は [parse.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:310)–[parse.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:318) |
| `permutation_violations` | P 行なし。収集箇所は [parse.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:347)–[parse.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:357) |

`_verify()` は `expected_commits` を渡さないため、optional witness の `expected_commits` / `observed_commits` はともに `None` で clean 条件を満たす（[test_verifier.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:37)、[core.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:22)–[core.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:42)）。

結果として `integrity.clean() == True`。それでも cycle があるため、[model.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/model.py:218)–[model.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/model.py:227) により `verdict="non-serializable"`、`certified=False` となる。

## test_verifier.py の変更位置

現行 [test_verifier.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:123)、赤 fixture 群の末尾かつ integrity 節の直前へ次を追加する。既存 import の `RW` / `WR` は [test_verifier.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:23)–[test_verifier.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:25) に既にある。

```python
def test_dense_cycle4_clean_g2():
    res = _verify("r9_dense_cycle4")
    assert res.integrity.clean(), res.integrity.notes
    assert res.certified is False
    assert not res.serializable
    assert res.verdict == "non-serializable"
    assert (
        res.n_txns, res.n_reads, res.n_writes, res.n_keys, res.n_edges,
    ) == (4, 4, 4, 4, 4)
    assert res.total_cycles == 1
    assert len(res.anomalies) == 1

    a = res.anomalies[0]
    assert a.phenomenon == "G2"
    assert set(a.cycle) == {0, 1, 2, 3}
    assert a.length == 4
    assert all(anomaly.length > 3 for anomaly in res.anomalies)
    edge_types = {
        (edge.src, edge.dst): set(edge.types)
        for edge in a.edges
    }
    assert edge_types == {
        (0, 1): {WR},
        (1, 2): {WR},
        (2, 3): {WR},
        (3, 0): {RW},
    }
```

`_V2_FIXTURE_FILES` は現行 [test_verifier.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:254) の閉じ括弧直前、r8 の4行の後へ辞書順で追加する。

```python
    "r9_dense_cycle4/trace_0.log",
    "r9_dense_cycle4/trace_1.log",
```

これにより既存 [test_all_v2_fixture_files_have_clean_framing](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:257) が在庫の完全一致と両ファイルの framing を既存書式のまま検査する。

## README の変更位置

現行 [fixtures/README.md:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/README.md:30)、r8 行の直後へ次の表行を追加する。

```markdown
| `r9_dense_cycle4` | **non-serializable / G2** | 手製・密な txid 0..3・clean。2 thread、wr 3 本 + rw 1 本で長さ 4 の単一 cycle |
```

現行 [fixtures/README.md:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/README.md:179) だけを次へ置換する。

```markdown
- **長さ 4 以上の巡回を無視する (`g6` / `r8` の対は通すが、新しい `r9_dense_cycle4` がこの穴を担う)**
```

「規模で買えない限界」の実 prefix に関する記録や r5/D799 の射程には触れない。

## 負例が恒真にならない根拠

単純に「長さ4以上の SCC を無条件に落とす」変異では、新テストだけの赤にはならない。既存 r5 テストも [test_verifier.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:119)–[test_verifier.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:121) の `assert not res.serializable` で赤になる。r5 が `indeterminate` に留まることと、既存 node が通ることは別である。

「新テストだけが赤」の帰属確認には、段6で次の挙動変異を使う。

- [dsg.py:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:252)–[dsg.py:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:275) に対し、**integrity が clean な入力に限って、最短巡回長が4以上の SCC を報告・total の双方から落とす**変異を当てる。
- r9 は clean かつ最短長4なので `total=0` となり、[core.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:147)–[core.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:157) で `serializable=True`、さらに `certified=True` へ誤遷移し、新テストが赤になる。
- r5 は `missing_txids=46` で unclean のため変異条件外となり、既存テストは変化しない。
- その他の既存 clean fixture の最長巡回は3、r8も長さ `3,3,2,2` なので条件外である。

これは hypothetical mutation による生死確認であり、deliverable として production を変更する提案ではない。

## (P1-1)〜(P1-5) の判断

- **(P1-1) 支持:** `r9_dense_cycle4` は赤 fixture の連番・内容とも一致する。
- **(P1-2) 支持:** genesis read は [dsg.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:92)–[dsg.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:105) の「producer 不在かつ `rv == GENESIS` なら orphan にせず、real version の直後版へ rw」を直接使う。実版 producer P を置く案は5 txn化し、P→T3 の wr と P→T0 の ww が2本増える。P に入る辺を作らなければ巡回長は4のままだが、fixture が不要に大きくなる。
- **(P1-3) 別案:** 1 file を退け、2 file にする。T0/T1/T2 は thread 0 で逐次、長時間生存する T3 は thread 1 とする。4 file までは不要。
- **(P1-4) 支持:** README 表へ r9 を足し、現行179行の未被覆記述だけを r9 名指しへ直す。r5・D799・T-2177には触れない。
- **(P1-5) 支持:** 長さ4は未被覆穴を塞ぐ最小長であり、5以上に増やす理由がない。

## 実装子が触ってよい path

- [trace_0.log](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/r9_dense_cycle4/trace_0.log)
- [trace_1.log](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/r9_dense_cycle4/trace_1.log)
- [test_verifier.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py)
- [fixtures/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/README.md)

`orchestrator/verifier/` の production 変更は不要であり、実装子の編集対象に含めない。

## 静的検査と実測境界

trace schema、辺生成、SCC、integrity 配線、verdict/certified の各経路は静的に照合済みである。read-only sandbox のため pytest その他のテストは実走しておらず、緑とは報告しない。実装後の実測と mutation KILLED の確認は親が行う。

## 総括

production 変更なしで、clean な長さ4 G2負例を追加できる。  
realizability のため1 file案を2 thread・2 file案へ修正する。  
DSG は wr 3本＋rw 1本の4-edge ringだけで、短い巡回を持たない。  
新テスト固有の生死確認には「clean な長周期だけを落とす」変異を使う。