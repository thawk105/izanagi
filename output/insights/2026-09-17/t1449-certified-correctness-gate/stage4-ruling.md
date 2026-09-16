# 段 4 裁定 — [T-1449] 条件付き最小 gate (2026-09-17 01:30 JST、親)

入力: `s1-brief.md`、`artifacts/.../s2-plan-2.md`、`artifacts/.../s3-a-1.md` (レンズ A、sol)、`artifacts/.../s3-b-1.md` (レンズ B、luna)、
`rulings-verbatim.md`。裁定 inbox に T-1449 / D1272 の新規更新なし (段 4 直前に再走査)。main = `1042a1bc9` 不変。
baseline 焦点走 (unit3 + unit5 + t139_submission_path、変更前) = **122 passed / 36.3 秒** (計算ノード、`baseline-focus.log`)。

## 1. 所見の裁定

| # | 出所 | 所見 (要旨) | 分類 | 裁定 |
|---|---|---|---|---|
| A1 | A | P1-b は §7.1(1) の失敗許容を「性能 completed が無い場合」へ狭める。「性能 completed + 検証失敗 + 0〜5 件」全体が偽造だという根拠はない | real | **採用。plan v2 で gate 条件を改める (§2)** |
| A2 | A | 検証割当てが 6 build を保存した後、性能割当てと残りの検証処理 (correctness run 等) が重なる時系列を追補 A は排除していない | plausible | **採用 (保守側)。** 親が検算: 検証 attempt の失敗は `post_performance_failure` の 3 raw 経路 (marker / actual / a03) を持てないので `pre_performance_infra_failure` にしか写らず、a10 で study は `design_not_feasible` 終端。その stage 受領証は §7.1(1) が 0〜5 件で受理すると凍結している。**この形は正規の失敗記録であり gate は発火してはならない** |
| A3 | A | raw anomaly 共存例は既存拒否 (V:2031-2035) であり新 gate の効果に数えない | real | 採用。matrix・記録で新 gate の拒否例から外す |
| A4 | A | 「性能 completed attempt が 1 件ある = 成功・certified」は D1272 と同値でない | real | 採用。成功の raw 定義を §2 のとおり「性能 completed があり、検証割当ての失敗が記録されていない」へ改める。attempt 成功 / stage 成功 / certified 採用の 3 択は §5 の裁定パッケージへ (本 wave は単票 gate のみ) |
| A5 | A | study 入口だけへの移設も単票・writer の 0 件経路を残す | plausible | 採用 (study-only 案は不採用)。単票 gate に置く |
| A6 | A | reason_code の参照自体は §8 違反でない | refuted | 同意。§8 は「申告値を正の権威にしない」まで |
| A7 | A | `test_reason_code_completed_is_not_positive_authority` は gate の条件選択を証明しない | real | 採用 (証明根拠に数えない) |
| A8 | A | `correctness` reason の一致だけでは新 gate の拒否を識別できない | real | 採用。各新負例は M1 (gate 削除) で受理へ反転することを matrix で示す (単一理由性) |
| A9 | A | 三者比較は TU・arm 束縛まで保証しない | real / scope 外 | 不採用 (実装しない)。§5 裁定パッケージ |
| A10 | A | brief の「失敗なら design_not_feasible」「正規手順で生じない」は引用元より強い | real | 採用 (brief 訂正 §6) |
| A11 | A | アンカー: 6 対規則は V:1994-2017、liveness は U:637、verification phase は U:351、`_full_receipt` 終端 646 | real (nit) | 採用 (§6) |
| A12 | A | 「study-level は scope 外」は直接変更 / 呼出経由の影響 / 未配線 (単位 6) を分けて書く | real | 採用 (記録の書き分け) |
| B1 | B | 4 配列に触る vector は 7 本でなく 14 本、46 本の内訳は receipt 33 / writer_authority 5 / prereg 2 / その他 6 | real | 採用 (記録)。**ただし §3 のとおり `_full_receipt` は変えないので vector は構造上不変**。46 本は unit5 全走で実測 |
| B2 | B | `negative-6.6-correctness-raw` は名前と違い `schedule_seed` を変える | refuted (親の前提) | 採用 (記録)。raw anomaly の根拠は U3:1011 / 1037 |
| B3 | B | fixture 拡張は既存 recipe の file 解決を壊さない (failure raw を残す限り) | refuted (懸念) | 同意 |
| B4 | B | M4 の編集位置を exact diff で固定 | plausible | 採用 (§4) |
| B5 | B | 完全 6 対 + 重複 1 件 = 7 件を件数検査削除が見逃す負例と変異を追加 | real | 採用 (T5 / M6、単体入口。top-level は schema maxItems 6 で shape が先に立つ) |
| B6 | B | M2 (gate 削除) は「既存 test では殺されない」対照を別記録 | real | 採用 (§4 の記録欄) |
| B7 | B | 新負例は top-level で観測可能 (先行層は空配列を走査しない) | refuted (懸念) | 同意。T2 を top-level に置く |
| B8 | B | 受入 5 分は実測で判定 | plausible | 採用 (段 6 で焦点 3 file + 受入全走) |
| B9 | B | `test_mocc_trace_job_contract.py:3856` は同名 enum、consumer でない | refuted (親の前提) | 採用 (焦点集合から外す) |
| B10 | B | 「vector は test 名を参照するだけ」は不十分: test 名の実在 + recipe 実行結果が拘束 | real | 採用 (brief 訂正)。`_full_receipt` 不変で recipe 結果も不変 |
| B11 | B | writer / study への新負例投入は直接試験されない | real | 採用 (記録は「直接検証 = 単体・top-level、writer / study = 呼出関係 + 既存回帰」) |

plan の P1-b (性能 completed ⇒ 6 対を無条件に要求) は **A1/A2 により不採用**。plan の他の部分 (挿入点、reason、fixture 部品、負例の形、M0〜M10 の骨格、焦点集合) は v2 へ引き継ぐ。

## 2. plan v2 — gate の確定

**gate (1 条件)。** `_validate_reason_branches` の attempts loop の後 (V:2049 の直前、`performance_slots` が確定した位置) に置く:

```python
verification_failure_recorded = any(
    isinstance(attempt, Mapping)
    and attempt.get("cluster_slot_or_null") is None
    and attempt.get("reason_code") != "completed"
    for attempt in attempts
)
if performance_slots and not verification_failure_recorded:
    evidence = value.get("correctness_evidence", ())
    evidence_pairs = {
        (entry.get("arm"), entry.get("workload"))
        for entry in evidence
        if isinstance(entry, Mapping)
    }
    expected_pairs = {(arm, workload) for arm in _ARMS for workload in _WORKLOADS}
    if len(evidence) != 6 or evidence_pairs != expected_pairs:
        _semantic(
            "correctness",
            "completed performance without a recorded verification failure "
            "requires six correctness arm/workload pairs",
        )
```

- `performance_slots` は loop 内で marker・allocation・failure・36-run 双射の raw 検査を通過した completed 性能 attempt の集合 (reason_code の申告だけで作らない、§8)。
- `reason_code != "completed"` の検証 attempt は loop で 4 値のいずれかに検証済みなので「失敗を記録した attempt」と同義。`correctness_anomaly` は `anomaly=True` を要求し、同じ anomaly が completed 性能 attempt を先に殺すので後段には来ない。

**禁止の署名:** 既存 raw 検査を通過した completed 性能 attempt が 1 件以上あり、検証割当て (`cluster_slot_or_null == null`) の非 completed な attempt が 1 件も無い受領証は、`correctness_evidence` が (stock, mode1, modeX) × (W1, W2) の 6 対を各 1 件・計 6 件で覆わない限り `SemanticValidationError(reason_code="correctness")` で拒否する。

**通る正例 (3 つ):**
1. 性能 completed + 検証 completed + 6 対 + liveness_run 6 件 (新 fixture `_certified_receipt`) — 受理。
2. 性能 completed + 検証 `pre_performance_infra_failure` + correctness 1 件 (現行 `_full_receipt`、§7.1(1) の失敗記録) — 受理 (gate は発火しない)。
3. 性能 completed 無し (全 attempt 失敗) + 検証 attempt 無し + correctness 0 件 — 受理 (gate は発火しない)。

**新たに拒否される集合 (受理集合の差):** 「性能 completed あり、検証割当ての attempt が受領証に無い (失敗も完了も記録なし)、かつ 6 対未満」。これは §7.1(1) の「検証割当てが失敗した stage」にも「completed の受領証」にも属さない形で、D1272 が名指す「成功まで三者比較 0 回」の穴そのもの。§4.13「attempts[] は durable intent の全 attempt を exact に被覆」とも整合 (検証割当てを走らせたなら attempt が要る)。

**成功・certified の raw 定義 (本 wave):** 「completed 性能 attempt が存在し、検証割当ての失敗が受領証に記録されていない」。`declared_use_class` は使わない (§8)。この定義は D1272 の「失敗途中の受領証の空配列は維持」「受理集合を必要以上に狭めない」を満たす最大の gate であり、P1-b はこれを超える (A1)。

**呼出順 (V:2596-2605) は不変。** 既存の検証 completed 分岐 (6 対不足 = `reason`、被覆不一致 = `cardinality`) は loop 内で先に立ち、新 gate と二重発火しない。

## 3. fixture と test (unit3、同じ変更単位)

**`_full_receipt` は変えない。** 理由: (i) それ自体が §7.1(1) の正規失敗記録で、gate v2 の過剰拒否対照 (正例 2) になる、(ii) 凍結 vector 46 本の基底なので不変なら期待値は構造上不変 (B1/B10 の懸念を根から消す)。

**追加する部品:**
- `_make_git_fixture.tree_files` に 11 file: correctness 出力 5 本 `correctness/{stock-w2,mode1-w1,mode1-w2,modeX-w1,modeX-w2}.json` (既存 `stock-w1.json` と同じ比較可能 JSON)、liveness raw 6 本 `liveness/{arm}-{w}.log` (非空の合成 log)。既存 `correctness/{arm}.bin` 3 本と `compile_commands.json` / `CMakeCache.txt` を再利用。
- helper `_certified_receipt(fixture) -> tuple[dict, ReceiptSchema]`: `_full_receipt` の値を deepcopy し、検証 attempt を `completed` (returncode 0、failure_evidence None、marker None)、`correctness_evidence` を 6 対 (ordinal / run_ordinal 1..6、arm ごとに `arms[arm]["compile"]["source"]` を複製、`build.binary = correctness/<arm>.bin`、`outputs = [correctness/<arm>-<w>.json]`)、`liveness` を `liveness_run` 6 件 (ordinal 1..6、`monotonic_ns` 106..111、raw pointer) にする。stock/W1 を先頭に置く。entry 間で可変 dict を共有しない。
- helper `_drop_verification_attempt(value)`: attempts から `cluster_slot_or_null is None` の要素を除く (evidence / allocations は残す)。

**新 test (名前は実装子が整えてよいが node id は ASCII):**

| id | 入口 | 入力 | 期待 | 殺す変異 |
|---|---|---|---|---|
| T1 | top-level | `_certified_receipt` | 受理 | (正例。gate が正例を落とす変異の対照) |
| T2 | top-level、parametrize count ∈ {0, 1} | `_full_receipt` − 検証 attempt、evidence 先頭 count 件 | `correctness` | M1 M2 M7 M8(count=1) M9 |
| T3 | `_validate_reason_branches` 単体、count ∈ {0, 1, 5} | 最小 payload: 性能 completed (marker・allocation・36 actual を満たす形は既存 `test_completed_verification_requires_six_pairs` 型で `planned_execution` 等を合わせる) + 検証 attempt 無し + evidence count 件 | `correctness` | M1 M2 M8 M9 |
| T4 | top-level | `_certified_receipt` − 検証 attempt、entry[5] を entry[0] の複製 (ordinal 6 / run_ordinal 6、対は stock/W1 重複) | `correctness` | M5 (件数だけ) |
| T5 | 単体 | 6 対完全 + 同対の重複 1 件 = 7 件、検証 attempt 無し | `correctness` | M6 (被覆だけ) |
| T6 | 単体、count ∈ {0, 5} | 性能 attempt は `pre_performance_infra_failure` (marker None、actual 0、failure_evidence あり)、検証 attempt 無し、evidence count 件 | 受理 | M2 M4 (正例) |
| T8 | 単体 | 性能 completed + 検証 attempt `pre_performance_infra_failure` + evidence 0 件 | 受理 | M3 M4 M9 (正例) |

既存 `test_semantic_validator_accepts_complete_performance_receipt` (top-level、`_full_receipt`) と `test_completed_verification_requires_six_pairs` は不変のまま、それぞれ正例 2 と既存 6 対規則の対照として matrix に載せる。T3 単体 payload で「性能 completed」を作るには `_validate_reason_branches` の completed 性能分岐 (marker 非 null、failure None、actual が planned と 36 件双射) を満たす最小形が要る — 実装子は `_planned_ids_for_slot` が読む `planned_execution.runs` と `actual_runs` を 36 件で合わせる (U3 の既存 `_full_receipt` から切り出してよい)。

## 4. 変異事前登録 (DW-M01)

spec は `izanagi-dev-wave-mutation-spec/v1`、category は `negative` / `positive`、runner argv は `-rf` 必須、`estimated_run_seconds` は 1 run あたり (baseline 36 秒 + dispatch 往復 ≈ 70 秒)。**exact な `old` / `new` は段 5 の実装後に親が実コードから写して固定する** (B4)。期待 node は probe 走 (全件 SURVIVED 期待) で観測してから本走 spec へ写す。

| ID | category | 変異 (対象は新 gate 内のみ) | 期待 |
|---|---|---|---|
| M0 | positive | gate 直上の comment だけを変える | SURVIVED (等価対照) |
| M1 | negative | gate block 全体を削除 | KILLED: T2[0,1] T3[0,1,5] T4 T5 |
| M2 | negative | `if performance_slots and not verification_failure_recorded` → `if not performance_slots and not verification_failure_recorded` | KILLED: T2 T3 T4 T5 (発火せず) + T6[0,5] (誤発火) |
| M3 | negative | 条件から `and not verification_failure_recorded` を落とす (性能 completed なら無条件要求 = P1-b) | KILLED: 既存 `test_semantic_validator_accepts_complete_performance_receipt`、T8、および `_full_receipt` を top-level 正例として通す unit5 node (probe で実測して固定) |
| M4 | negative | 条件を `if True` | KILLED: M3 の集合 + T6[0,5] |
| M5 | negative | `or evidence_pairs != expected_pairs` を落とす (件数だけ) | KILLED: T4 |
| M6 | negative | `len(evidence) != 6 or` を落とす (被覆だけ) | KILLED: T5 |
| M7 | negative | reason を `"correctness"` → `"reason"` | KILLED: T2 T3 T4 T5 |
| M8 | negative | 検査を `if not evidence:` (空配列だけ拒否) | KILLED: T2[1] T3[1,5] T4 T5 |
| M9 | negative | `not verification_failure_recorded` → `verification_failure_recorded` (carve-out の反転) | KILLED: T2 T3 T4 T5 (発火せず) + T8 + M3 の既存正例集合 |

**M1 の反実仮想記録 (B6):** M1 で赤になる node が新負例だけであること (既存 focus 集合は全緑) を matrix 結果に別記する = 既存 test は本 gate を要求していなかった証拠。
**M3 / M9 が既存正例を殺すこと**が「carve-out (§7.1(1) の失敗記録を通す) が凍結契約に要る」証拠。
hang_risk を持つ変異は無い (全て純粋な条件変更)。dispatch 経路で走らせる。

## 5. 裁定パッケージ候補 (scope 外、実装しない。ユーザーへ返す)

1. **「成功・certified」の 3 択 (A4):** 本 wave は単票の raw 定義 (§2) を採った。attempt 成功 / stage 成功 / certified 採用 (a10/a11 の認証結果) のどれを D1272 の「certified」と同視するかは、単位 6 以降の認証実装が確定するときに再裁定候補。**検証失敗を記録した受領証 (正例 2) が下流で certified 採用されないことは認証実装の責務**であり、本 gate は保証しない。
2. **evidence-without-attempt の参照整合:** 「検証割当てを指す correctness_evidence があるのに、その割当ての attempt が無い」受領証は v2 で 6 対なら受理される。§4.13 の exact 被覆と突き合わせる参照整合 gate (割当てに attempt 必須) は別条件。
3. **correctness compile の TU / arm 束縛 (A9):** D574 決定 (3) の「当該 TU」の実 build 対応は correctness 側で照合していない。
4. **検証 attempt の両 stage 再掲の契約 (plan §裁定候補):** §0.1 は割当ての同一 bytes を言うが attempt の再掲は明文が無い。

## 6. brief の訂正

- (P1-a) は D1272 から導けない履歴条件 (plan)。(P1-b) は §7.1(1) の失敗記録を過剰拒否 (A1/A2)。→ v2 (§2)。
- 「失敗なら design_not_feasible」→ a10 は開始前 infra failure = `design_not_feasible`、correctness anomaly = 候補終端 reject と区別 (A10)。「正規手順で生じない」→ 取り下げ。
- アンカー: 6 対規則 V:1994-2017、liveness U:637、verification phase U:351、`_full_receipt` 終端 U:646 (A11)。
- 「vector は test 名を参照するだけ」→ test 名の実在 (U5:352) + recipe 実行結果 (U5:267) が拘束 (B10)。`_full_receipt` 不変で両方不変。
- create-only vector の `intent` は unit5 の専用入口由来 (plan)。
- `test_mocc_trace_job_contract.py:3856` は同名 enum で consumer でない (B9)。
- 「変更 file の sha256 pin 0 件」→「指定 approval 束縛と tracked file 検索の範囲で検出せず」(B)。
- 焦点走は `tools/run_tests.py <3 file> -q -rf` (plan)。

## 7. 段 5 の分割

author 1 本 (workspace-write): validator の gate + unit3 の fixture 部品 / helper / T1〜T8 を同一 diff。docs は触らない。commit は親。

## 8. 段 6 レビュー後の追記 (01:45 JST、親)

レビュー A (`s6-a-1.md`) / B (`s6-b-1.md`) とも **must-fix 0 件**。fix 子は起動しない。real 所見の反映:

- §2 の「新たに拒否される集合」の「6 対未満」は **「6 対の完全被覆を欠く (0〜5 件、および 6 件中の重複対を含む)」** と読む (A)。
- §1 A2 の「検証 attempt の失敗は `pre_performance_infra_failure` にしか写らない」は**正規運用上の想定**であり、現 validator の
  `post_performance_failure` 分岐 (V:2040) は slot を条件にしないので保証ではない (A)。gate は非 completed 全体を失敗記録として
  例外扱いするので署名に影響しない。
- §4 の期待 node 列挙は不完全 (B): M2/M4 は `test_post_failure_accepts_{marker_route,actual_run_route,recomputes_a03_route}`
  も殺し、M3/M4/M9 は `_full_receipt` を通す unit3 正例 / study test / unit5 の `semantic_positive`・writer authority・destination
  経路も殺し、既存 phase 負例の期待 reason も置き換える。**probe 走の観測 node を完全集合として本走 spec に固定する。**
- M6/M7 の `old` は行全体・2 行で一意化した (`mutation-spec-probe.json`)。
- 実装子の「指定コマンドで実走」は sandbox の `pytest.main` 直接起動 (親の prompt が指示した形)。権威は親の焦点走。
- 親の焦点走 (patch 適用後、計算ノード dispatch): **133 passed / 34.5 秒、rc=0** (`post-focus-1.log`)。1 回目は bounded local が
  OOM 上限 (≈2 GB) で退き dispatch へ切り替わった (変更に帰属しない)。
- 統合 commit `abce1ff51` (provenance full 監査 rc=0)。
