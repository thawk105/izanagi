# [T-2436] 段 4 裁定 — WW 理由の整列

段 3 の 2 レンズ (A: 正しさ境界 / B: 検査の実効性) の所見を real / refuted で裁定し、plan v2 と
変異事前登録を確定する。**裁定 inbox を再走査した結果、wave 開始後に main は 1 commit も進んで
おらず (base `cc9bba523` = 現 main)、承認済み裁定を覆す新事実は無い。**

## 1. レンズ A の所見

| # | 所見 | 判定 | 裁定 |
| --- | --- | --- | --- |
| A-1 | wr 枝の順序安定性が parser の `Txn.reads` 構築順まで証明されておらず、親の一般化が閉じていない | **real** | **採用。親が実測で閉じた** (下記 2)。テスト追加はしない |
| A-2 | 束縛調査が path literal と blob SHA の完全一致に限られ、role/group/schema/集約 digest を key にする束縛を排除できていない | **real** | **採用。親が実測で閉じた** (下記 3)。証拠の書き方も直す |
| A-3 | 凍結成果物調査が JSON/JSONL に限られ、text renderer の出力と派生 digest を見ていない | **real** | **採用。親が実測で閉じた** (下記 4) |
| A-4 | brief の「commit 前は必ず `contract-loader-drift` で赤」は断定しすぎ | **real** | **採用。「発火しうる」へ統一**し、実装段で exact nodeid と rc を分けて記録する |
| A-5 | 新テストが `phenomenon` / `serializable` / `verdict` / `certified` を固定していない | **real** | **一部採用。** `verdict` / `serializable` / `phenomenon` は足す。**`certified` は足さない** — 過剰決定だから (下記 5) |
| — | 受理集合・`phenomenon`・`integrity.notes` 発火条件・key 単独整列の十分性 | refuted | 実装変更なし |
| — | `workers>1` で理由列が並べ替わる経路 | refuted | 実装変更なし |
| — | 規律 2 に触れる向き・新テストの恒真性 | refuted | 実装変更なし |

## 2. A-1 の解消 — 親の実測

1 つの辺に **WR 理由を 6 本**持つ trace を作り、6 seed で測った (`probe_wr_order.py`)。

```
seed 0   0->1 ww=060104030205 wr=0b0c0d0e0f10 | 1->0 rw=010203040506
seed 1   0->1 ww=050204010306 wr=0b0c0d0e0f10 | 1->0 rw=010203040506
seed 2   0->1 ww=040105030602 wr=0b0c0d0e0f10 | 1->0 rw=010203040506
seed 3   0->1 ww=050206030401 wr=0b0c0d0e0f10 | 1->0 rw=010203040506
seed 4   0->1 ww=010603050204 wr=0b0c0d0e0f10 | 1->0 rw=010203040506
seed 777 0->1 ww=020103040506 wr=0b0c0d0e0f10 | 1->0 rw=010203040506
```

**wr も rw も 6 seed すべて同一順で、変動するのは ww だけである。** 一般化ではなく実測になった。
D1817 の scope (WW 交差だけ整列する) は十分。

## 3. A-2 の解消 — 探索ではなく履歴で閉じる

「path 以外を key にした束縛が無い」は**探索では原理的に閉じない** (探索語が存在しないから)。
代わりに履歴で閉じた。

`orchestrator/verifier/dsg.py` は直近 1 週間で **3 回変更されている** (`d719c1e35` 2026-09-02、
`709e57b66` 2026-09-05、`54183270e` 2026-09-05)。その間 main は緑である。
**dsg.py の内容に張られた live pin は、per-file でも集約でも存在しない** — 存在すれば
これらの wave がすでに踏んでいる。最終的な権威は commit 後の受入全走であり、本 wave はそれを行う。

## 4. A-3 の解消 — text 出力も 0 件

text renderer は `ww key=<key> (e,t)→(e,t)` の形で理由を並べる (`report.py:144-154`)。
追跡下でこの文字列を含む file は 2 件だけで、**1 行に `ww key=` を 2 個持つ行は 0 件**
(`git grep -c "ww key=.*ww key=" -- .` が rc=1)。構造化 JSON 側の 0 件と合わせ、
**凍結成果物の再発行は不要**が text 面でも成立する。

## 5. A-5 の一部不採用 — `certified` は過剰決定

`Integrity.clean()` は counter 11 個に加えて `proof_surfaces.certification_gate_satisfied()` と
commit witness の一致も要求する (`model.py:450-467`)。本 wave の合成 trace は protocol の
proof-surface metadata を持たないため、**counter が全部 0 でも `clean()` は False** になる
(親の実測)。したがって `certified is False` は「cycle があるから」と「integrity が unclean だから」の
**2 つの独立な理由**で成立し、`DW-M03` の言う過剰決定になる。

`verdict` は `not serializable` を先に見る (`model.py:503-515`) ので、cycle だけで
`"non-serializable"` に決まる。よって固定するのは次に限る (親の実測値)。

```
verdict = "non-serializable"   serializable = False
anomaly_count = 1              total_cycles = 1
anomalies[0].phenomenon = "G2" anomalies[0].cycle = [0, 1]   length = 2
```

`certified` は assert しない。理由をテストの comment に 1 行残す。

## 6. レンズ B の所見

| # | 所見 | 判定 | 裁定 |
| --- | --- | --- | --- |
| B-1 | 新 node を受入所要時間台帳へ登録しない判断の根拠が不足 (担当と時点が無い) | **real** | **採用。ただし登録は本 wave では行わない** (下記 7) |
| B-2 | M1〜M4 は受理集合を変えないので契約上 `KILLED` ではなく `diagnostic sensitivity pin` | **real** | **採用** (`DW-M08` の明文どおり) |
| B-3 | M4 (`key=hash`) の失敗保証が未実測 | **real** | **採用。M4 を事前登録から外す** (下記 8) |
| B-4 | 残る限界 (`workers=1` のみ、固定 seed の保証範囲) を明記すべき | **real** | **採用。記録に残す** |
| — | seed 1/777・6 key の設計、subprocess の env と import 経路 | refuted | 設計変更なし |
| — | 所要時間見積り、新規 test file 回避、fixture 非新設 | refuted | 設計変更なし |
| — | 等価変異の区別 | refuted | ただし段 6 の spec では省略せず全候補に完全 nodeid を書く |
| 両レンズ | SHA-256 の assert は bytes 一致から従うので冗長 | — | **採用。落とす** (規律 5、盛らない) |

## 7. B-1 の裁定 — 台帳は本 wave の変更面に含めない

**`orchestrator/tests/acceptance_duration_ledger.json` は変更しない。**

- 理由は仮想リスクではなく直近の実測である。worklog 1367 ([T-2366] wave) は、branch 側で同 file を
  更新すると main を取り込むたび競合し、**競合を解決した merge は land の前進 merge 検査が
  非 clean として拒否する (rc=23)** ため受入をやり直す循環に入ることを実測した (3 回・約 2 時間)。
  同 wave はこの循環を断つために台帳を main 側へ一本化した。
- 被覆 gate は `登録済み nodeid ÷ 収集 nodeid >= 0.90`。現在 20042 entry / 収集約 21866 node で
  約 91.7%、閾値に対し約 1.7 point の余裕がある。**新規 1 node では破れない。**
- 代わりに本 wave は (a) 受入時に当該 node の実所要を測って worklog と insight に残し、
  (b) 上の余裕を数字で書き、(c) 登録は台帳更新を主目的とする別 wave が行うと明記する。
  **推定値を実測せずに登録することは禁じる** (レンズ B の指摘どおり)。

## 8. 変異事前登録 (`DW-M01`、実装前登録)

対象は `orchestrator/verifier/dsg.py` の `_reasons()` の WW 交差 1 箇所。
**区分はすべて `diagnostic sensitivity pin`** (受理集合も fail-closed 挙動も変わらず、
構造化シグナルの順序だけを pin するため。`DW-M08` の明文)。

| ID | 変異 | 期待 |
| --- | --- | --- |
| M1 | `sorted(...)` を外し `for k in u_writes.keys() & v_writes.keys():` へ戻す | 赤 node = `orchestrator/tests/test_verifier.py::test_multi_ww_reason_report_is_hash_seed_deterministic` の**完全一致 1 件** |
| M2 | `sorted(..., reverse=True)` | 同上の完全一致 1 件 |
| M3 | `sorted(..., key=lambda key: (u_writes[key], v_writes[key]))` | 同上の完全一致 1 件 |

- **M4 (`key=hash`) は登録しない。** hash 値が seed で変わることは、6 key の相対順が seed 間で
  必ず変わることを含意しない (レンズ B)。probe 2 パスの費用に見合わない (規律 5)。
- 等価変異 (赤を要求しない): `sorted(..., key=lambda key: key)`、
  `sorted(v_writes.keys() & u_writes.keys())`、`sorted(set(u_writes).intersection(v_writes))`。
- **単一理由性 (`DW-M01`):** M1〜M3 は受理集合を変えないので、前後・内側の他層は赤にならない。
  期待 node が 1 件の完全集合であること自体が、既存テストが整列を区別しないという親の静的実測
  (多重 WW golden 0 件) の実走による裏取りになる。段 6 で実測して確認する。

## 9. plan v2 (確定)

1. **実装。** `orchestrator/verifier/dsg.py` の `_reasons()` の
   `for k in u_writes.keys() & v_writes.keys():` を `for k in sorted(...):` にする。整列 key は
   key 文字列のみ。他は 1 文字も変えない。
2. **テスト。** `orchestrator/tests/test_verifier.py` へ
   `test_multi_ww_reason_report_is_hash_seed_deterministic` を 1 本足す。
   - 6 key の 2-transaction lost-update trace を `_tmp_trace` で一時生成 (fixture は新設しない)。
   - `PYTHONHASHSEED` を `"1"` と `"777"` にした subprocess を 2 本立て、
     `result_to_dict(verify_trace_dir(dir, workers=1))` を
     `json.dumps(sort_keys=True, separators=(",", ":"))` した **bytes の一致**を assert。
   - 各 report で、辺 `0->1` の理由列が `[("ww", k) for k in sorted(keys)]` と一致することを assert。
   - 各 report で `verdict == "non-serializable"`、`serializable is False`、`anomaly_count == 1`、
     `total_cycles == 1`、`anomalies[0]["phenomenon"] == "G2"` を assert。
   - **`certified` は assert しない。** 過剰決定である旨を comment に 1 行残す。
   - **SHA-256 の assert は置かない** (bytes 一致から従う)。
   - `finally` で一時 trace を削除する。
3. **変更しないもの。** wr / rw 枝、consumer 側の正規化、fixture、`_V2_FIXTURE_FILES`、
   `acceptance_duration_ledger.json`、closure の binding、gate / 検査 / 台帳の新設。

## 10. 記録に残す限界 (B-4、A-4)

- 固定 seed 2 本の検出力は、**実測した CPython 3.10.12 と固定入力**に対する実証であって、
  将来の Python の文字列 hash / set 実装に対する形式証明ではない。
- 本テストは `workers=1` だけを通す。**worker 数を変えても report 全体が同一**であることは
  本 wave の検査対象ではない (既存の `test_parallel_edge_replay_uses_global_logical_ordinal` が
  同一 process 内での一致を見ているのみ)。
- commit 前に焦点走を回すと `contract-loader-drift` が**発火しうる**。必ず赤になるとは書かない。
  実装段では exact nodeid と失敗 reason、commit 前後の結果を分けて記録する。
