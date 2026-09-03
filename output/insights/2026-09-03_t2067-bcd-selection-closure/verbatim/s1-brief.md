# 段 1 brief — [T-2067] 残件 (b)(c)(d)

正本: `docs/archive/worklog-phase3-0902-1202.md` の [T-2067] 本文、`docs/decisions.md` の D1503。
基準 commit: `9f2a68a18b572b662a35efc8fe0ed3a9ad901569`（local main と乖離 0、開始 gate rc=0）。

## scope

- **(c)** `build_manifest` / `write_manifest` が床値選択 gate を通さず manifest を構築・保存できる
  公開迂回口を塞ぐ。repo 内の caller は test helper だけである。
- **(d)** 床値選択 eligibility の実導出を、**launch 経路**と **consumer 経路**の負例で実際に通す。
  負例は実体を名指しし、導出関数を stub しない。
- **(b)** 「load-only consumer 3 群」母集合を (d) の結果で数え直し、docs へ記録する。

## 確定済みユーザー裁定

- (a) oracle report / verdict / judge への選択強制、(e) s8c C06 予算群、(f) 起動証明書の実時間性は
  **scope 外**。(a) は凍結成果物の bytes が変わるためユーザー裁定送り、(e) は T-2159 着地後の再評価、
  (f) は D1241 が機構を禁じている。
- 本題の実装だけを行う。仮想リスク向けの gate・検査・台帳・一般化を足さない。
- 絶対規律 2 を緩めない。anomaly を検出した variant の即 reject は不変。

## 不変条件

- 既存テストの期待値を変更しない。反転・緩和・skip・削除を禁じる。
- 凍結成果物の bytes を変えない。`_GENERATOR_SOURCES` が pin する 5 本
  (materializer / report / judge / outcome_stage_contract / artifacts) を編集しない。
- `output/s8b-freeze/` 配下、campaign WAL、`external/ccbench` へ書かない。
- `orchestrator/campaign/freeze_verification_hold.py` を編集しない（解除はユーザー明示命令のみ）。
- 選択 gate の受理集合を緩めない。拒否は署名で書き、通る正例を 1 つ添える。

## 親が実測して覆した前提（段 4 で再裁定する）

正本 (d) の「実導出を走らせて rule-mismatch を出す test が repo に無い」は**現行 main では偽**である。
`orchestrator/tests/test_s8b_holdout_freeze.py::test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility`
が `_install_real_floor_selection_runs` で実 earlier run を作り、実導出を通して rule-mismatch を出す
（2026-08-29 の commit `31426fb9a` で着地済み）。

**ただし (d) の結論そのものは実測で支持される。** 親が `_derive_floor_selection_eligibility` を
無条件 `False` へ一時変異させて焦点走を実測した結果（DW-O19、即時復元・非 commit、
復元 bytes は `7904d47b36fa87ac40dac0c2da1a114d4b04000ed5a8c15f17b89523b9ebbdb0` で一致）:

| 走行 | 結果 |
|---|---|
| baseline（4 file、`-k "selection or eligib"`） | 25 passed / 34.90s |
| 変異後（同一集合） | **6 failed, 19 passed** / 34.79s |

赤 6 件は**すべて** `test_s8b_holdout_freeze.py`（v2 candidate 経路）だった。
`test_s8b_ratified_verify.py`（launch 経路 + 狭い API）、`test_s8b_oracle_manifest.py`、
`test_s8c_result_judge.py` は**全緑**。したがって被覆の穴は「repo 全体で実導出が未検査」ではなく
**「launch 経路と consumer 経路が実導出を一度も通らない」**である。(d) の対象はこの 2 経路に限る。

## 成果物の形

- (c) 選択 gate を通さない manifest 構築・保存の公開 API が無くなり、その拒否を固定する負例が付く。
- (d) launch 経路と consumer 経路それぞれに、実導出を通して `floor-selection-rule-mismatch` を出す
  負例が付く。DW-M08 に従い、新テストと変更前 HEAD 版の双方へ同じ変異を走らせ、
  **新テストだけが検出する差分**を示す。
- (b) 数え直した母集合を worklog fragment と insight へ記録する（純増のみ、再掲しない）。

## (P1) 親の provisional 裁定・攻撃対象

- **(P1-1)** (c) の最小形は `build_manifest` / `write_manifest` を module private へ落とし、
  gate 済みの `build_approved_manifest` だけを public に残すことである。
  `VerifiedManifest._seal` と同型の seal token 方式は、`build_manifest` が任意 `freeze_path` を取り
  g1 ratified freeze を持たない既存 test fixture を壊すため採らない。
- **(P1-2)** (d) の最小形は `test_s8b_ratified_verify.py` の launch / consumer 2 経路へ、
  実 earlier run を持つ genuine な負例を 1 対追加することである。既存の stub 版 2 test は
  「gate が呼ばれた事実と引数」を固定する検査点として D1504 と同型に残す。
- **(P1-3)** (b) の実測値は「3 群」でなく **4 群**であり、内訳は report / judge / verdict（(a) に属す）と
  C06 予算群（(e) に属す）である。純増の実装は無く docs 記録だけになる。
- **(P1-4)** 実装子は 1 本にする。(c) と (d) は編集 file が素集合だが、(d) が共有 fixture の移動を
  要するなら producer/consumer 契約が単位を跨ぐため、並列化の利得より事故率が上回る。

## 実アンカー表（分類でなく実在の位置）

### 実装面（production）

| # | anchor | 現状 |
|---|---|---|
| A1 | `orchestrator/campaign/s8b_oracle_manifest.py:818` `build_manifest` | public、選択 gate なし |
| A2 | `orchestrator/campaign/s8b_oracle_manifest.py:842` `build_manifest_from_ratified` | public、選択 gate なし。`build_approved_manifest` から呼ばれる |
| A3 | `orchestrator/campaign/s8b_oracle_manifest.py:902` `write_manifest` | public、選択 gate なし。create-only atomic link |
| A4 | `orchestrator/campaign/s8b_oracle_manifest.py:1197`〜`:1206` `build_approved_manifest` | 唯一の gate 済み経路。CLI subcommand は `build-approved` の 1 本だけ |
| A5 | `orchestrator/campaign/s8b_ratified_freeze.py:3558` `assert_g1_floor_selection_identity` | consumer 経路の gate。非 g1 は観測せず返る |
| A6 | `orchestrator/campaign/s8b_ratified_freeze.py:3303` `_launch_validate` の `LaunchValidatedFreeze` 分岐 | launch 経路の gate |
| A7 | `orchestrator/campaign/s8b_holdout_freeze.py:1865` `_derive_floor_selection_eligibility` | 実導出。共有 admission 台帳から再導出する |
| A8 | `orchestrator/campaign/s8b_holdout_freeze.py:1928` `_assert_floor_selection_identity` | 3 経路が共有する判定 |
| A9 | `orchestrator/campaign/s8b_holdout_freeze.py:2053` `build_v2_g1_candidate` の呼出し | 実導出が現に検査されている**唯一**の経路 |

### 実装面（test）

| # | anchor | 現状 |
|---|---|---|
| T1 | `orchestrator/tests/test_s8b_ratified_verify.py:834` `_with_earlier_floor_result_at_head` | earlier run を `b"{}"` で作る。実導出は通らない |
| T2 | `orchestrator/tests/test_s8b_ratified_verify.py:854` `test_launch_validate_rejects_floor_selection_rule_mismatch` | `HF._derive_floor_selection_eligibility` を stub |
| T3 | `orchestrator/tests/test_s8b_ratified_verify.py:871` `test_g1_selection_helper_rejects_rule_mismatch` | 同上 |
| T4 | `orchestrator/tests/test_s8b_holdout_freeze.py:1985` 付近 `_install_real_floor_selection_runs` | 実 earlier run を作る既存 helper（実導出を通す） |
| T5 | `orchestrator/tests/test_s8b_holdout_freeze.py:2155` `test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility` | 実導出で rule-mismatch を出す既存 test |
| T6 | `orchestrator/tests/test_s8b_oracle_report.py:268,391,402` | `build_manifest` / `write_manifest` の caller |
| T7 | `orchestrator/tests/test_s8b_oracle_manifest.py:196,402,410,424,443,469,489,528,551,571,607,630,657,780,801,858` | 同上 |

### (b) の母集合候補（実測）

| consumer | 呼び方 | 選択 identity | 帰属 |
|---|---|---|---|
| `orchestrator/campaign/s8b_oracle_report.py:2547` | load + reverify | **未強制** | (a) scope 外 |
| `orchestrator/campaign/s8b_oracle_judge.py:749` | load + reverify | **未強制** | (a) scope 外 |
| `orchestrator/campaign/s8b_verdict.py:828` | load + reverify | **未強制** | (a) scope 外 |
| `orchestrator/campaign/p3_autonomous_workload_trial.py:4710` | load only（C06 予算） | **未強制** | (e) scope 外 |
| `orchestrator/campaign/s8b_oracle_manifest.py:1205` | load + 狭い API | 強制済み | entry 1202 |
| `orchestrator/campaign/s8c_result_judge.py:2076` | load + 狭い API | 強制済み | entry 1138 |
| `orchestrator/campaign/s8b_oracle_driver.py:496,644,1335` | `launch_validate` | 強制済み | A6 |

## DW-O09 pin 閉包（実測）

- `output/s8b-freeze/holdout_freeze.json` の `/generator/sha256` が
  `orchestrator/campaign/s8b_holdout_freeze.py` の bytes を pin する。記録値
  `1910fff3…`、現行 bytes `7904d47b…` で**着手前から不一致**であり、この照合は
  `freeze_verification_hold.HELD = True`（ユーザー裁定 2026-08-12、21 件）で保留中である。
  よって同 file の編集は凍結鎖を**新たに**壊さない。解除は行わない。
- `_GENERATOR_SOURCES`（`s8b_oracle_manifest.py:66`）が pin するのは
  materializer / report / judge / outcome_stage_contract / artifacts の 5 本で、
  `s8b_oracle_manifest.py` 自身・`s8b_ratified_freeze.py`・`s8b_holdout_freeze.py` は含まれない。
  (a) が scope 外である理由（report / judge が pin 側にある）と整合する。
- 編集面 file を走査する構造検査: `orchestrator/tests/test_ccbench_spawn_sites.py:194-203`
  （関数別 spawn site 数）、`orchestrator/tests/test_official_perf_closure.py:66,72,206`、
  `orchestrator/tests/test_s8c_preregistration_invariant.py:54,81,88,112-128`、
  `orchestrator/tests/test_s8c_preregistration_predicates.py:32,535,1164,…`（関数名 token）。
  `s8b_ratified_freeze.py` の関数を改名・削除するとこれらが赤になる。

## DW-G05 成果物影響

- (c) 未対応なら、床値選択規則に束縛されない manifest を構築・封印できる公開 API が残る。
  将来の caller が oracle の certified 選択結果をその manifest の上で出しうる。
- (d) 未対応なら、実導出が壊れても launch 経路と consumer 経路のテストは緑のままで
  （親が実測済み）、床値選択 identity の強制が実質空になっても検出できない。
- (b) 未対応なら、事実に反した残余の数え方が後続 wave の scope 判断に使われる。

## 実測環境

Pegasus。テストは `tools/run_tests.py` の既定自動判定で計算ノードへ dispatch する
（login node での pytest 直起動は hook が拒否する）。受入全走も同じ経路。
同一 worktree からの dispatch は直列にする（DW-O26）。

## 分割方針

- 実装面は Codex `role=author` 1 本に委譲する（(P1-4)）。親は brief・裁定・統合 commit・
  変異 matrix・受入全走・記録・land だけを担い、実装面を直接編集しない。
- (b) の docs 記録は親が書く。
