## 所見

must-fix、nit ともに所見なし。commit `dd43f92e2` は段4裁定の確定プランに一致し、静的に確認した範囲で負例の恒真化・意図しない辺・integrity 不良はない。

## 裁定との照合

| 確定プラン | 判定 | 照合結果 |
|---|---|---|
| 1. README は表へ1行だけ追加 | 一致 | r8 直後へ r9 行だけ追加されている（[README.md:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/README.md:30)）。親版179行の文面は変更されず、表の挿入で現行180行へ移動しただけ（[README.md:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/README.md:180)）。 |
| 2. `abort_reasons == {}` | 一致 | [test_verifier.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:127) に存在する。 |
| 3. realizability の4組 pin | 一致 | `(txid, thid, commit)` が裁定どおり固定されている（[test_verifier.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:137)）。 |
| 4. `all(anomaly.length > 3 ...)` を落とす | 一致 | 対象 assert は commit に存在しない。長さ自体は `a.length == 4` で固定される（[test_verifier.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:150)）。 |
| 5. 編集4 path、production 差分0 | 一致 | 差分は README、trace 2本、`test_verifier.py` の計4 pathのみ。`orchestrator/verifier/` の差分は0。 |

段2の trace、テスト本体、在庫2行、README表行にも、段4で明示された変更以外の逸脱はない（[確定プラン:31](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/s4-ruling.md:31>)）。

## assert の実効性

| assert | 判定 |
|---|---|
| `res.integrity.clean()`（126） | 有効。trace健全性を直接固定し、後続の判定値からは導けない。 |
| `res.abort_reasons == {}`（127） | 有効。`abort_reasons` は integrity 非関与なので126から含意されない（[parse.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:172)）。 |
| `res.certified is False`（128） | 有効。consumer が使う通過判定を直接固定する。先行2 assertだけでは含意されない。M1/M2の最初の killer。 |
| `not res.serializable`（129） | 有効。`certified=False` は空入力などでも成立するため、それだけから巡回ありとは導けない。 |
| `verdict == "non-serializable"`（130） | 有効な派生API pin。現行定義では129から派生するが、`verdict` 実装の不整合を独立に検出でき、式自体は恒真ではない。 |
| 統計5値 `==(4,4,4,4,4)`（131–133） | 有効。transaction/read/write/key とグラフ全体の辺数を固定する。 |
| `total_cycles == 1`（134） | 有効。129が保証するのは非ゼロまでで、単一SCCは保証しない。 |
| `len(res.anomalies) == 1`（135） | 有効。全数と報告witnessの整合を固定し、報告欠落・余分なwitnessを検出する。 |
| `(txid, thid, commit)` 4組（138–145） | 有効。グラフ・統計だけでは固定できない物理順序を担う。裁定済みどおりfilename対応は対象外。 |
| `phenomenon == "G2"`（148） | 有効。巡回の分類を固定する。 |
| `set(a.cycle) == {0,1,2,3}`（149） | 有効。witnessの構成transactionを固定する。 |
| `a.length == 4`（150） | 有効。直前のset比較だけでは重複要素を排除できないため含意されない。 |
| `edge_types == {...}`（155–160） | 有効。4辺の向きと各辺型を正確に固定する。 |

前の assert と同じ値を言い換えるだけの恒真 assert はない。

## fixture の独立再導出

辺生成規則は、読んだ版のproducerから読み手へWR、読んだ版の直後版producerへ読み手からRW、同一keyの連続実版間にWWを張る（[dsg.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:81)、[dsg.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:107)）。

| trace行 | 独立に導かれる効果 |
|---|---|
| `trace_0:1` | T0、commit `(1,1)`、R0/W2を宣言。 |
| `trace_0:2` | key1 `(1,1)` のproducerをT0にする。後のgenesis readから `3→0` RW。 |
| `trace_0:3` | key2 `(1,1)` のproducerをT0にする。line 6から `0→1` WR。 |
| `trace_0:4` | T0を宣言数どおり正常終了。 |
| `trace_0:5` | T1、commit `(1,2)`、R1/W1を宣言。 |
| `trace_0:6` | T0版key2を読むため `0→1` WR。key2に後続実版がなくRWなし。 |
| `trace_0:7` | key3 `(1,2)` のproducerをT1にする。line 10から `1→2` WR。 |
| `trace_0:8` | T1を正常終了。 |
| `trace_0:9` | T2、commit `(1,3)`、R1/W1を宣言。 |
| `trace_0:10` | T1版key3を読むため `1→2` WR。後続実版なし。 |
| `trace_0:11` | key4 `(1,3)` のproducerをT2にする。`trace_1:3` から `2→3` WR。 |
| `trace_0:12` | T2を正常終了。 |
| `trace_1:1` | T3、thread 1、commit `(1,4)`、R2/W0を宣言。 |
| `trace_1:2` | key1 genesisを読む。orphanにはならず、直後実版producer T0へ `3→0` RW。 |
| `trace_1:3` | T2版key4を読むため `2→3` WR。後続実版なし。 |
| `trace_1:4` | T3を正常終了。 |

各keyに実版は1個しかないためWWは0。したがって隣接関係は正確に `{0:{1}, 1:{2}, 2:{3}, 3:{0}}` で、chordや追加SCCはない。非自明SCCは4頂点の1個、巡回は `0→1→2→3→0` のみで、長さ2・3の巡回は作れない。

実現可能な順序も存在する。thread 1のT3がkey1のgenesisを読み、その間にthread 0がT0、T1、T2を逐次commitし、T3が最後にT2版key4を読んでcommitできる。3本のWRはcommit順方向で、逆走するのは意図したRW `3→0` だけである。

## integrity

`Integrity.clean()` が検査する全counterは [model.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/model.py:139)–[model.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/model.py:174) に列挙される。

| counter | 静的導出値 |
|---|---:|
| `orphan_reads` | 0。実版readには全てproducerがあり、key1はgenesis。 |
| `version_dups` | 0。4個の `(key, version)` は全て一意。 |
| `dup_txids` | 0。Cのtxidは0～3が各1回。 |
| `genesis_commits` | 0。全commitが`(1,0)`より大きい。 |
| `missing_txids` | 0。txid集合が密な`0..3`。 |
| `write_version_mismatch` | 0。全W版が対応Cのcommitと一致。 |
| `malformed_keys` | 0。全keyが小文字・偶数長hex。 |
| `framing_violations` | 0。宣言数は順に0/2、1/1、1/1、2/0で実数と一致し、Eも各1個。 |
| `lock_coverage_violations` | 0。X行なし。 |
| `write_intent_violations` | 0。I行なし。 |
| `permutation_violations` | 0。P行なし。 |
| commit witness | `None/None`。`_verify` は `expected_commits` を渡さない（[test_verifier.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:37)）。 |
| `abort_reasons` | `{}`。A行なし。収集結果は [core.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:158) で結果へ渡る。 |

witnessの全辺も再構成可能で、報告上限にも掛からないため`notes`へ追加される条件もない。

## 変異への応答

| 変異 | 新テストの予測 | 既存テスト・非帰属赤 |
|---|---|---|
| M1 無条件drop | integrityとabortは不変。`total=0`、`serializable=True`、`certified=True`となり、最初に [test_verifier.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:128) が落ちる。 | r5もdropされ、既存 [test_verifier.py:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:120) が落ちる。 |
| M2 clean時だけdrop | r9はcleanなのでM1と同じく、最初は128行の`certified is False`。 | 意味挙動では新テスト以外は落ちない。r5はunclean、他の既存clean fixtureには長さ4以上の巡回がない。ただし全木を未除外で走らせれば、`CONTRACT_LOADER_RELATIVE_PATHS`のHEAD blob束縛による53件の`contract-loader-drift`が非帰属赤になり得る（[s4-ruling.md:80](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/s4-ruling.md:80>)）。 |
| M3 等価sort key | 新テストで落ちるassertはない。1 SCCしかなく、`len`と`lambda comp: len(comp)`は同じkeyを返す。 | M2と同種のsource-drift赤はあり得るが意味変化ではない。新テスト自体が落ちる経路はない。 |

これは静的予測であり、KILLED／SURVIVEDの実測結果ではない。

## 既存テストへの影響

- productionコードと既存fixtureは未変更なので、既存traceのverdict・`certified`・レポート値・downstream受理集合は変わらない。
- 在庫テストはfixture rootの全`trace_*.log`を再帰収集し、tupleと完全一致させる（[test_verifier.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:298)）。追加2 fileが辞書順で `_V2_FIXTURE_FILES` に登録されており、既存fixtureの受理条件は変えていない。
- 同在庫テストがr9へ行う既存検査はframingだけなので、M2の誤った`certified=True`を単独では殺さない。純増した新テストがその役割を持つ。
- 素のrunnerは`globals()`から全callableな`test_*`を動的収集するため、新テストも自動的に含まれる（[test_verifier.py:1980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:1980)）。runnerやallowlistの変更は不要。
- 成果物への基準時影響はない。production判定・レポート・台帳の値は不変で、テスト側だけが「cleanな長さ4巡回を誤ってcertifiedにする実装」を新たに拒否する。

## 実測境界

sandbox指定に従い、pytest、素のrunner、mutation harnessはいずれも実走していない。本回答は静的レビューであり、テストを「緑」とは判定していない。

## 総括

重い所見はない。静的には次の3点を確認した。

1. 段4確定プランの5点と編集scopeに逸脱がない。
2. fixtureは意図したWR 3本＋RW 1本だけを作り、単一の長さ4 G2と完全cleanなintegrityを構成する。
3. M1/M2では新テストの`certified is False`が最初に落ち、M3で新テストが落ちる意味経路はない。