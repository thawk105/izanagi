# [T-1851] 単位 C1b 実装 — 段 4 裁定と変異事前登録

base `8924c0ef3`。**契約の正本は
`output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`、
実装手順は同 dir の `plan-v2.md`。本 wave はこの 2 文書を書き換えない。**

## 1. 段 2・3 の流用

読み込み契約の規定により、変更面の骨格が同一なので前 wave の段 2 plan・段 3 レンズ 2 本を
流用する。再検査は段 6 レビューへ寄せる。**旧 brief は流用せず、段 1 で anchor を測り直した。**

## 2. 段 1 実測が出した新事実の裁定

| # | 新事実 | 裁定 |
|---|---|---|
| P1 | plan v2 §4.4 の呼出し閉包 (4 / 7 / 3) は **caller 数ではなく出現数**。実 caller は 2 / 6 / 2 | **real。ただし plan の結論は覆らない** — 「callback 規約を変えるなら全 callable を同じ commit で直す」は不変。実装子は数を写さず自分で数え直す |
| P2 | `record_attempt_terminal` の consumer は s8b 系の外にもある (`p3_autonomous_workload_trial` / `trial_registry` / `s8c_preregistration_evidence` と各 test、計 14 file) | **real。plan の「keyword-only 既定なら既存 caller は変更不要」は保たれる見込みだが、実装子が実際に確かめる。** 変更が要ると判明したら実装せず報告する |
| P3 | `test_official_perf_closure.py` の集合等値 assert は `:903` ではなく `:905` | **real・微差。** 契約 9 節の要求 (leaf に perf 述語の新しい直接 call を置かない) は不変 |

**契約 v3.1 と plan v2 のその他の条項は、段 1 の実測ですべて裏が取れた。変更しない。**

## 3. 本 wave の実装範囲

plan v2 §2 の **実装子 1 (leaf) を先に単独で閉じる。** 所有 file は 2 本。

- `orchestrator/campaign/s8b_terminal_evidence.py` (新設)
- `orchestrator/tests/test_s8b_terminal_evidence.py` (新設)

leaf が閉じたら実装子 2 (統合、既存 8 file) を同 wave 内で直列に起動する。
**規模が尽きた場合は leaf を checkpoint として次 wave へ送る** (plan v2 §6、ユーザー裁定済み)。

## 4. 変異事前登録 (DW-M01)

**実装前に登録する。** 各変異は実装後に「同じ入力を拒否する層が前後にも内側にも無い」ことを
確認し、確認できなければ登録を取り下げて実効 gate へ再照準する。**冗長 gate による赤を kill に
数えない。**

### 4.1 実装子 1 (leaf) の変異 — 本 wave で走らせる

| ID | 位置 | 変異 | 期待する単一理由 |
|---|---|---|---|
| L1 | 証拠 schema の exact key 検査 | 最外層に余分 key を 1 つ許す | outer exact key 検査だけが拒否 |
| L2 | `attempt_binding` の exact 検査 | draft 9 key 集合へ余分 key を 1 つ許す | draft binding の exact 検査だけが拒否 |
| L3 | 同上 | `observation_event_sha256` を `observation_start_event_sha256` の綴りへ置換 (契約 1.3) | validated binding の exact 検査だけが拒否 |
| L4 | canonical bytes 生成 | 末尾 LF を 1 つ足す | canonical bytes 等値検査だけが拒否 |
| L5 | canonical bytes 生成 | JSON separator を `", "` へ変える | 同上 (L4 と別変異) |
| L6 | 非有限値の正規化 | 非有限値を `throughputs` に残す | 有限性検査だけが拒否 |
| L7 | 同上 | `nonfinite_count` を増やさない | 契約 1.4 の和の不変条件だけが拒否 |
| L8 | E1 枝順 | 枝 1 (競合) を枝 2 (failure) の後ろへ移す | 競合入力の E2 語だけが変わる |
| L9 | E1 枝 2 / 3 | `failure` 非 null 枝を削除 | 該当入力の分類だけが変わる |
| L10 | E1 枝 4 | partial exec を `measurement_dispersion_exceeded` へ誤分類 | 該当入力の E2 語だけが変わる |
| L11 | `assess_session` への入力 | 落とした本数だけ `reps_expected` を減らす (契約 1.4 が名指しで禁止) | `required_reason` の消失だけが露見 |
| L12 | 主値の取り方 | `assess_session.median` でなく `throughputs[0]` を使う | 主値の等値検査だけが拒否 |
| L13 | 4.2 の捕捉集合検査 | launcher の 3 語集合から `OSError` を落とす | exception_type の member 検査だけが拒否 |
| L14 | 同上 | 集合外の型名を受理する | 同上 (L13 と向きが逆) |
| L15 | `require_sealed_terminal_evidence` | 型を `type(x) is` から `isinstance` へ緩める | 厳密型検査だけが拒否 |
| L16 | 相互整合 (契約 2 節) | `probe_after is None ⇔ probe_before.competing` の片方向を落とす | 相互整合検査だけが拒否 |
| L17 | digest 再導出 | `raw_output_sha256` を文書の自己申告値からコピーする | digest 再導出の等値だけが拒否 |
| L18 | immutability | `canonical_bytes` が内部 bytes への参照をそのまま返す (可変化) | immutability 検査だけが拒否 |

### 4.2 実装子 2 (統合) の変異 — 実装子 2 を起動できた場合だけ

plan v2 §5.1 の M1〜M12 に加え、§5.2 の**生存 2 件に専用の kill 手段を割り当てる。**

| ID | 変異 | kill 手段 (D1522) |
|---|---|---|
| S1 | `terminal-failure` 枝だけ `failure_reason` 固定のまま残す | `_assert_null_matrix` を v2 profile の `retryable_reason_field` つきで**直接呼び**、`terminal-failure` 行で照合先が切り替わることを単独で確かめる |
| S2 | `:1687` の old replay だけ evidence 再読を省く | evidence loader の**呼出し回数を数える seam** を置き、old / candidate の 2 回が独立に発火することを確かめる |

`not-consumed` 枝の正例も同じく **D1522 の下層直呼び**で作る (契約 5.3)。
**上流の sealed 経路を正例に使わない** — E1 は `not-consumed` を出さないため恒真な拒否になる。

## 5. 停止条件

- 契約 v3.1 の条項を実装子が「実体化できない」と判断した場合、**回避策を自作せず報告して止める**
  (前 wave が契約 v2 で踏んだ型)。
- 規模上限を超えそうなら止めて報告する。production の途中分割はしない。
- 所有外 file に変更が要ると判明したら実装せず報告する。
