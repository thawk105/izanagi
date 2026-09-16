## 1. gate 条件

**P1-b を採用する。性能 completed の既存検査を通過した attempt がある受領証では、`correctness_evidence` が stock/mode1/modeX × W1/W2 の6対を各1件、合計6件で覆うことを要求する。** P1-a の「検証 completed attempt の存在」は追加条件にしない。

以下、行番号は現在のファイルを指す。

- `V`：[orchestrator/submission_gate/_semantic_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1449-certified-correctness-gate/orchestrator/submission_gate/_semantic_validator.py)
- `U3`：[orchestrator/tests/test_t338_submission_gate_unit3.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1449-certified-correctness-gate/orchestrator/tests/test_t338_submission_gate_unit3.py)
- `U5`：[orchestrator/tests/test_t338_submission_gate_unit5.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1449-certified-correctness-gate/orchestrator/tests/test_t338_submission_gate_unit5.py)
- `R`：`output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md`
- `A`：`output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md`

判断理由は次のとおり。

1. **D1272 の要求を証拠配列に直接適用できる。** 非空だけでは1件の穴が残るため、6件かつ被覆集合一致を要求する。既存の `V:1117` が各 entry の compile 三者比較を行い、`V:1803` が outputs の raw を再読する。新 gate はそれらの検査を受ける証拠が必要な全対について存在することを要求する。
2. **失敗 stage の0〜5件を無条件には拒否しない。** `R:752` の条件付き件数規則を保ち、性能 completed がない受領証には新 gate を適用しない。`A:80`、`:314` の唯一の binary 生成元と、`:626` の検証失敗時終端を合わせると、正規手順の検証失敗 stage に性能 completed が共存するとは読めない。
3. **main_run の検証 attempt 再掲には根拠があるが、明文の範囲を越えて断定しない。** `R:51` は検証割当ての同一 ID・bytes、`:476` は durable intent の全 attempt の exact 被覆を要求する。したがって同じ検証 intent を両 stage の対象に含めるなら再掲が必要であり、`U3:1065` の deepcopy もその形である。ただし、stage ごとの intent 集合の境界を明示した規定や、現行 validator による外部 intent 台帳との exact 照合ではない。fixture の deepcopy だけで「再掲以外はすべて不正」とは証明できない。P1-b ならこの解釈に gate を依存させずに済む。
4. **§8 は申告値を成功の証拠に昇格させない要求として読む。** `R:786` の字面を「reason_code の参照自体を禁止」と読むと、同じ凍結文書の §5、schema の条件分岐、`V:1993` 以降と衝突する。既存実装は申告された分岐に raw 条件を課して拒否する構造である。新 gate も単なる `any(reason_code == "completed")` を作らず、既存の性能分岐を最後まで通過した `performance_slots` を使う。

ここで `performance_slots` は reason_code と独立な分類器ではない。**既存の marker・allocation・failure・actual/planned 完全双射検査を通過した集合**であり、その限定をコメントと試験で明記する。

P1-c は採用する。`certified` field はなく、本 wave は性能 completed を持つ受領証への必要条件を実装する。`declared_use_class` は条件に使わない。

## 2. 挿入点と reason_code

**`V:2049` の `_validate_reason_branches` の loop 後に挿入する。独立関数と top-level 呼出しは増やさない。**

実装形は次の1条件とする。

```python
if performance_slots:
    evidence = value.get("correctness_evidence", ())
    expected_pairs = {
        (arm, workload) for arm in _ARMS for workload in _WORKLOADS
    }
    evidence_pairs = {
        (entry.get("arm"), entry.get("workload"))
        for entry in evidence
        if isinstance(entry, Mapping)
    }
    if len(evidence) != 6 or evidence_pairs != expected_pairs:
        _semantic(
            "correctness",
            "completed performance requires six correctness arm/workload pairs",
        )
```

top-level では shape、参照先が唯一の verification allocation であること、ordinal、全 pointer、compile、outputs の検査を通過して到達する。ここで同じ参照検査や raw parser を再実装しない。

**禁止の署名：既存検査を通過した性能 completed attempt が存在し、correctness 証拠が6対を過不足なく覆わない受領証は、`correctness` で拒否する。**

**通る正例：性能36-run の完全双射、検証 completed、正しい correctness 6対と liveness_run 6対を持ち、既存検査にも合格する受領証は受理する。**

reason_code は `correctness`。`V:1122` の correctness 配列、`:2039` 前後の raw anomaly、`:2047` の anomaly 証拠不足と同じ領域に属する。

呼出順 `V:2596–2605` は維持する。とくに既存の検証 completed 分岐を先に残すため、その件数不足の `reason`、被覆不一致の `cardinality` を新 gate が上書きしない。

## 3. 正例 fixture の改修

変更対象は `U3:181` の `_make_git_fixture` と `U3:332` の `_full_receipt`。

**検証 attempt：`U3:561–574`**

- `reason_code = "completed"`
- `qsub_result.returncode = 0`
- `failure_evidence = None`
- `performance_started_marker = None`
- `allocation_id = "alloc-verification"`、intent、空の observations は維持する。
- failure 用 raw file は新しい負例から使えるよう残す。

**correctness：`U3:581–600`**

以下の順で6件を生成する。既存テストが `[0]` の stock/W1 を変更するため、先頭を維持する。

| ordinal / run_ordinal | arm | workload | binary | outputs |
|---:|---|---|---|---|
| 1 | stock | W1 | `correctness/stock.bin` | `correctness/stock-w1.json` |
| 2 | stock | W2 | 同上 | `correctness/stock-w2.json` |
| 3 | mode1 | W1 | `correctness/mode1.bin` | `correctness/mode1-w1.json` |
| 4 | mode1 | W2 | 同上 | `correctness/mode1-w2.json` |
| 5 | modeX | W1 | `correctness/modeX.bin` | `correctness/modeX-w1.json` |
| 6 | modeX | W2 | 同上 | `correctness/modeX-w2.json` |

**`build.source` は各 arm の `arms[arm]["compile"]["source"]` をコピーする。** 現行の stock 用 source を全件に流用すると、mode1/modeX の patch identity が異なり、`V:1133` 付近で `correctness` になる。

各 compile record は独立した dict とし、既存 correctness 用 argv、compile_commands、raw CMakeCache を利用する。各 `run_scope.allocation_id` は `alloc-verification`。

**liveness：`U3:641`**

6対と同順に以下の7 keyを持つ entry を作る。

- `ordinal`: 1..6
- `allocation_id`: `alloc-verification`
- `probe`: `liveness_run`
- `arm_or_null`、`workload_or_null`: 対応する対
- `monotonic_ns`: 例えば106..111
- `raw`: 各対の fileRecord

schema `:864` の必須 field、`V:1514–1533` の probe・対の検査を満たす。`V:2285` の全 pointer 検査で raw を読むため、実ファイルを用意する。

**`tree_files` に追加する11ファイル：**

- correctness 出力5本：`stock-w2.json`、`mode1-w1.json`、`mode1-w2.json`、`modeX-w1.json`、`modeX-w2.json`。すべて `correctness/` 配下。
- liveness raw 6本：`liveness/stock-w1.log`、`stock-w2.log`、`mode1-w1.log`、`mode1-w2.log`、`modeX-w1.log`、`modeX-w2.log`。

既存の stock/W1 出力と correctness binary 3本は再利用する。outputs は全件、既存と同じ比較可能な JSON、例えば `{"expected":{"value":1},"actual":{"value":1}}` とする。`V:1735` は比較対象のない JSON や verdict だけの raw を拒否する。liveness raw は現在内容の成功判定を再計算していないため、対が分かる非空の合成ログを置く。

**phase/time の追加変更は不要。** `U3:358` の `_phase_data("verification", 100)` は既に全6 phase の enter/leave を生成し、時刻100..111が allocation 区間100..120に収まる。`V:197` の cap 合計は2640秒、deadline 3300秒、requested walltime 3600秒で整合する。`V:2110–2243` は検証 reason_code が completed になったことによる追加分岐を持たない。検証 actual_runs は引き続き0件。

これは合成 fixture の算術整合性であり、20nsで実際の検証処理が完了したという証拠ではない。

## 4. 凍結 vector の期待値不変

index の46件について `unit3_reference`、`expected_reason` と mutation を静的に確認した。**以下は実走結果ではなく、呼出順に基づく不変性の論証である。**

指定7本は次のとおり。

| vector | mutation と最初の拒否 | fixture 改修の影響 |
|---|---|---|
| `negative-7.1-08-reason-branches` | 性能 attempt を pre failure、marker を null、failure を非nullにするが36 actual を残す。`V:2036` の pre failure 分岐で `reason` | 性能 completed がなく `performance_slots` は空。実際には loop 内で先に拒否され、新 gate に到達しない |
| `negative-7.1-08-raw-marker-route` | 上記と同じ mutation、同じ `reason` | 同上。名前にかかわらず、残った actual が拒否根拠 |
| `negative-7.1-16-create-only` | 検証 attempt の intent path を性能側と同一にし、digest をゼロへ変更。`V:2347` の直接呼出しで `intent` | reason_code を参照しないので検証 completed 化は無関係 |
| `negative-6.8-reference-graph` | 性能 allocation と attempt の slot をともに9へ変更。参照間の slot は一致するが consumed は1..8。`V:2375` の allocation 検査で `allocation` | 新しい証拠は verification allocation を指すため影響なし |
| `negative-7.1-09-allocation-slot` | 上記と同じ mutation、同じ `allocation` | 同上 |
| `negative-6.5-schedule-derivation` | 性能 preflight の宣言 `stat_after` をゼロへ変更。`V:1827` の raw 再計算との不一致で `a03` | 検証 observations は空のまま。reason_branches より前 |
| `negative-7.1-10-stat-recompute` | 上記と同じ mutation、同じ `a03` | 同上 |

**create-only の説明は修正が必要。** `U5:298` 付近はこの vector を `_validate_create_only_references` に直接渡す。top-level の順序も create-only → reason_branches ではあるが、そのさらに前に `_validate_all_pointers` がある。この mutation を top-level にそのまま渡せば、偽の digest が `pointer` で落ちる。凍結期待値 `intent` の根拠は専用 entrypoint である。

残る39本は以下のように整理できる。

- **通常の receipt mutation 28本**：schedule/planned、cardinality、source、pointer、performance compile、argv/run log、phase の既存検査が拒否する。phase の6本だけは新 gate より後だが、correctness 6対を変更しないため新 gate を通過し、元の phase 拒否へ進む。他は新 gate より前に拒否される。
- **専用 semantic entrypoint 4本**：preregistration 2本、schema_pin 1本、`negative-7.1-01-liveness-pairs` 1本。最後は `U5:220` の独自 payload を使い、検証 completed の6件中1対を重複させる。既存分岐の `cardinality` が維持される。
- **その他の専用経路6本**：writer authority の負例4本、API 1本、parse 1本。意味検査を経る missing-authority 経路でも、改修後 fixture は新 gate を通過する。
- **receipt 正例1本**：`semantic_positive`。test 名を維持し、改修後 fixture を受理する。

上記「通常の receipt mutation 28本」には分類上の数え分けを避けるため、実装段では index の entrypoint ごとに再集計し、**最終的な証明は46 parameter 全件の実走**で行う。sealed writer 正例と既存宛先 `EEXIST` 経路も `_full_receipt` を使うため、必ず含める。凍結ファイルの編集は不要である。

## 5. 負例 test

top-level と `_validate_reason_branches` 単体の両方を置く。前者は本番入口まで到達すること、後者は既存の検証 completed 検査に隠れず新条件を識別することを確認する。

`U3:685` 付近に次を追加する。名称は計画上の提案名。

| test | 内容・期待 |
|---|---|
| `test_completed_performance_requires_correctness_coverage_top_level` | `count=[0,1,5]`。性能 completed を維持し、検証を元の pre failure・returncode 1・failure pointer ありへ戻す。correctness は先頭 count 件、liveness は空。top-level で `correctness`。N1/N2を含む |
| `test_completed_performance_requires_correctness_coverage_reason_branches` | 同条件を単体入口へ渡し `correctness`。既存の検証 completed 件数検査が拒否原因にならない |
| `test_completed_performance_rejects_duplicate_correctness_pair` | 検証 pre failure、correctness は6件だが W2 の1件を同 arm のW1へ変更。ordinal は維持。top-level と単体で `correctness`。件数だけの実装を殺す |
| `test_failed_stage_accepts_partial_correctness_evidence` | `count=0..5`。性能・検証とも pre failure、actual_runs と性能 observations を空にし、性能 marker を null、failure を設定。性能 `binary_rehash` も空へ戻す。top-level・単体で受理 |
| `test_correctness_coverage_does_not_require_verification_attempt` | 単体入口で検証 attempt を除き、性能 completed と correctness 6対を維持して受理。P1-b が検証 enum を新たな受理証拠にしないことを固定する |

最後の試験は gate の局所契約であり、durable intent の欠落が正規手順として正当だと認める試験ではない。

`test_completed_verification_requires_six_pairs`（`U3:685`）はそのまま維持し、0件の既存期待値 `reason` を変えない。`U3:975` の `test_reason_code_completed_is_not_positive_authority` も変更しない。raw facts がない入力は新 gate より前に `reason` で拒否される。

失敗 stage 正例では actual_runs を消すだけでは不足する。`V:2469` 以降が到達した rehash point と actual の整合性を検査するため、性能 rehash も調整する。

## 6. 変異 matrix の事前登録候補

各変異は単独で適用し、KILLED は該当 node の assertion failure として記録する。

| ID | 変異 | 期待 KILLED node |
|---|---|---|
| M0 | コメントのみ変更 | KILLED なし。等価対照 |
| M1 | 外側条件を `if not performance_slots` へ反転 | `test_completed_performance_requires_correctness_coverage_top_level[0]` |
| M2 | 新 gate を削除 | 同 `[0]`、`[1]` |
| M3 | 外側条件を `if True` にする | `test_failed_stage_accepts_partial_correctness_evidence[0]` |
| M4 | gate が見る `performance_slots` を常に空にする | `test_completed_performance_requires_correctness_coverage_reason_branches[0]` |
| M5 | 拒否 reason を `reason` 等へ変更 | `test_completed_performance_requires_correctness_coverage_top_level[0]` |
| M6 | 被覆集合検査を削除し、件数6だけにする | `test_completed_performance_rejects_duplicate_correctness_pair` |
| M7 | 空配列だけ拒否し、1〜5件を許す | `test_completed_performance_requires_correctness_coverage_top_level[1]`、`[5]` |
| M8 | 特定の1対欠落を特例で許可する | 同 `[5]`。欠落対は事前に modeX/W2 と固定 |
| M9 | 拒否条件全体を `True` にする | 既存 `test_semantic_validator_accepts_complete_performance_receipt` |
| M10 | 完全被覆に加えて検証 completed の存在を必須化 | `test_correctness_coverage_does_not_require_verification_attempt` |

M3 と M9 は異なる。外側条件の恒真化は成功正例では検出できず、**失敗 stage の受理正例が必要**である。

集合変異を既存の検証 completed 分岐だけで殺さないよう、M6/M8 の対象入力では検証 attempt を pre failure にする。

## 7. 焦点テスト集合

確認した consumer は次のとおり。

| consumer | 参照・影響 |
|---|---|
| `_writer.py:17,73` | validator を import し publish 前に実行 |
| `U3:24` | 直接 import。fixture 改修と新 gate の主要試験 |
| `U5:28,42,385,560` | validator と U3 fixture を利用。46 vector、writer 経路を含む |
| `test_t139_submission_path.py:24,39` | U3 fixture の間接 consumer。`_authority_fixture` が `seed.tree_files` をすべてコピーするため追加ファイルも伝播 |
| `test_mocc_trace_job_contract.py` | 現行ファイル内に `_semantic_validator`、`submission_gate`、`test_t338` の文字列参照も見つからない。直接 consumer には数えない |

再走集合は **unit3 全件、unit5 全件、`test_t139_submission_path.py` 全件**。unit5 の46 parameter は省略しない。Mocc trace 全件は今回の焦点集合には含めない。

実装段では `tools/run_tests.py` を通し、必要な docs/Codex checker、commit 後の provenance 監査を通常手順で行う。brief の `python3 -c "import pytest; pytest.main(...)"` 直接実行案は使わない。

本段ではテストを実行していない。

## 8. リスク

**失敗 stage の受理集合。** 新条件は性能 completed を持たない入力には作用しない。検証失敗・correctness 0〜5件を parameter 化した受理正例でこの境界を確認する。性能 completed と検証失敗が共存する従来の合成入力は意図的に拒否対象となるが、唯一の検証割当てが失敗したら終端となる正規手順とは区別する。

**P1-b の限界。** 性能 completed＋correctness 完全6対＋検証 pre failure という入力は、新 gate 単独では拒否しない。三者比較0回の穴は閉じるが、検証 attempt の履歴整合性まで保証する条件ではない。その追加を暗黙に混ぜない。

**既存 reason の優先順位。**

- 検証 completed の件数不足：既存 `reason`。
- 検証 completed の6件中重複：既存 `cardinality`。
- malformed outputs や compile 不一致：先行する既存 `correctness` / `compile`。
- 検証が非 completed／不在で性能 completed、correctness 不足：新 gate の `correctness`。

この順序を維持すれば、同じ入力で新旧が二重に発火することはない。N1/N2 は既存の検証 completed 分岐を避けて新 gate に到達させる。

**fixture の波及。** source を stock 固定で複製しないこと、stock/W1 を先頭に残すこと、各 output と liveness raw の pointer を揃えることが重要。既存 anomaly/raw-parser テストは先頭だけを書き換えるため、残り5件と共有する可変 dict を作らない。

**study-level は変更しない。** `V:2630` は各受領証を個別検証してから stage 順序と検証 allocation の ID・raw digest を照合する。今回の必要条件は個別検証を通じて両 stage に適用されるため、新しい study-level 条件は不要であり scope 外。

## 裁定パッケージ候補

将来必要なら、次を独立した解釈整理の対象にできる。本 wave の実装には含めない。

- 両 stage の durable intent 集合に検証 attempt が必ず含まれるという exact な契約と、その照合責任。
- correctness 6対が存在しても検証 attempt が失敗を申告する入力を、別途拒否する必要があるか。
- §8 の「受理条件の入力禁止」と §5 の分岐検査の関係を、申告値による成功認定の禁止としてどう説明するか。

これらを理由に凍結文書・schema・vector を変更する案は出さない。

## brief の誤り

1. **P1-a は D1272 から一意には導けない。** 検証 completed の存在必須化は、証拠の非空・三者比較とは別の履歴条件を含む。最小条件として P1-b を採る。
2. **create-only の期待値説明は専用入口を区別する必要がある。** `intent` が維持される理由は unit5 の直接呼出しであり、同じ mutation を top-level に通した場合は先行する pointer 検査が拒否する。
3. **「失敗なら design_not_feasible」は広すぎる。** a10 は開始前 infra failure が `design_not_feasible`、correctness anomaly は候補終端 reject と区別する。
4. **直接 pytest harness の実行案は採らない。** 指定された規律どおり `tools/run_tests.py` を使う。
5. fixture 改修には、各 arm に対応した `build.source` と、失敗正例での `binary_rehash` 調整も必要である。

## 総括

確定案は P1-b：既存 raw 検査を通過した性能 completed があれば、correctness 6対の完全被覆を要求する。
`_validate_reason_branches` の loop 後へ追加し、拒否は `correctness` とする。
P1-a の検証 completed 存在必須化は、本 wave に含めない。
正例 fixture は検証 completed・correctness 6対・liveness 6対へ改修する。
失敗 stage の0〜5件受理正例を置き、恒真化を検出する。
create-only vector の `intent` は専用入口によるもので、top-level の説明を補正する。
凍結ファイルと study-level は変更しない。
本段は静的検査のみで、ファイル変更・テスト実行は行っていない。