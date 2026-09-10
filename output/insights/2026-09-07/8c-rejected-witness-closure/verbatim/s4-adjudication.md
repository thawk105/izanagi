# 段 4 裁定 — 8c formal consumer の rejected 側 producer/consumer 不整合

段 2 プラン 1 本、段 3 敵対 2 レンズをすべて受領。3 本とも `tools/check_codex_output.py` rc=0。
親は段 3 の指摘を独立に検算し、以下を裁定する。

## 方向 (P1) — 維持、ただし理由を狭める

**consumer を実在 field へ合わせる。producer に 3 field を新設しない。** 方向は維持する。

ただし親 brief の理由 1 「producer が書く boolean は必ず恒真になる」は**一般化しすぎだった**。
段 3 レンズ A が反例を出した — producer は untyped JSON へ潰れる前の `VerifyResult` を持つので、
`vr.verdict == "non-serializable" and vr.integrity.clean()` のように偽になりうる値を書ける。
この指摘は real であり採用する。理由 1 は次へ差し替える。

> producer が書く boolean は**自己申告**であり、consumer はそれを検算する独立の証拠を持たない。
> consumer 側で導けば、record が主張する `constraint_sha256` を WAL 上の実 verifier 証拠と
> 突き合わせる形になり、入力の 2 つの部分が互いを検算する。

**併せてレンズ A の警告も採用する** — 「untyped JSON の schema と導出関係を再検査しない consumer 実装は
producer 側より明確に弱い」。したがって下記 must-fix 1〜4 は方向を成立させるための必要条件であり、
仮想リスク向けの追加ではない。

## real / 採用 (must-fix)

| # | 出所 | 所見 | 裁定 |
| --- | --- | --- | --- |
| M1 | レンズ A-1 | `anomalies=[{}]` のような任意 dict が witness class として通る | **採用**。anomaly の構造検査を入れる |
| M2 | レンズ A-2 | `integrity.clean=False` の cycle を candidate 起因と誤認する | **採用**。`integrity.clean is True` を要求 |
| M3 | レンズ A-1 | `certified=true` / `serializable=true` と `verdict=non-serializable` の相互矛盾を検査しない | **採用**。verify 内部整合を要求 |
| M4 | レンズ A-3 | `anomaly_count == len(anomalies)` を consumer 境界で検査しない | **採用**。両方を要求 |
| M5 | レンズ A-4 + 親 | 正規化の整列・重複排除が構造破損 witness を正常 witness と同一化し、異なる cycle を同一 class へ潰す | **採用**。整列・重複排除を**全廃**する |
| M6 | レンズ A-6 | `reason == verify["verdict"]` は allowlist の下で冗長。連言表が単独反転を示せていない | **採用**。2 つの独立連言へ分解 |
| M7 | レンズ A-6 | RW-02 / RW-07 / RW-08 の負例が変異した連言以外でも落ちる (単一理由性が不成立、DW-M01) | **採用**。負例を組み直す |
| M8 | レンズ B-1 | 「不整合を閉じる」は過大。閉じるのは WAL 側だけ | **採用**。記録の文言を訂正 |
| M9 | レンズ B-2 | 受理集合は narrowing でなく非単調 (旧形除外・新形追加) | **採用**。brief の主張を訂正 |
| M10 | レンズ B-3 | report の reason は変わらない。変わるのは fixture 由来 digest と receipt / reference | **採用**。DW-G05 の記述を訂正 |

### M5 の裁定内容 — 正規化を全廃する

段 2 の `_WITNESS_UNORDERED_LIST_FIELDS` (`cycle` / `edges` / `types` / `reasons` を整列・重複排除) を
**採用しない**。親の実測 — `orchestrator/verifier/dsg.py:578-591` は `cycle=nodes` を最短 cycle の
**順序付き**節点列として作り、`edges` を `zip(nodes, nodes[1:] + nodes[:1])` の ring 順で対応させる。
整列すると同じ節点集合上の異なる cycle が同じ digest へ落ち、`edges` の整列は `cycle` との対応を壊す。

さらにこの正規化は**必要ですらない**。verifier の出力は同一 trace に対して決定的である
(`_sccs()` を size 昇順に整列、`_shortest_cycle`、`_reasons` はいずれも決定的)。吸収すべき
非決定性が無い。

したがって witness class の導出は
**`hashlib.sha256(canonical_json_bytes(anomaly)).hexdigest()` だけ**とする。
`canonical_json_bytes` (`orchestrator/campaign/reflux_origin_artifacts.py:55-70`) が dict key 順を
決定的にし、float / NaN を拒否する。list の順序は一切変えない。

併せて `len(anomalies) == 1` を要求する。verifier policy 成果物が
`witness_class_cardinality = 1` を宣言しており、production の別 SCC は txid 集合が互いに素なので
class cardinality 1 と anomaly 1 件は production 上一致する。明示的に 1 件を要求することで、
段 2 案が持っていた「同一 anomaly の重複を集合化で潰す」経路も同時に消える。

## real だが scope 外 — 裁定パッケージへ送る

- **レンズ A-5: class の意味。** 本裁定の class は occurrence identity (txid) を含む。同じ構造の
  違反が別 txid で 2 回現れると cardinality 2 で拒否される。構造同値類を定義するのは新しい
  一般化であり、ユーザーが明示的に scope 外とした。**限界として明記する。**
- **レンズ A-4 の残り。** reason の重複を持つ構造破損 anomaly は、それ自身が record の
  `constraint_sha256` と一致すれば通る。trace を持たない consumer 境界では
  `mocc_g2_discriminator` の `rw-reason-multiplicity-mismatch` に相当する判定ができない。
  production の `_reasons()` が同一 reason を 2 度返さない保証は読み取れなかったので、
  distinctness を要求すると健全な reject を偽陽性にしうる。**限界として明記する。**
- **terminal 外枠の exact gate。** D1715 が既に scope 外へ送った項目。`_wal_field()` の
  root→payload fallback により root `verify` / `reason` が payload を shadow できる点も同じ。
- **result-evidence record 全体の producer 新設。** 両レンズが独立に real と認めた。
  `OriginProducerInputs` の構築は repo 内で test 1 件だけ。

## refuted

- **未知 abort reason の fail-open。** 否定。1 要素の positive allowlist なので未知値は必ず FC07。
  レンズ A の独立列挙は 30 reason を数え、親の 22 種を包含した。列挙漏れが受理を広げる経路は無い。
- **`total_cycles == anomaly_count` が恒真。** 否定。`orchestrator/verifier/dsg.py:569` が
  `(切り詰めた list, 全 SCC 数)` を別々に返し、`orchestrator/tests/test_verifier.py:2592` に
  `total_cycles=2, len(anomalies)=1` の実例がある。
- **第三の pin の存在。** 否定。レンズ B が 4 経路 (64 桁 hex literal / 長さ literal /
  生成関数の全 caller / orchestrator/tests 外) で独立に走査し、実行可能な pin は
  `reflux_origin_fixture_baseline.json` の 5 entry と `test_reflux_result_evidence.py:24-27` の
  4 literal だけと確認した。親の起動時走査 (blob hash / sha256 で 0 件) と整合する。
- **焦点走の consumer test 漏れ。** 否定。レンズ B の参照関係走査は段 2 の 12 file と差分 0。
- **producer 方向が必ず弱い。** 否定 (上記「方向」参照)。方向の選択理由を狭めた。

## DW-O13 — 要求する値の到達可能性 (実測)

新しい判定式が要求する値の組は、実在する verifier fixture で到達可能である。

`orchestrator/tests/test_verifier.py::test_dense_cycle4_clean_g2` (fixture
`orchestrator/tests/fixtures/r9_dense_cycle4`) は次を assert している。

- `res.integrity.clean()` が真
- `res.certified is False`
- `res.serializable` が偽 / `res.verdict == "non-serializable"`
- `res.total_cycles == 1`
- `len(res.anomalies) == 1`

すなわち「clean integrity・単一 cycle・非切詰め」の組は実 trace から到達する。
到達不能な値を要求してはいない。

## plan v2 — 確定した判定式

`orchestrator/campaign/reflux_formal_consumer.py` の `_validate_wal_outcomes()` の rejected 枝を
次の意味へ置換する。定数は production 正本から import し、逐語 literal を増やさない。

```python
_CANDIDATE_ATTRIBUTABLE_ABORT_REASON = "non-serializable"
_ANOMALY_KEYS = frozenset({"phenomenon", "length", "cycle", "edges"})
_EDGE_KEYS = frozenset({"from", "to", "types", "reasons"})
_REASON_REQUIRED_KEYS = frozenset({"type", "key"})
_REASON_OPTIONAL_KEYS = frozenset({"u_ver", "v_ver"})
_PHENOMENA = frozenset({"G0", "G1c", "G2"})
```

構造検査 `_valid_witness_anomaly(anomaly)` は、production 生成器
(`orchestrator/verifier/report.py` の `_anomaly_to_dict` / `_edge_to_dict` / `_reason_to_dict`、
`orchestrator/verifier/dsg.py:578-591` の ring 構成) から導ける不変条件だけを要求する。

- `anomaly` の key 集合が `_ANOMALY_KEYS` と exact 一致。
- `phenomenon` が `_PHENOMENA` の要素 (`dsg.py:562-567` の `_classify` が返す 3 値)。
- `cycle` が `type(x) is int` の非空 list で、要素が相異なる (最短 cycle なので節点は distinct)。
- `length == len(cycle)` (`model.py:370-372` の property)。
- `edges` が list で `len(edges) == len(cycle)`。
- 各 edge の key 集合が `_EDGE_KEYS` と exact 一致。
- **ring の位置的対応:** `edges[i]["from"] == cycle[i]` かつ
  `edges[i]["to"] == cycle[(i + 1) % len(cycle)]` (`dsg.py:581` の `ring` の定義そのもの)。
- 各 edge の `types` が非空 str list、`reasons` が非空 list。
- 各 reason の key 集合が `_REASON_REQUIRED_KEYS` を含み `_REASON_REQUIRED_KEYS | _REASON_OPTIONAL_KEYS`
  に含まれる。`type` / `key` は str。`u_ver` / `v_ver` があれば `type(x) is int` の list。

判定式本体:

```python
else:
    _require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)
    _require(
        FormalReasonCode.FC07,
        _wal_field(terminal, "reason") == _CANDIDATE_ATTRIBUTABLE_ABORT_REASON,
    )
    verify = _wal_field(terminal, "verify")
    _require(FormalReasonCode.FC07, type(verify) is dict)
    _require(
        FormalReasonCode.FC07,
        verify.get("verdict") == _CANDIDATE_ATTRIBUTABLE_ABORT_REASON,
    )
    _require(FormalReasonCode.FC07, verify.get("serializable") is False)
    _require(FormalReasonCode.FC07, verify.get("certified") is False)
    integrity = verify.get("integrity")
    _require(
        FormalReasonCode.FC07,
        type(integrity) is dict and integrity.get("clean") is True,
    )
    anomalies = verify.get("anomalies")
    _require(FormalReasonCode.FC07, type(anomalies) is list and len(anomalies) == 1)
    total_cycles = verify.get("total_cycles")
    anomaly_count = verify.get("anomaly_count")
    _require(FormalReasonCode.FC07, type(total_cycles) is int)
    _require(FormalReasonCode.FC07, type(anomaly_count) is int)
    _require(FormalReasonCode.FC07, anomaly_count == len(anomalies))
    _require(FormalReasonCode.FC07, total_cycles == anomaly_count)
    _require(FormalReasonCode.FC07, _valid_witness_anomaly(anomalies[0]))
    _require(
        FormalReasonCode.FC07,
        _witness_class_sha256(anomalies[0]) == physical["constraint_sha256"],
    )
```

`type(x) is int` は `bool` を除外する (`type(True) is bool`)。
`_witness_class_sha256()` 内で `canonical_json_bytes()` が `ArtifactError` を上げた場合は
FC07 へ変換し、素通しの例外にしない。

`build_attempt_id`、terminal の `stage` 判定、accepted 枝、`_wal_field()`、FC07 以外の判定式、
reason code、他の gate は変えない。

## plan v2 — token 表と fixture

- `orchestrator/campaign/reflux_source_closure.py:86` の `wal.abort.payload.witnesses` を
  `wal.abort.payload.verify.anomalies` へ変える。1 行の置換に留め、entry を増やさない。
- `orchestrator/tests/reflux_origin_fixture_builder.py:312` の同 literal を同時に変える。
- 同 builder の abort payload (`:376-386`) を production 形へ揃える —
  `reason`, `build_attempt_id`, `build_admission_receipt_sha256`, `verify`, `workload`。
  `verify` は `orchestrator/verifier/report.py:96-137` と同じ key 集合から `trace_dir` を除いたもの。
- `_CONSTRAINT_SHA256` は fixture 独自の `_canonical_bytes` / `_sha256`
  (`reflux_origin_fixture_builder.py:64-79`) で anomaly literal から導く。
  production の `canonical_json_bytes` を fixture から呼ばない (D1665 の独立性)。
- pin の新しい値は**実装子が変更後の実物から再計算する**。段 2 / 段 3 が提示した値をコピーしない。
  対象は `orchestrator/tests/reflux_origin_fixture_baseline.json` の
  `build_source_closure_record` / `build_launch_admission_inputs` /
  `build_recovery_envelope_inputs` / `build_ordered_wal_projection` /
  `build_result_evidence_record` の 5 entry (hash と byte 長の両方を全 entry 再計算) と、
  `orchestrator/tests/test_reflux_result_evidence.py:24-27` の golden literal 4 個
  (および `:145-151` の raw record 長を実物で確認)。

## plan v2 — 正例の positive control

新しい構造検査が**実の production 出力を受理する**ことを、性質でなく実体で示す。

`orchestrator/tests/test_reflux_formal_consumer.py` に、
`orchestrator.verifier.core.verify_trace_dir` を `orchestrator/tests/fixtures/r9_dense_cycle4` に
対して実走し、`orchestrator.verifier.report.result_to_dict()` の
`["anomalies"][0]` が `_valid_witness_anomaly()` を通ることを assert する test を 1 本足す。
これは「性質を満たす手書き dict」ではなく**実の callee**を名指しする正例である。

## 変異事前登録 (B-060、番号は fold 時に確定)

runner は焦点走 12 file、`--runner-mode dispatch`。baseline PASSED を必須とする。
各変異は、変異した連言だけが判定を変える負例で kill されること (DW-M01 の単一理由性) を
実装後に確認する。確認できない変異は登録せず実効 gate へ再照準する。

| id | 変異 | 期待 | 単一理由性のための負例 |
| --- | --- | --- | --- |
| B-060-M1 | `reason` の allowlist 比較を `True` にする | KILLED | reason だけ `indeterminate`、verify は正例のまま |
| B-060-M2 | `verify["verdict"]` の比較を `True` にする | KILLED | verdict だけ `indeterminate`、reason は `non-serializable` |
| B-060-M3 | `integrity.clean is True` を落とす | KILLED | integrity だけ `clean=False`、他は正例 |
| B-060-M4 | `serializable is False` を落とす | KILLED | serializable だけ `True` |
| B-060-M5 | `certified is False` を落とす | KILLED | certified だけ `True` |
| B-060-M6 | `anomaly_count == len(anomalies)` を `True` にする | KILLED | anomaly_count だけ 2、total_cycles も 2、anomalies は 1 件 |
| B-060-M7 | `total_cycles == anomaly_count` を `True` にする | KILLED | total_cycles だけ 2、anomaly_count は 1 |
| B-060-M8 | `type(total_cycles) is int` を `isinstance(..., int)` へ緩める | KILLED | total_cycles / anomaly_count を `True` にする |
| B-060-M9 | `len(anomalies) == 1` を `>= 1` へ緩める | KILLED | 相異なる 2 anomaly、counter も 2 |
| B-060-M10 | `_valid_witness_anomaly` の ring 位置対応検査を落とす | KILLED | edges の from/to を入れ替えた anomaly |
| B-060-M11 | `_valid_witness_anomaly` の exact key 集合検査を落とす | KILLED | anomaly に余分 key を 1 つ足す |
| B-060-M12 | `_valid_witness_anomaly` を無条件 `True` にする | KILLED | `anomalies=[{}]` (レンズ A-1 の入力そのもの) |
| B-060-M13 | witness digest の exact 比較を `True` にする | KILLED | anomaly は正例のまま、record と ledger の constraint を別の有効 64 桁値へ揃える |
| B-060-M14 | token 表を旧 `wal.abort.payload.witnesses` へ戻す | KILLED | 正例 fixture の source closure 発行 |
| B-060-M15 | baseline の変更 entry を 1 文字壊す | KILLED | fixture builder の独立再計算 |

SURVIVED を期待する変異は登録しない。

## 成果物影響 (DW-G05) — 訂正版

放置したときに変わるのは次であり、certified 選択集合・材料レポート・ledger event は変わらない
(D338 により consumer は全検査通過後も `P6Unavailable` を返す)。

- **参照:** source-closure 成果物が「`verifier_policy_sha256` は runtime で
  `wal.abort.payload.witnesses` に束縛される」と宣言しているが、その field は
  production にも consumer にも存在しない。proof chain の成果物が**指示対象の無い束縛**を
  主張している状態であり、この束縛を信頼する後続の producer は虚構に対して実装することになる。
- **受理集合:** FC07 の rejected 枝は production の証拠を 1 件も読めない。変更後は
  旧 3-field 形が除外され、production `verify` 形が追加される (非単調)。
- **実差:** fixture 由来の record / source-closure digest と、そこから連鎖する
  receipt・`formal_receipt_sha256`・`evidence_root_sha256`。

## 焦点走 file 集合 (12、段 2 とレンズ B が一致)

```text
orchestrator/tests/test_ccbench_spawn_sites.py
orchestrator/tests/test_p3_autonomous_workload_trial.py
orchestrator/tests/test_reflux_formal_consumer.py
orchestrator/tests/test_reflux_origin_artifacts.py
orchestrator/tests/test_reflux_origin_binding.py
orchestrator/tests/test_reflux_origin_client.py
orchestrator/tests/test_reflux_origin_fixture_builder.py
orchestrator/tests/test_reflux_origin_topology.py
orchestrator/tests/test_reflux_originless_compatibility.py
orchestrator/tests/test_reflux_result_evidence.py
orchestrator/tests/test_reflux_source_closure.py
orchestrator/tests/test_trial_registry.py
```

新規 test で `orchestrator/verifier` を import するため、正例走の追加 node は
`test_reflux_formal_consumer.py` 内に置く。新規 test file は作らない
(file 集合メタテストの更新を発生させない)。

## 分割方針

変更面は 4 file (consumer / source closure / fixture builder / 2 つの pin file) で、
判定式が 1 箇所に集中するため実装子は 1 本。
