# [T-419] probe 因果実験 — 逐語と一次資料

wave branch `worktree-dev-wave-t419-probe-experiment`。ユーザー裁定 (2026-08-04 /rulings、
worklog (182)) の U-1「計算ノードで走行 CPU・cpufreq driver・boost 設定・同居プロセスを束縛した
probe 実験を置き、因果を立証してから是正方式を選ぶ」を実行した wave の逐語。

## 結論 (要旨)

**因果は立証も反証もされていない。** 実験は計算ノード bnode138 で 1 回走り、fail-closed で
A0 の直後に停止した (`execution_validity=INVALID` / `causal_verdict=NOT_EVALUATED`、probe_rc=3)。
因果の本体である A1 (pin sweep) は走っていない。

停止理由は 2 件で、**いずれも再実行では解消しない環境事実**である。

| # | 事実 | 影響 |
|---|---|---|
| E-1 | 計算ノードには NQSV 常駐デーモン `nqs_shpd` (uid 0、cgroup `/system.slice/nqs-jsv.service`) が居り、今回 CPU 22 で正の CPU 時間を消費した | 「非自 process の CPU 時間ゼロ」を単独性の必要条件にすると計算ノードでは決して満たせない |
| E-2 | `/sys/.../cpufreq/policyN/cpuinfo_cur_freq` は 48 policy すべてで Permission denied (非 root) | 診断 snapshot が常に incomplete になる。加えて「`/proc/cpuinfo` 以外の独立した周波数源へ替える」案は Pegasus では非 root で閉じている |

E-1 は親の裁定 G-1 が本機体で過剰に厳しいこと、E-2 は段 4 の裁定 (「不在・不可読・値ありを区別する」)
が実装で「不可読 = 致命」になっていたことを意味する。**どちらも実験側の欠陥であり、
probe 本体・述語・受理集合の問題ではない。**

## 予備データ (A0 の 30 読み、静穏な bnode138、非 pin)

**arm は INVALID なので判定には使わない。** 読み値自体は無傷なので方式選択の材料として残す。
生出力は `output/env/pegasus/t419-probe-causality/0_888740.nqsv/`。

- 帯外はどの読みでも**ちょうど 1 個**、しかも**毎回 CPU 44**。reader も 30/30 とも CPU 44。
- 帯内値 1410 個は**すべて厳密に 2101.0** (ユニーク値 1 個)。厳密一致率 47/48 = 0.979。
- 帯外値は 3061.3〜3096.8 MHz。
- **常駐デーモンが居た CPU 22 は一度も帯外にならなかった** — sleep 状態の同居は帯外化しない。

**reader が一度も移動しなかったため、「reader の CPU だから帯外」と「CPU 44 が個体として特別」を
このデータでは区別できない。** それを分けるのが A1 であり、走らなかった。ログインノードでは
帯外位置が毎回変わったが、別機体の観測なので因果の分母には入れていない (段 3 レンズ A-11)。

同じ 30 読みへ各方式を当てた予備値 (`m`=2101.0、帯 `[2058.98, 2143.02]`)。

| 方式 | 受理式 | 予備実測 |
|---|---|---|
| 現行 | `∀i. S[i] ∈ B` | **0/30 通過** |
| α から巡回を抜いた形 (K=5 連続読みの位置ごと最小) | `∀i. min_k S_k[i] ∈ B` | **0/6 ブロック通過** |
| β (走行 CPU の 1 要素除外) | `∀i≠r. S[i] ∈ B` | 30/30 通過 |
| γ (帯外 1 個許容) | `#{i : S[i] ∉ B} ≤ 1` | 30/30 通過 |

**α の「走行 CPU を移しながら」は省略できない。** 裁定原文の α は
「走行 CPU を移しながら K 回読み論理 CPU ごとに最小値を採る」であり、巡回は最初から裁定に含まれる。
上表の 2 行目は**巡回を抜いた形**の実測であり、**0/6 で通らない** — reader が移動しない限り
その CPU は K 回とも帯外で累積最小が下がらないからである。
つまりこの予備データは α を否定するのではなく、**巡回部分が load-bearing である**ことを示す。
α 本体 (巡回あり) は A1 が走っていないため未測定である。

**β と γ の「通った」は感度 (should-pass) を示すだけで、真の環境逸脱を拒否できるか
(specificity) は未測定**である。それを測る A2 は走らなかった。

## この wave がしたこと・していないこと

- **した:** 実験 driver (`tools/pegasus/probes/t419_probe_causality.py`)、PBS wrapper、
  解析関数の合成 fixture テスト、計算ノードでの 1 回の走行、変異 matrix、裁定パッケージ。
- **していない:** 是正の実装。probe 本体・較正の再取得・凍結 bytes・`env_contract.py` の pin は
  1 bit も触っていない。**Pegasus campaign は開いていない。**

## 段 6 の巡回と、3 巡目が無い理由

敵対レビュー 2 本 (18 所見、全件 real) → fix 3 巡 → 焦点再レビュー 2 巡。1 巡目 NO-GO
(closed 9 / partial 7 / regressed 2)、2 巡目 NO-GO (残り 3 点)。3 巡目の fix 後に予定していた
**焦点再レビュー 3 巡目は codex の利用枠切れ (回復予定 2026-08-08 12:37) で実行できていない。**
`DW-O16` の「3 巡上限 → 親が変異で裏取りして残る所見を real/refuted に裁定して閉じる」経路で閉じた。

## 変異 matrix (事前登録 8 本 + 両層裏取り 1 本)

spec は `mutation-spec.json` / `mutation-spec-2layer.json`、台帳は
`mutation-ledger.json` / `mutation-ledger-2layer.json`。runner は
`python3 tools/run_tests.py orchestrator/tests/test_t419_probe_causality.py -rf` (計算ノード dispatch)。
baseline は両走とも PASSED。

| ID | 変異 | 結果 | 実際に赤くなった node |
|---|---|---|---|
| M1 | paired contrast を恒真化 | KILLED | `test_paired_contrast_only_fixture_kills_m1` |
| M2a | primary read count gate を無効化 | KILLED | `test_a4_primary_count_gate_has_a_single_reason_fixture` |
| M2b | 例外 gate を無効化 | KILLED | `test_invalid_fixtures_are_not_evaluated[exception_only]` |
| M3 | canonical 述語を中央値の厳密一致へ | KILLED (erratum) | `test_band_endpoints_are_inclusive`, `test_in_band_non_nominal_uses_canonical_band` |
| M4 | α の累積最小を累積最大へ | KILLED | `test_alpha_converges_by_positional_cumulative_minimum` |
| M5a | 競合 consumer gate を無効化 | **SURVIVED (等価変異)** | なし |
| M5b | 競合 detector を無効化 | KILLED (erratum) | 5 node (下記) |
| M6 | should-reject を常時 reject へ (正例) | KILLED | `test_should_pass_fixtures_are_not_overrejected`, `test_should_reject_rows_are_not_replaced_by_constant_reject` |
| M5a-2layer | 競合 gate の両分岐を同時に無効化 | KILLED | `test_contention_invalidates_execution_and_verdict`, `test_residual_above_self_unattributable_invalidates_and_stops_later_arms` |

**M5a の生存は等価変異である。** 条件を偽にしても直後の
`elif attribution not in {"CLEAN", "ATTRIBUTION_UNRESOLVED"}` が COMPETITOR を拾い続けるため、
**受理挙動は変わらず診断文字列だけが変わる** (`DW-M03` の「診断文字列だけの赤を kill にしない」の
裏返し)。`DW-M02` に従い両層同時変異で裏取りしたところ、事前登録どおり 2 node が赤になり、
**gate 自体はテストで pin されている**ことが実測で確定した。

**erratum (親の過少・過剰列挙、`DW-M08`)。** M3 は 3 node を予測したが実際は 2 node
(`test_band_formula_external_oracle_literals` は band 式のみを見るため赤にならない = 過剰列挙)。
M5b は 1 node を予測したが実際は 5 node
(`test_isolation_residual_is_never_cancelled_across_cpus`,
`test_positive_nonself_pid_delta_is_competitor_snapshot_evidence`,
`test_released_child_pid_reuse_is_not_allowlisted`,
`test_short_lived_competitor_is_detected_from_unattributed_ticks`,
`test_residual_above_self_unattributable_invalidates_and_stops_later_arms`) で、
**検出力は予測より強かった** = 過少列挙。いずれも初回結果を消さず本節に残す。
harness の node 抽出が dispatch 経路で `None` を返したため、赤 node は job stdout 全文から
親が抽出した (F71 の正本規則)。

## ファイル

| ファイル | 中身 |
|---|---|
| `brief.md` | 段 1 brief と前提実測 |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対レンズ 2 本 (計 29 所見、全件 real) |
| `s4-adjudication.md` | 段 4 裁定 + 変異事前登録 + erratum-1 (読み数 430→445) |
| `s5-impl.md` | 段 5 実装子の報告 |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー 2 本 (18 所見、全件 real) |
| `s6-fix.md` / `s6-fix2.md` / `s6-fix3.md` | 段 6 fix 3 巡 |
| `s6-refocus.md` / `s6-refocus2.md` | 焦点再レビュー 2 巡 (いずれも NO-GO) |
| `mutation-spec.json` / `mutation-spec-2layer.json` | 変異事前登録 |
| `prompts/` | 各子へ渡した prompt (逐語) |

`s3`〜`s6` は codex worker の出力そのままである。親の裁定は `s4-adjudication.md` が正本。
