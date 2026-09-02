## 所見 1 — 現 trace は realizable だが、新テストは realizability を固定しない

- **所見:** 提案された trace 自体は物理的に整合する。一方、提案テストは同じ DSG を作る非 realizable な内容でも通るため、fixture の将来改変に対する realizability の保証になっていない。
- **根拠:** 新テストは統計・巡回・辺型だけを検査する（[s2-plan.md:104](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:104>)、[s2-plan.md:118](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:118>)）。parser は `thid` と filename の対応や wr 辺の commit 順を検査せず（[parse.py:273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:273)）、DSG も producer がいれば commit 順に関係なく wr を張る（[dsg.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:92)）。
- **失敗する具体例:** T0/T1/T2/T3 の commit を順に `(1,4),(1,3),(1,2),(1,1)` とし、W と対応する R の版も合わせて変更すると、T1・T2・T3 は未来に commit する producer の版を読んだ非物理 trace になる。それでも辺は同じ `0→1→2→3→0`、integrity は clean、統計・G2・length・edge-types も提案 assert と完全一致する。また、T3 frame を `trace_0.log` へ移し `trace_1.log` を空にしても全 assert が通るが、実 emitter は `thid=1` を `trace_0.log` へ書かない。
- **提案:** production は変えず、新テスト内で fixture 固有に、txid 0..3 の `(thid, commit)` が `[(0,(1,1)),(0,(1,2)),(0,(1,3)),(1,(1,4))]` であることと、T3 frame が `trace_1.log` にあることを検査する。

## 所見 2 — 「全 counter」の列挙から `abort_reasons` が漏れている

- **所見:** Integrity の全フィールドは列挙されているが、`parse.py` が数える全 counter という軸では `ParseIssues.abort_reasons` が漏れている。
- **根拠:** `abort_reasons` は [parse.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:172) で定義され、A 行ごとに加算される（[parse.py:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:360)）。`VerifyResult` にも配線される（[core.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:158)）。段2の表はこれを含まない（[s2-plan.md:70](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:70>)）。
- **失敗する具体例:** `trace_0.log` 冒頭へ `A lock-conflict` を追加しても、integrity、統計5値、辺、巡回、verdict の提案 assert はすべて通る一方、出力は `abort_reasons={"lock-conflict": 1}` となる。「parse/dsg が数える全 counter がゼロ」という説明だけが偽になる。
- **提案:** `abort_reasons` は integrity 非関与であることを明記したうえで、fixture 固有 assert として `assert res.abort_reasons == {}` を加える。

## 所見 3 — monkeypatch 実測は source 変異の一意帰属をまだ証明していない

- **所見:** 親の monkeypatch は生死を示すが、「新テストだけが変異を KILL する」ことは示していない。段2は clean 条件を足してこの問題を正しく認識しているものの、その条件付き source 変異は未実測である。
- **根拠:** 親 probe では r5 が `indeterminate` へ変わった（[brief.md:28](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/brief.md:28>)）。これは `serializable=True` への変化なので、既存 [test_verifier.py:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:120) も赤になる。段2もこの先行 kill を認め（[s2-plan.md:151](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:151>)）、別の「clean 入力限定」変異へ切り替えている（[s2-plan.md:157](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:157>)）。
- **失敗する具体例:** `dsg.py` で長さ4以上の SCC を無条件に `sccs` と `total` から除けば、新テストに加えて r5 の既存テストも落ち、新テストの純増寄与は0になる。monkeypatch で観測済みの挙動はこちらであり、段2が予定する clean 条件付き source 変異とは同一でない。
- **提案:** 段6では clean 条件付きの exact source replacement を使い、失敗 node が `test_dense_cycle4_clean_g2` だけであることを確認する。主たる kill assert は [s2-plan.md:100](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:100>) の `assert res.certified is False`。

## 所見 4 — D799 から「手製以外の経路がない」までは一般化できない

- **所見:** D799 が測ったのは固定 source trace の prefix 閾値系列であり、別の実行・スケジュールでも長さ4が出ないことまでは測っていない。
- **根拠:** D799 の実測範囲は `tid <= 1000` までの prefix である（[d1455.md:10](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/refs/d1455.md:10>)、[d799.md:33](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/refs/d799.md:33>)）。親の18 fixture censusも「現在追跡している在庫」に限られる。
- **失敗する具体例:** 段2のスケジュール自身が、read-set 再検証を抜いた CC なら実 emitter から出力可能な4-cycleである。stock Silo は stale な key 1 を [transaction.cc:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/external/ccbench/cc/silo/transaction.cc:453) で abort するが、既存 broken patch はその abort を省く（[broken-silo-norw-validation.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/patches/broken-silo-norw-validation.patch:9)）。したがって別走行で実 trace が得られる可能性を D799 は排除しない。
- **提案:** この wave の結論は「現在の18 fixtureと測定済み prefix 系列には clean な長さ4 witness がない」に限定する。D799/D1455本文の射程訂正は指定どおり T-2177 の scope であり、本 wave では触れない。

## DSG の静的再導出

提案 trace そのものの辺は正しい。

| key | 規則 | 生じる辺 |
|---|---|---|
| key 1 | T3 が genesis `(1,0)` を読み、唯一の実版 `(1,1)` の producer が T0 | rw `T3→T0` |
| key 2 | T1 が T0 の `(1,1)` を読む。後続版なし | wr `T0→T1` |
| key 3 | T2 が T1 の `(1,2)` を読む。後続版なし | wr `T1→T2` |
| key 4 | T3 が T2 の `(1,3)` を読む。後続版なし | wr `T2→T3` |

各 key の実版は1個なので [dsg.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:107) の ww は0本。隣接関係は正確に `{0:{1},1:{2},2:{3},3:{0}}` で、chord はない。

SCC は `{0,1,2,3}` の1個。`_shortest_cycle` は `s=min(scc)=0` から始まり（[dsg.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:177)）、各節点の SCC 内隣接が1個だけなので `0→1→2→3→0` 以外を返せない。報告 `length` は4で、長さ2・3の巡回は存在しない。

## Integrity の静的再導出

| counter | 提案 trace の値 | 根拠 |
|---|---:|---|
| `orphan_reads` | 0 | 実版read 3件に producerあり。key 1 は genesis なので免除 |
| `version_dups` | 0 | 各 `(key,version)` が一意 |
| `dup_txids` | 0 | C の txid は0,1,2,3各1回 |
| `genesis_commits` | 0 | commit は `(1,1)`〜`(1,4)` |
| `missing_txids` | 0 | `max(txid)+1 == len(txns) == 4` |
| `write_version_mismatch` | 0 | 全W版が対応Cのcommitと一致 |
| `malformed_keys` | 0 | 全keyが小文字・偶数長hex |
| `framing_violations` | 0 | 宣言R/W件数が実数と一致し、全frameにEあり |
| `lock_coverage_violations` | 0 | X行なし |
| `write_intent_violations` | 0 | I行なし |
| `permutation_violations` | 0 | P行なし |
| commit witness | clean | `_verify` は witness を渡さず両側 `None` |
| `abort_reasons` | `{}` | A行なし。integrity外の集計counter |

したがって提案 trace の `integrity.clean()` は真である。見落としによって `indeterminate` になる経路は見つからない。

## 物理的整合の判定

提案された実行順は成立する。T3 が key 1 の genesis を先に読み、thread 0 が T0→T1→T2 を逐次 commit、T3 が最後に key 4 の T2版を読んで commitすれば、wr 3本はcommit順方向、rw `T3→T0`だけが逆走する。

stock SiloならT3は stale key 1 の再検証でabortするが、負例が表すべき壊れたCCではそのabortを抜け、実 emitter の [transaction.cc:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/external/ccbench/cc/silo/transaction.cc:601) 以下から同形式を出力できる。したがって提案 trace 自体は README の構造的事実に反しない。production変更は不要である。

## 反実仮想と変異帰属

段2の clean 条件付き変異については、新テストの純増寄与がある。

- 新テストを削除すると、在庫テストは r9 を verify しても framing しか assert しない（[test_verifier.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:257)）。したがって変異は生き残る。
- r5 は unclean なので変異条件外。既存のcleanな赤fixtureは報告最短長が2または3で条件外。緑fixtureにはSCCがない。
- 新テストありでは r9 が `serializable=True / certified=True` へ誤遷移し、最初に `assert res.certified is False` が落ちる。
- `all(anomaly.length > 3 ...)` 単独は空リストに対して恒真だが、直前の `total_cycles == 1` と `len(res.anomalies) == 1` が空を拒むため、全体として恒真ではない。
- assert は certified、verdict、長さ、正確な4辺を見ており、件数・dirname・hashだけに依存していない。

## 総括

重い所見は次の3件である。

1. monkeypatch 実測は無条件変異で既存r5テストにも殺されるため、clean条件付きsource変異の一意帰属は段6で未確認。
2. 提案trace自体はrealizableだが、新テストはcommit順・thread/file対応を固定せず、同じ出力を持つ非物理fixtureも通す。
3. D799が排除したのは測定済みprefix系列だけで、「手製以外の経路がない」までは一般化できない。

DSGは正確な4-edge ring、最短巡回長4、integrityは全clean条件を満たす。pytestその他は実走しておらず、緑とは判定していない。