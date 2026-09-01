## 前提と harness 契約

静的検査のみで確定した。pytest・書き込みは実施していない。

`tools/mutation_harness.py::_require_exact_keys` の exact key は指定どおりである。

- root: `schema`, `estimated_run_seconds`, `timeout_seconds`, `hang_timeout_seconds`, `mutations`
- mutation: `id`, `category`, `replacements`, `expected_nodes`, `expected_status`, `hang_risk`
- replacement: `file`, `old`, `new`
- `schema`: `izanagi-dev-wave-mutation-spec/v1`
- `category`: `negative | positive | both-layers`
- 全変異とも `hang_risk: false`

以下の全 `old` は `str.count(old) == 1` 相当で対象 file 内の一意性を確認済みである。

## M1 — `_classify` を常に G2 にする

対象: `orchestrator/verifier/dsg.py:245-250`

`old`:

```python
        all_types = {t for e in edges for t in e.types}
        if RW in all_types:
            return "G2"
        if WR in all_types:
            return "G1c"
        return "G0"
```

`new`:

```python
        return "G2"
```

観察: 上記 6 行の出現数は 1。

事前期待:

- `category: negative`
- `expected_status: KILLED`
- `expected_nodes`:

```text
orchestrator/tests/test_verifier.py::test_classify_branches
```

単一理由性は成立する。node は合成 `CycleEdge` を直接 `_classify` に渡し、別の parser・DSG・integrity gate は通らない。

ただしこれは semantic kill ではない。`core.py:149` の受理判定は `total == 0`、`VerifyResult.verdict` も `serializable` と integrity だけを見る。分類結果は診断 payload にしか効かない。したがって機械的には KILLED だが、DW-M03 上は「diagnostic sensitivity pin」であり、M1 の SURVIVED を正しさゲートの穴と数えてはいけない。

## M2 — epoch を無視した tid-only 版順序

採用対象: `orchestrator/verifier/dsg.py:72,101,211,226` の 4 replacement。

置換 1:

```python
            self.versions[k] = sorted(set(vs))
```

を

```python
            self.versions[k] = sorted(
                set(vs), key=lambda version: version[1])
```

へ置換する。

置換 2:

```python
                    idx = bisect_right(vs, rv)
```

を

```python
                    idx = bisect_right(
                        vs, rv[1], key=lambda version: version[1])
```

へ置換する。

置換 3:

```python
            iu = bisect_left(vs, u_writes[k])
```

を

```python
            iu = bisect_left(
                vs, u_writes[k][1], key=lambda version: version[1])
```

へ置換する。

置換 4:

```python
            idx = bisect_right(vs, r.ver)
```

を

```python
            idx = bisect_right(
                vs, r.ver[1], key=lambda version: version[1])
```

へ置換する。

4 個の `old` はそれぞれ出現数 1。

候補比較:

- 構築側だけを `sorted(set(vs), key=tid)` にする案は不採用。後続 `bisect_left/right` が辞書式 tuple 比較のままなので、bisect の「同じ順序で sort 済み」という前提を破る。r6/r7 が赤になっても、原因は tid-only ではなく不整合な binary search に混ざる。
- bisect 側だけを tid-only にする案は rw successor だけを変え、ww 版順は epoch-aware のまま残る。その射程なら `r7_epoch_rw_successor` だけが対象で、`r6_epoch_version_order` は残る。
- 推奨は上記 4-anchor。版列、acceptance 側 rw、診断再構成側 ww/rw を同じ tid-only 順序へ揃え、M2 の名前どおり verifier 全体の版比較を落とす。

事前期待:

- `category: negative`
- `expected_status: KILLED`
- `expected_nodes`:

```text
orchestrator/tests/test_verifier.py::test_epoch_version_order_g2
orchestrator/tests/test_verifier.py::test_epoch_rw_successor_order_g2
```

静的な fixture 再導出でも、変化する tracked fixture はこの 2 件だけで、双方とも cycle が消える。

単一理由性は成立する。両 node は `integrity.clean()` を明示確認しており、別 integrity gate による拒否はない。赤理由は「epoch を捨てた版順序により G2 cycle が消えて serializable へ広がった」に絞れる。

## M3 — 長さ 4 以上の最短 witness を無視する

対象: `orchestrator/verifier/dsg.py:255`

`old`:

```python
        sccs = self._sccs()
```

`new`:

```python
        sccs = [
            comp for comp in self._sccs()
            if len(self._shortest_cycle(set(comp))) < 4
        ]
```

観察: `old` の出現数は 1。

事前期待:

- `category: negative`
- `expected_status: SURVIVED`
- `expected_nodes: []`

現在の `total_cycles` は simple cycle 数ではなく非自明 SCC 数である。このため、正確な変異の意味は「選ばれる最短 witness が 4 以上の SCC を total から外す」となる。短い cycle と長い cycle を同じ SCC が含む場合、長い方だけを個別に無視する表現力は現行実装にない。

全 tracked 赤 fixture の shortest witness は長さ 2 または 3 なので、定義上既存 suite はこの変異を殺せない。仮想の clean な長さ 4 fixture では別拒否層はなく、受理集合が fail-open に広がるため単一理由性は成立する。

## M4 — framing violation count を常に 0 にする

対象: `orchestrator/verifier/core.py:65`

`old`:

```python
    dsg.integrity.framing_violations = len(issues.framing_violations)
```

`new`:

```python
    dsg.integrity.framing_violations = 0
```

観察: `old` の出現数は 1。

事前期待:

- `category: negative`
- `expected_status: KILLED`
- `expected_nodes`:

```text
orchestrator/tests/test_verifier.py::test_declared_read_and_write_counts_must_match
orchestrator/tests/test_verifier.py::test_missing_end_is_indeterminate
orchestrator/tests/test_verifier.py::test_duplicate_end_is_indeterminate
orchestrator/tests/test_verifier.py::test_new_commit_before_end_records_missing_end
orchestrator/tests/test_verifier.py::test_cycle_verdict_takes_priority_over_framing_violation
orchestrator/tests/test_verifier.py::test_characterization_txn_tail_loss_is_indeterminate
```

`issues.framing_violations`、details、notes は残るが、`Integrity.clean()` が見るのは数値フィールドである。この 1 行を 0 にすると framing-only 入力は `indeterminate` から `serializable/certified` へ広がる。他の拒否層はない。

`test_cycle_verdict_takes_priority_over_framing_violation` は cycle 自体でも拒否されるため、その node の赤は counter 診断だけで semantic kill ではない。残る framing-only 5 node は受理結果も変わるので DW-M03 の semantic kill を満たす。

## M5 — g6 fixture の bytes hash で期待値を即返す

対象: `orchestrator/verifier/core.py:26-27`

`old`:

```python
    """1 run (= 1 trace ディレクトリ) を検証する。"""
    txns, issues = parse_trace_dir(trace_dir)
```

`new`:

```python
    """1 run (= 1 trace ディレクトリ) を検証する。"""
    if os.path.isdir(trace_dir):
        digest = __import__("hashlib").sha256()
        for name in sorted(
                name for name in os.listdir(trace_dir)
                if name.startswith("trace_") and name.endswith(".log")):
            with open(os.path.join(trace_dir, name), "rb") as stream:
                digest.update(stream.read())
        if digest.hexdigest() in {
                "1dbb84734cd360e785f25ae241ab2d61ef51a4b2c55e77ea8af2a641ee511a2",
        }:
            result = VerifyResult(
                trace_dir=trace_dir,
                serializable=True,
                n_txns=200,
                n_reads=924,
                n_writes=460,
                n_keys=131,
                n_edges=931,
            )
            if expected_commits is not None:
                result.integrity.expected_commits = expected_commits
                result.integrity.observed_commits = 200
            return result
    txns, issues = parse_trace_dir(trace_dir)
```

観察: 2 行の `old` は 1 箇所のみ。hash は tracked `g6_silo_serial_1thread/trace_0.log` の現行 SHA-256 と一致する。

事前期待:

- `category: negative`
- `expected_status: SURVIVED`
- `expected_nodes: []`

この具体形は定義上 SURVIVED する。g6 に対して既存 node が読む全フィールドを現行期待値で返し、他の入力は通常経路へ落とすためである。

この生存が示すのは、fixture 集合が閉じており、「同じ意味だが未知 bytes」の metamorphic input が無いことである。一般的な事故退行の穴というより、既知 fixture だけを特別扱いする overfitting を repo 内 suite が排除できないという D387 型の限界である。

より強い代案は g6/r8 双方の完全な `VerifyResult` を hash map に埋め込む形だが、巨大な anomaly object の hard-code になるだけで情報量は増えない。上の singleton 既知集合で同じ限界を最小に実証できる。

## P1 — rw anti-dependency を落とす正例対照

対象: `orchestrator/verifier/dsg.py:105`

`old`:

```python
                            self._add(tid, w_tx)
```

`new`:

```python
                            pass
```

観察: `old` の出現数は 1。

事前期待:

- `category: positive`
- `expected_status: KILLED`
- `expected_nodes`:

```text
orchestrator/tests/test_verifier.py::test_g4_has_rw_edge_but_no_cycle
orchestrator/tests/test_verifier.py::test_write_skew_g2
orchestrator/tests/test_verifier.py::test_total_cycles_survives_witness_cap
orchestrator/tests/test_verifier.py::test_lost_update_g2
orchestrator/tests/test_verifier.py::test_cycle3_g2
orchestrator/tests/test_verifier.py::test_mixed_cycle_g2_all_three_edge_types
orchestrator/tests/test_verifier.py::test_nonlatest_read_caught_via_ww_transitivity
orchestrator/tests/test_verifier.py::test_cycle_verdict_takes_priority_over_framing_violation
orchestrator/tests/test_verifier.py::test_structured_report_has_edge_detail
orchestrator/tests/test_verifier.py::test_silo_serial_1thread_fixture_contract
orchestrator/tests/test_verifier.py::test_broken_silo_norw_fixture_contract
orchestrator/tests/test_verifier.py::test_broken_silo_norw_structured_report_is_exact
orchestrator/tests/test_verifier.py::test_epoch_version_order_g2
orchestrator/tests/test_verifier.py::test_epoch_rw_successor_order_g2
orchestrator/tests/test_verifier.py::test_real_silo_edge_type_combinations_are_exact
orchestrator/tests/test_verifier.py::test_real_silo_serializable
orchestrator/tests/test_t1286_commit_receipt.py::test_uncertified_verifier_capability_cannot_issue_receipt[r1_write_skew]
orchestrator/tests/test_t1286_commit_receipt.py::test_uncertified_verifier_capability_cannot_issue_receipt[r2_lost_update]
```

静的な fixture 再導出結果:

- `r8_silo_broken_norw`: edges `1509 → 1022`、cyclic `True → False`
- raw witness `{T3,T7}` の `T3→T7` は wr だが、逆向き `T7→T3` は rw のみなので確実に閉路が消える。
- `test_broken_silo_norw_fixture_contract` は最初の `assert not res.serializable` で落ちる。
- t1286 の 2 parameter node は、本来 uncertified である r1/r2 が certified になり receipt 発行可能側へ倒れるため落ちる。

DW-M03 の semantic kill を直接担うのは赤 fixture、r6/r7、t1286 の node 群である。以下は補助的な golden/diagnostic 赤である。

- `test_g4_has_rw_edge_but_no_cycle`: edge count だけ
- `test_silo_serial_1thread_fixture_contract`: acceptance は緑のまま、`n_edges` golden
- `test_broken_silo_norw_structured_report_is_exact`: verifier-derived report golden
- `test_real_silo_edge_type_combinations_are_exact`: edge-type golden
- `test_real_silo_serializable`: acceptance は緑のまま、`n_edges` golden

r8 は integrity clean で、閉路以外の拒否層がないため正例対照として単一理由性を満たす。

## E1 — 等価変異

対象: `orchestrator/verifier/dsg.py:78`

`old`:

```python
        if u != v:                       # 自己ループ (RMW で自分が直後版を書く等) は辺にしない
```

`new`:

```python
        if not (u == v):                 # 自己ループ (RMW で自分が直後版を書く等) は辺にしない
```

観察: `old` の出現数は 1。

`u` と `v` は parser/DSG 内部の `int` txid なので、受理集合、adjacency、生成物はすべて同一である。

- `category: positive`
- `expected_status: SURVIVED`
- `expected_nodes: []`

これは harness が注入実在を記録しながら `SURVIVED` を報告できることの正例になる。

## test file の参照閉包

「transitive import 全体」を採ると、campaign の大半が verifier receipt module へ到達し、静的 import graphだけで 100 file 超になる。それは behavioral 分母ではない。実際に対象 `core.py/dsg.py` を入力へ適用する producer closure は次の 5 file である。

```text
orchestrator/tests/test_verifier.py
orchestrator/tests/test_t1286_commit_receipt.py
orchestrator/tests/test_campaign.py
orchestrator/tests/test_s1_direct_comparison.py
orchestrator/tests/test_silo_ladder_rung1_driver.py
```

根拠:

- `test_verifier.py`: 直接 `verify_trace_dir`/`DSG` を実行
- `test_t1286_commit_receipt.py`: r1/r2/g1 を `verify_trace_dir_with_capability` へ投入
- `test_campaign.py`: pipeline の実 verifier entrypoint を g1/r1 および動的 trace に通す
- `test_s1_direct_comparison.py`: pipeline の実 entrypoint を g1 に通す
- `test_silo_ladder_rung1_driver.py`: `validate_raw_bundle` が raw trace を再検証

直接 import はするが、今回の 5 source の挙動を実行しない file は以下。

```text
orchestrator/tests/test_critic.py
orchestrator/tests/test_p3_b4_launcher.py
orchestrator/tests/test_t1416_backoff_compiler_binding.py
```

保存済み・手製の verifier JSON を consumer として検査するだけで、source 変異では結果が変わらない file は以下。

```text
orchestrator/tests/test_mocc_g2_discriminator.py
orchestrator/tests/test_mocc_g2_repro_ledger.py
orchestrator/tests/test_mocc_trace_pair.py
orchestrator/tests/test_silo_ladder_rung1_evidence.py
orchestrator/tests/test_t152_write_intent_coverage.py
```

上記 7 変異で実際に赤くなりうる file は、静的には次の 2 file だけである。

```text
orchestrator/tests/test_verifier.py
orchestrator/tests/test_t1286_commit_receipt.py   # P1 の parameterized 2 node のみ
```

`test_campaign.py` の r1 経路は real capability を作った後に `_red_vr()` で結果を置換するため P1 を mask する。M4 が触る tail-loss 入力も commit witness mismatch で別途拒否される。S1 は g1、ladder fixture は conflict のない blind write 4 件なので今回の変異に追加検出力を持たない。

## contract-loader drift 群

`CONTRACT_LOADER_RELATIVE_PATHS` に対象 source が含まれること自体は確認できる。しかし「import した全 test が赤になる」は誤りである。drift は次の関数が live disk と HEAD blob を比較した場合にだけ発火する。

- `capture_contract_loader_binding()`
- `verify_live_contract_loader_binding()`

単なる verifier import、`verify_trace_dir()`、`test_verifier.py` はこの層を通らない。

推奨分母では contract-loader drift node は exact に空集合である。したがって `--deselect` は不要で、最初から次を正選択するのがよい。

```text
orchestrator/tests/test_verifier.py
orchestrator/tests/test_t1286_commit_receipt.py::test_uncertified_verifier_capability_cannot_issue_receipt
```

関数 node の指定で r1/r2 の 2 parameter instance がとも収集される。これなら identity pin の赤を semantic kill に混ぜず、P1 の downstream fail-closed も保持できる。

親の広い file 集合を一度選んで大量の `--deselect` を並べる方法は推奨しない。特に `test_campaign.py` や S1 系では live-binding 呼出しが helper 経由にも広がるため、関数名の静的リストは変更に弱い。正選択なら同一性層の node は 0 件であり、意味層だけが分母になる。

## 推奨分母

推奨は「verifier の全単体 node + verifier capability の赤 fixture node」である。

```text
orchestrator/tests/test_verifier.py
orchestrator/tests/test_t1286_commit_receipt.py::test_uncertified_verifier_capability_cannot_issue_receipt
```

理由:

- 狭すぎる fixture 対だけでなく、parser、integrity、DSG、report、実 emitter fixture を全て含む。
- P1 が「verdict を緑にした結果、receipt を発行可能にする」downstream fail-open まで検査する。
- hand-made verifier JSON consumer は source 変異へ反応しないので分母へ足しても検出力は増えない。
- contract-loader identity red を behavioral kill と誤認しない。
- M3/M5/E1 の SURVIVED を、不要な同一性層で全件 KILLED に見せない。

したがって「既存テストの検出力」という主張は、この exact node 集合に限定して行うのが最も誠実である。

## kill 意味論

| 変異 | harness の機械結果期待 | DW-M03 分類 |
|---|---|---|
| M1 | KILLED | 診断分類だけ。semantic kill ではない |
| M2 | KILLED | r6/r7 が non-serializable から serializable。semantic kill |
| M3 | SURVIVED | clean な長さ 4 witness の受理拡大を未検出。実際の coverage hole |
| M4 | KILLED | framing-only 入力が indeterminate から certified。semantic kill。ただし cycle併存 node は診断赤 |
| M5 | SURVIVED | 既知 hash overfitting。閉じた fixture 集合/D387 限界 |
| P1 | KILLED | rw 消失で赤 fixture が certified 側へ倒る。semantic positive control |
| E1 | SURVIVED | 完全な等価変異 |

D799 決定 (4) の raw bytes 分離は現在も成立している。

```text
test_new_real_fixture_bytes_are_exact
test_real_silo_fixture_bytes_are_exact
```

両 node は fixture file 自体だけを読み、`core.py/dsg.py` の 7 変異では落ちない。したがって bytes SHA が semantic node を先に覆い隠す変異は今回の 7 件にはない。

一方、次は raw bytes node ではなく verifier-derived golden であり、P1 では補助赤になる。

```text
test_broken_silo_norw_structured_report_is_exact
test_real_silo_edge_type_combinations_are_exact
test_silo_serial_1thread_fixture_contract
test_real_silo_serializable
```

P1 には独立した semantic node があるので golden 赤に依存せず KILLED と判定できる。M1 は診断 node しかないため semantic kill に昇格させてはいけない。

## 親 brief の修正点

(P1-A): 「11 file + mocc 系」の広い分母は採らない。多くは型 import、保存 JSON consumer、identity pin であり、今回の source 変異の behavioral detection ではない。推奨分母は上記 2 node selector。

(P1-B): 正しい。hash branch を現行 fixture hash と期待値に合わせて書く限り M5 は定義上 SURVIVED する。意味は「既知 bytes に対する overfitting を拒否する未知・metamorphic 入力がない」であり、一般 verifier の正しさを測る変異としては低情報量である。

(P1-C): raw bytes node の分離は維持されている。ただし structured report・edge count・stats の golden node は別に残り、P1 で補助赤を出す。kill 台帳では semantic node と golden-only node を分ける必要がある。

(P1-D): brief の疑いが正しい。`_classify` は verdict/certified に効かない。M1 の生存は穴ではなく設計どおりであり、実際には `test_classify_branches` が診断文字列を殺すだけである。

F-new1: 「pin に載るため全変異が数百件の drift 赤を引く」は誤り。pin は live-binding consumer が呼ばれた時だけ発火し、推奨分母では該当 node は 0。過去の `pipeline.py` 384 件を verifier source へ一般化できない。

F-new2: M2 KILLED、M3 SURVIVED の予測は妥当。M1 は機械的 KILLED でも semantic kill ではない。M4 は未知ではなく既存 framing node により KILLED と静的確定できる。M5 は上記の具体形なら必ず SURVIVED。

F-new3: 「唯一の穴」を複数形へ直す点は正しい。ただし semantic hole の候補数へ M1 を含めて最大 5 とするのは不正確で、M1 は受理集合を変えない。M5 も事故退行の穴というより fixture overfitting/D387 control と別記すべきである。

## 総括

(a) 7 変異はすべて exact `old/new` と一意 anchor を確定できる。期待は M1/M2/M4/P1 が機械的 KILLED、M3/M5/E1 が SURVIVED。ただし M1 は semantic kill ではない。

(b) 推奨分母は `test_verifier.py` 全体と t1286 の `test_uncertified_verifier_capability_cannot_issue_receipt` のみ。contract-loader drift node はこの分母では 0 件。

(c) brief は F-new1 の「全変異が数百 drift 赤」、F-new2 の M1 semantic 解釈と M4 未知、P1-D の「M1 生存＝穴」を修正すべきである。