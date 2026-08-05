# [T-452] + [T-453] 変異台帳

wave `dev-wave-t452-t453-clock-authority` / anchor commit `b84d30d` (fix 2 巡目) /
harness `tools/mutation_harness.py` / runner `python3 tools/run_tests.py -q -rf` (計算ノードへ dispatch)

spec = `mutation-spec.json` (sha256 `d00d91731cc189b722d834032719441f3ea22ad771e109388d61f49a385f2a72`)、
再照準分 = `mutation-spec-m6b.json` (sha256 `9a1252e33b8be39d9078a3adaa644f5c4bc8ba460f859b77a4d9739fb03d26e1`)。
baseline は両走行とも rc=0 / 赤 0 件。

## 結果

| ID | 変異 | harness 判定 | 期待 ⊆ 実測 | 親の裁定 |
|---|---|---|---|---|
| M1 | policy 定数 `2.0` → `3.0` | MISMATCH | 部分 | **KILLED** — 実測 47 node。期待に挙げた metamorphic は落ちないのが正しい (下記 erratum-A) |
| M2 | loader の policy equality を削除 | MISMATCH | ○ | **KILLED** — 実測 5 node、期待 4 node をすべて含む |
| M3 | issuer の policy equality を無効化 | MISMATCH | ○ | **KILLED** — 実測 13 node、期待 4 node をすべて含む |
| M4 | canonical consumer の policy equality を無効化 | MISMATCH | ○ | **KILLED** — 実測 12 node、期待 1 node を含む |
| M5 | 取得時 self gate の observed を `[:-1]` で slice | MISMATCH | 部分 | **KILLED** — 実測 3 node (下記 erratum-B) |
| M6 | receipt の observed clock 検査を無効化 (初回) | **SURVIVED** | × | **変異の作りの誤り** — 再照準して M6b へ (下記 erratum-C) |
| M6b | 同 gate の実効部分 `set(observed_clock) != {"samples_mhz"}` を除去 | **KILLED** | ○ | **KILLED** — 実測 1 node = 期待 1 node。単一理由 |
| M7 | silo の canonical 述語を median 比較へ戻す | **KILLED** | ○ | **KILLED** — 実測 2 node = 期待 2 node。単一理由 |
| M8 | v1 legacy parser の sentinel 厳密検査を緩める | **KILLED** | ○ | **KILLED** — 実測 3 node = 期待 3 node。単一理由 |
| M9 | registry 不変条件の loop 内で `passes = True` に固定 | **KILLED** | ○ | **KILLED** — 実測 1 node = 期待 1 node。単一理由 |
| M10 | expected schema 上限を `== 100.0` の一点判定へ退行 | MISMATCH | 部分 | **KILLED** — 実測 2 node (下記 erratum-D) |

**再照準後の 11 件すべてで kill が成立した。SURVIVED は 0 件。**

## erratum (初回結果は消さない — `DW-M02`)

### erratum-A — M1 の期待ノードが過剰だった

`test_effective_clock_policy_metamorphic_wiring_producer_loader_issuer_consumer_self` を期待赤に
挙げたが、この検査は **設計上 policy 値に非依存**である (自分で policy を `3.0` / `2.0` へ patch し、
producer・loader・issuer・consumer・self gate が一斉に追従するかだけを見る)。定数を `3.0` に
変えても緑のままなのが正しい挙動であり、値の変更を殺したのは AST の
`test_effective_clock_policy_is_single_literal_authority` である (これは期待どおり赤になった)。
実測赤 47 node は、policy 定数が広く配線されていることの証拠でもある。

### erratum-B — M5 の期待ノード名が誤りだった

slice 変異を殺したのは `test_self_gate_rejects_outlier_at_every_index` (48 index を全数
parametrize した検査) と `test_cli_effective_clock_self_failure_is_quality_rejected_before_publish[47]`
であり、**まさにこの変異を想定して設計した検査**である。親が期待欄に別名
(`test_self_gate_rejects_all_nonpolicy_equality_edges`) を書いた登録ミスであって、gate の穴ではない。

### erratum-C — M6 の変異が実効 gate を外していなかった

初回の M6 は
`if (not isinstance(observed_clock, Mapping) or set(observed_clock) != {"samples_mhz"}):` の先頭へ
`False and` を挿入した。Python では `and` が `or` より強く束縛するため、式は
`(False and not isinstance(...)) or (set(...) != {...})` となり、**実効 gate である key 集合検査が
そのまま残っていた**。注入自体は実在した (diff で確認) が、対象 gate を無効化できていない。
`DW-M04` の「SURVIVED は注入実在を確認するまで equivalent としない」に従い、
key 集合検査そのものを除去する M6b へ再照準して KILLED を確認した。

### erratum-D — M10 の期待ノードが過剰だった

`>= 100.0` を `== 100.0` へ退行させても `100.0` 自身は依然拒否されるため、
`test_expected_clock_tolerance_upper_boundary_rejects[100.0]` は緑が正しい。
赤になるべきは `[100.00000000000001]` と `[1e+300]` の 2 件であり、実測はそのとおりだった。

## 正例 (受理集合を縮小する wave の過剰拒否検出)

| ID | 正例 | 結果 |
|---|---|---|
| P1 | policy `2.0` かつ全標本が帯内の観測が canonical consumer と silo の live/raw で pass する | 緑 (`test_silo_live_clock_wiring_moves_with_policy_and_uses_exact_keys[3.0-True]` ほか) |
| P2 | 履歴 v1 artifact 19 件が legacy parser で射影でき、`5.0` / `99.0` の expected artifact が schema では依然 parse 可能 | 緑 (`test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies`、`test_schema_v2.py` の共有 fixture が `5.0` を維持) |

## 運用上の記録

- 変異 M3 の走行で dispatch が `rc=16` (infra 失敗) を返し、harness は failed node を確実に抽出
  できないため fail-closed で停止した。`--resume` で継続し、残りを完走させた。
  **`rc=16` は変異結果ではない。**
- 変異走行中は worktree を触っていない (受入全走との重ね実行もしていない)。
